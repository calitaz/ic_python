'''
 Script em Python para captura de comentários no site de notícia g1.globo.com
 Captura comentários, data do comentário, titulo da noticia, link da noticia e data da noticia
 Gera dois JSONs, um com os comentarios,data de comentario e link da noticia
 e outro com titulo, link da noticia e data da noticia
 Os JSONs são "linkados" pelo link da noticia
 
 Desenvolvido por: Tauã Gomes de Almeida
 
'''


#Bibliotecas
import pandas
import requests
import time
from pandas import DataFrame
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


#Variáveis
records = [] 
links_reportagem = []
titulos = []
data_hora = []
links_noticia = []
list_data_comentarios = []
tags_assunto = []
links_noticia_comentario = []

#Cria uma sessão, evita erros de HTTP request que aconteciam no site ao ter lentidão na requisição
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

#Link para o webdriver chrome
driver = webdriver.Chrome('C:/chromedriver/chromedriver.exe')

#Funcao para limpar arrays duplicados (não esta sendo usado)
def limpaArrays(array):
    igual = set()
    result = []
    for item in array:
        if item not in igual:
            igual.add(item)
            result.append(item)
    return result

#Funcao para gerar os arquivos em JSON
def gera_json():
    
    dados_noticia = {
        'link_noticia': links_noticia,
        'titulo': titulos,
        'data_hora': data_hora,
        'tags': tags_assunto
    }
    
    
    dados_comentarios = {
        'link': links_noticia_comentario,
        'comentarios': records,
        'data_comentario': list_data_comentarios
    }
    
    df = DataFrame(dados_comentarios, columns=['link','comentarios','data_comentario'])
    with open('comentarios_.json', 'w', encoding='utf-8') as file:
        df.to_json(file, force_ascii=False, orient='index')
    

    df2 = DataFrame(dados_noticia, columns=['link_noticia','titulo','data_hora','tags'])
    with open('dados_noticias_.json', 'w', encoding='utf-8') as file:
        df2.to_json(file, force_ascii=False, orient='index')

#Funcao de captura das informaçoes         
def pega_comentarios():
    res = driver.execute_script('return document.documentElement.outerHTML')
    soup = BeautifulSoup(res, 'html.parser') 
    link_noiticia = soup.find("link",{"itemprop":"mainEntityOfPage"})
    href_link_noticia = link_noiticia.get('href')
    busca_titulo_noticia = soup.find("h1",{"class":"content-head__title"})
    titulo_noticia = busca_titulo_noticia.text
    busca_data_hora = soup.find("time",{"itemprop": "datePublished"})
    data_hora_text = busca_data_hora.text
    lista_recente = soup.find("div","glbComentarios-lista glbComentarios-lista-recentes")
    if(lista_recente):
        lista = lista_recente.find("ul", class_ = "glbComentarios-lista-todos")
        if(lista):
            li = lista.find_all("li", {"itemtype":"http://schema.org/UserComments"})
            for coments_ in li:
                coments = coments_.find("p", class_ = "glbComentarios-texto-comentario")
                if(coments):
                    comentarios = coments.contents[0]
                    comentarios.strip()
                    records.append((comentarios)) 
                    links_noticia_comentario.append((href_link_noticia))
                    data_coments = coments_.find("abbr", {"itemprop":"commentTime"})
                    data_comentarios = data_coments.get('title')
                    list_data_comentarios.append((data_comentarios))
                   
            entities = soup.find("a",{"class":"entities__list-itemLink"})
            if(entities):
                tags_assunto.append((entities.text))
            else:
                entities = soup.find("a",{"class":"header-editoria--link"})
                tags_assunto.append((entities.text))
            data_hora.append((data_hora_text))
            titulos.append((titulo_noticia))
            links_noticia.append((href_link_noticia))
    
#Funcao para apertar o botao de respostas a comentarios                               
def botao_respostas():
    while True:
        try:
            mais_comentarios = driver.find_element_by_xpath("//*[@class='glbComentarios-lista glbComentarios-lista-recentes']/ul/li/div[1]/div/div[3]/button[not(contains(@style,'display: none'))]")
            time.sleep(3)
            if(mais_comentarios.is_displayed()):
                ActionChains(driver).move_to_element(mais_comentarios).click(mais_comentarios).perform()
        except NoSuchElementException as e:
            break
    pega_comentarios()   

#Funcao para apertar o botao de carregar mais comentarios
def botao_carrega():
    while True:
        try:
            carrega_mais = driver.find_element_by_xpath('//*[@id="boxComentarios"]/div[4]/button')
            time.sleep(2)
            if(carrega_mais.is_displayed()):
                ActionChains(driver).move_to_element(carrega_mais).click(carrega_mais).perform()
            else:
                break
        except NoSuchElementException as e:
            break
    botao_respostas()
     
#Funcao para buscar as reportagens da pagina inicial do g1.globo.com
def busca_reportagens(url):
    pagina_globo = session.get(url)
    soup = BeautifulSoup(pagina_globo.text, 'html.parser')
    div_reportagens = soup.find_all("div",{"class":"_et"})
    for inside_divs in div_reportagens:
        tag_a = inside_divs.find("a")
        href_a = tag_a.get('href')
        if(href_a):
            valid_href = href_a
        links_reportagem.append(tag_a.get('href'))
        
    for links in limpaArrays(links_reportagem):
        try:
            pagina = session.get(links)
        except:
            time.sleep(5)
        finally:
            soup = BeautifulSoup(pagina.text, 'html.parser')
            existe_boxcomentarios = soup.find("div",{"id":"boxComentarios"})
            if(existe_boxcomentarios):
                driver.get(links)
                driver.maximize_window()
                try:
                    box_comentarios = driver.find_element_by_id('boxComentarios')
                    driver.execute_script('arguments[0].scrollIntoView(true);', box_comentarios)
                finally:
                    try:
                        element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "glbComentarios"))
                        )
                    except TimeoutException as timeout:
                        print(timeout)
                        break
                    finally:
                        botao_carrega()
    driver.quit()

#Funcao de inicialização
def __init__(url):
    busca_reportagens(url)

#Start
__init__('https://g1.globo.com')
gera_json()   
        
          