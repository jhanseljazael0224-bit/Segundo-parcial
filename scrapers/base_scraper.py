
import requests
from bs4 import BeautifulSoup


class BaseScraper:

    def __init__(self, nombre, url):
        self.nombre = nombre
        self.url = url
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "ProyectoAcademicoScraper/1.0"
        })

    def obtener_html(self):

        try:
            respuesta = self.session.get(
                self.url,
                timeout=30
            )

            respuesta.raise_for_status()

            return respuesta.text

        except requests.RequestException as error:
            print(f"Error al consultar {self.nombre}: {error}")
            return None

    def analizar_html(self, html):

        if not html:
            return None

        return BeautifulSoup(html, "html.parser")
