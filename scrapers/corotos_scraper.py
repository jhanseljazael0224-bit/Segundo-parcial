
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
        direccion = url or getattr(self, "url", None) or self.LISTADO
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
        encontrado = re.search(patron, texto, flags=re.IGNORECASE | re.DOTALL)
        return encontrado.group(1).strip() if encontrado else ""

    def _parsear_propiedad(self, html):
        """Transforma una ficha individual en un objeto Propiedad."""
        soup = BeautifulSoup(html, "html.parser")
        encabezado = soup.find("h1")
        if encabezado is None:
            return None

        nombre = encabezado.get_text(" ", strip=True)
        texto = soup.get_text(" ", strip=True)
        # Ignorar menús anteriores al título y anuncios recomendados posteriores.
        posicion = texto.find(nombre)
        if posicion >= 0:
            texto = texto[posicion:]
        texto = texto.split("También te puede interesar", 1)[0]

        precio_match = re.search(r"(?:RD\$|US\$|USD\$)\s*[\d.,]+", texto)
        if not nombre or not precio_match:
            return None
        precio = re.sub(r"\s+", "", precio_match.group(0))

        caracteristicas = self._seccion(
            texto, r"Características", r"Descripción|Ubicación"
        )
        if not caracteristicas:
            caracteristicas = texto.split("Descripción", 1)[0]

        # Una ficha puede mostrar tamaño de construcción o tamaño de terreno.
        tamano_match = re.search(
            r"Tamaño\s+(?:de\s+)?(?:Construcción|Terreno)"
            r"\s*(?:\(m²\))?\s*:?\s*([\d.,]+)",
            caracteristicas,
            flags=re.IGNORECASE,
        )
        tamano = f"{tamano_match.group(1)} m²" if tamano_match else None

        habitaciones = self._numero(caracteristicas, "Habitaciones")
        banos = self._numero(caracteristicas, "Baños")
        parqueos = self._numero(caracteristicas, "Parqueos")

        ubicacion = self._seccion(
            texto,
            r"\bUbicación\b(?:\s+location_on)?",
            r"Condición del Producto|Chatear con el vendedor|Hacer oferta",
        )
        ubicacion = ubicacion.replace("×", " ").strip(" ·,-") or None
        if not ubicacion:
            sector = re.search(
                r"\bSector\s*:\s*(.*?)(?=\s+Condición|\s+Tamaño|$)",
                caracteristicas,
                flags=re.IGNORECASE,
            )
            ubicacion = sector.group(1).strip() if sector else None

        vendedor = self._seccion(
            texto,
            r"Chatear con el vendedor(?:\s+Enviar)?",
            r"Miembro desde\s*:",
        )
        vendedor = vendedor.strip(" ·,-") or None

        return Propiedad(
            "Corotos", nombre, precio, ubicacion, vendedor,
            tamano, habitaciones, banos, parqueos,
        )

    def extraer(self, estatus=None, limite=200):
        """Recorre el listado y las fichas hasta reunir `limite` inmuebles."""
        if limite <= 0:
            return []

        propiedades = []
        urls_vistas = set()
        paginas_sin_nuevos = 0

        for pagina in range(1, self.MAX_PAGINAS + 1):
            if len(propiedades) >= limite:
                break
            url_listado = (
                self.LISTADO if pagina == 1
                else f"{self.LISTADO}?page={pagina}"
            )
            html_listado = self._solicitar(url_listado, estatus)
            if not html_listado:
                print("[Corotos] Listado no disponible; se detiene la búsqueda.")
                break

            enlaces = [
                url for url in self._enlaces_anuncios(html_listado)
                if url not in urls_vistas
            ]
            if not enlaces:
                paginas_sin_nuevos += 1
                if paginas_sin_nuevos >= 2:
                    print("[Corotos] Sin nuevos anuncios en dos páginas.")
                    break
                continue
            paginas_sin_nuevos = 0
            print(f"[Corotos] Página {pagina}: {len(enlaces)} anuncios nuevos.")

            for url in enlaces:
                if len(propiedades) >= limite:
                    break
                urls_vistas.add(url)
                time.sleep(self.PAUSA_SEGUNDOS)
                html_anuncio = self._solicitar(url, estatus)
                if not html_anuncio:
                    continue
                propiedad = self._parsear_propiedad(html_anuncio)

                if propiedad is not None:
                    propiedades.append(propiedad)

                    print(f"\n[{self.nombre}] {len(propiedades)}/{limite}")
                    print(f"Nombre: {propiedad.nombre}")
                    print(f"URL: {url}")

            if len(propiedades) < limite:
                time.sleep(self.PAUSA_SEGUNDOS)

        print(f"[Corotos] Total conseguido: {len(propiedades)} de {limite}.")
        return propiedades

    def obtener_propiedades(self, limite=200):
        """Alternativa para ejecutar una prueba sin EstatusScraping."""
        return self.extraer(estatus=None, limite=limite)