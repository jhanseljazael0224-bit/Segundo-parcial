import requests 
from bs4 import BeautifulSoup 

class Scraper:
    def __init__(self, nombre, url):
        self.nombre = nombre
        self.url = url
    self.session = requests.Session()
    self.session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })
    def obtener_html(self):
        try:
            respuesta = self.session.get(
                self.url,
                timeout = 30
            )
            respuesta.raise_for_status()
            return respuesta.text 
        except requests.request_exception as error:
            print("Error al consultar {sel.nombre}: {error}")

    def analizar_html(self,html):
        if html is None: 
            return None
        return BeautifulSoup(html,"html.parser")
        

        
        
