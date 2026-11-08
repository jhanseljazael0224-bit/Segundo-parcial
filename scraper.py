import requests 
from bs4 import BeautifulSoup 

class Scraper:
    def __init__(self, nombre, url):
        self.nombre = nombre
        self.url = url
        
    def get_html(self):
        response = requests.get(self.url)
        return response.text 
        