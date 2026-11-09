
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import config
from models.propiedades import Propiedad
from scrapers.base_scraper import BaseScraper


class CorotosScraper(BaseScraper):
    BASE_URL = "https://www.corotos.com.do"
    LISTADO = BASE_URL + "/c/inmuebles-en-venta"
    PAUSA_SEGUNDOS = 1.2
    MAX_PAGINAS = 40

    def __init__(self):
        super().__init__("Corotos", self.BASE_URL)
        self.nombre = "Corotos"
        # BaseScraper ya crea una sesión en la estructura actual del proyecto.
        if not hasattr(self, "session") or self.session is None:
            self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept-Language": "es-DO,es;q=0.9",
        })

    def obtener_html(self, url=None):
        """Descarga HTML para pruebas sin el medidor de tiempos."""
        direccion = url or self.LISTADO
        try:
            respuesta = self.session.get(
                direccion, timeout=config.timeout
            )
            respuesta.raise_for_status()
            return respuesta.text
        except requests.RequestException as error:
            print(f"[Corotos] No se pudo abrir {direccion}: {error}")
            return None

    def _solicitar(self, url, estatus):
        """Usa el medidor de main.py cuando está disponible."""
        if estatus is not None:
            try:
                return estatus.obtener_html_medido(self, url)
            except requests.RequestException as error:
                print(f"[Corotos] Error HTTP en {url}: {error}")
                return None
        return self.obtener_html(url)

    @staticmethod
    def _enlaces_anuncios(html):
        """Encuentra URLs únicas de inmuebles, no perfiles ni anuncios externos."""
        soup = BeautifulSoup(html, "html.parser")
        enlaces = []
        encontrados = set()

        for enlace in soup.select('a[href*="/anuncio/inmuebles-"]'):
            href = enlace.get("href", "").split("#")[0]
            url = urljoin(CorotosScraper.BASE_URL, href)
            if not re.search(
                r"^https://www\.corotos\.com\.do/anuncio/"
                r"inmuebles-en-(?:venta|alquiler)/", url
            ):
                continue
            if url not in encontrados:
                encontrados.add(url)
                enlaces.append(url)
        return enlaces

    @staticmethod
    def _numero(texto, etiqueta):
        """Obtiene un número después de una característica como 'Habitaciones'."""
        encontrado = re.search(
            rf"\b{etiqueta}\s*:?\s*(\d+)", texto, flags=re.IGNORECASE
        )
        return int(encontrado.group(1)) if encontrado else None

    @staticmethod
    def _seccion(texto, inicio, fin):
        """Devuelve el contenido entre dos rótulos de la ficha."""
        patron = rf"{inicio}\s*(.*?)\s*(?:{fin})"