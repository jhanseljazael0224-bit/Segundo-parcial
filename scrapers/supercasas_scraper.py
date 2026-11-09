
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import config
from models.propiedades import Propiedad
from scrapers.base_scraper import BaseScraper


class SuperCasasScraper(BaseScraper):
    BASE_URL = "https://www.supercasas.com"
    LISTADO = BASE_URL + "/buscar"
    MAX_PAGINAS = 35
    PAUSA_SEGUNDOS = 1.0
    PATRON_ANUNCIO = re.compile(r"/[^/]+/\d{5,}/?$")
    PATRON_PRECIO = re.compile(r"(?:US|RD)\$\s*[\d.,]+", re.I)

    def __init__(self):
        super().__init__("SuperCasas", self.BASE_URL)
        self.nombre = "SuperCasas"
        if not hasattr(self, "session") or self.session is None:
            self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0 Safari/537.36",
            "Accept-Language": "es-DO,es;q=0.9,en;q=0.7",
        })

    def obtener_html(self, url=None):
        #Descarga el HTML (cuando no se está midiendo por EstatusScraping)
        url = url or getattr(self, "url", None) or self.LISTADO
        try:
            respuesta = self.session.get(url, timeout=config.timeout)
            respuesta.raise_for_status()
            return respuesta.text
        except requests.RequestException as error:
            print(f"[SuperCasas] Error descargando {url}: {error}")
            return None

    def _solicitar(self, url, estatus):
        """Registra el tiempo de *cada* request usando el sistema del proyecto."""
        if estatus is None:
            return self.obtener_html(url)
        try:
            return estatus.obtener_html_medido(self, url)
        except requests.RequestException as error:
            print(f"[SuperCasas] Request fallido ({url}): {error}")
            return None

    @staticmethod
    def _texto(elemento):
        return elemento.get_text(" ", strip=True) if elemento else ""

    @staticmethod
    def _numero(texto, campo, decimales=False):
        coincidencia = re.search(
            rf"\b{campo}\s*:\s*(\d+(?:[.,]\d+)?)", texto, re.I
        )
        if not coincidencia:
            return None
        valor = coincidencia.group(1).replace(",", ".")
        return float(valor) if decimales else int(float(valor))

    @staticmethod
    def _tamano(texto):
        # En /buscar aparece: Construcción: 150 Mt2; en otros listados,
        # 150 Mt2 Construcción. Preferir construcción sobre solar.
        for campo in (r"Construcci[oó]n", r"Solar|Terreno"):
            patrones = (
                rf"(?:{campo})\s*:\s*([\d.,]+)\s*(?:Mt2|m2|m²)",
                rf"([\d.,]+)\s*(?:Mt2|m2|m²)\s*(?:{campo})",
            )
            for patron in patrones:
                hallazgo = re.search(patron, texto, re.I)
                if hallazgo:
                    return hallazgo.group(1) + " m²"
        return None

    @classmethod
    def _precio(cls, texto):
        # Preferimos el precio de VENTA cuando un anuncio tiene venta y alquiler.
        venta = re.search(
            r"\bVenta(?:\s+Amueblad[ao])?\s*:\s*"
            r"((?:US|RD)\$\s*[\d.,]+)", texto, re.I
        )
        if venta:
            return re.sub(r"\s+", " ", venta.group(1)).strip()
        encontrado = cls.PATRON_PRECIO.search(texto)
        return encontrado.group(0).strip() if encontrado else None

    @classmethod
    def _tarjetas(cls, html):
        """Extrae URLs únicas y datos de los anuncios desde el listado."""
        soup = BeautifulSoup(html, "html.parser")
        resultados = []
        urls_vistas = set()

        for enlace in soup.find_all("a", href=True):
            url = urljoin(cls.BASE_URL, enlace["href"])
            parsed = urlparse(url)
            if parsed.netloc not in ("www.supercasas.com", "supercasas.com"):
                continue
            if not cls.PATRON_ANUNCIO.fullmatch(parsed.path):
                continue
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if url in urls_vistas:
                continue

            # El enlace suele contener el nombre y el precio. Las características
            # pueden estar en un contenedor padre adyacente.
            texto_enlace = cls._texto(enlace)
            texto_datos = texto_enlace
            padre = enlace.parent
            for _ in range(3):
                if padre is None:
                    break
                candidato = cls._texto(padre)
                if len(candidato) <= 1300 and (
                    "Habitaciones:" in candidato or "Construcción:" in candidato
                    or "Baños:" in candidato
                ):
                    texto_datos = candidato
                    break
                padre = padre.parent

            # Evitar anuncios sin precio publicable.
            if cls._precio(texto_datos) is None:
                continue
            urls_vistas.add(url)
            resultados.append((url, texto_enlace, texto_datos))
        return resultados

    @staticmethod
    def _ubicacion(titulo, texto_tarjeta):
        # Ej.: "Apartamento en Venta y Alquiler, Punta Cana Village"
        if "," in titulo:
            parte = titulo.rsplit(",", 1)[-1].strip()
            if parte:
                return parte
        # Ej.: "Apartamento Punta Cana Village Venta: US$ 410,000"
        match = re.search(
            r"^(?:Apartamento|Casa|Villa|Solar|Penthouse|Terreno|"
            r"Local Comercial|Nave|Oficina|Edificio|Finca|Townhouse|Negocio)"
            r"\s+(.+?)\s+(?:Venta|Alquiler)(?:\s+Amueblad[ao])?\s*:",
            texto_tarjeta, re.I
        )
        return match.group(1).strip() if match else None

    @staticmethod
    def _vendedor(soup):
        # En fichas reales aparece un encabezado "Datos de Contacto"
        # seguido por un <h3> con el nombre del vendedor.
        for tag in soup.find_all(["h2", "h3", "h4"]):
            if "datos de contacto" in tag.get_text(" ", strip=True).lower():
                siguiente = tag.find_next(["h3", "h4"])
                if siguiente:
                    nombre = siguiente.get_text(" ", strip=True)
                    if nombre and len(nombre) < 150:
                        return nombre

        texto = soup.get_text(" ", strip=True)
        match = re.search(
            r"Datos de Contacto\s+(.{2,90}?)\s+"
            r"(?:Particular|Inmobiliaria|Tel\s*:|Cel\s*:|WhatsApp\s*:)",
            texto, re.I
        )
        return match.group(1).strip() if match else None

    @classmethod
    def _parsear_propiedad(cls, html, texto_enlace, texto_tarjeta):
        """Fusiona datos del listado y ficha, devuelve Propiedad o None."""
        soup = BeautifulSoup(html, "html.parser") if html else None
        h1 = soup.find("h1") if soup else None
        titulo = cls._texto(h1)

        # Cuando no hay ficha disponible, conservar la información del listado.
        if not titulo:
            titulo = re.split(
                r"\b(?:Venta|Alquiler)(?:\s+Amueblad[ao])?\s*:",
                texto_enlace, maxsplit=1, flags=re.I
            )[0].strip(" «»/-")
        if not titulo:
            return None

        precio = cls._precio(texto_tarjeta)
        if not precio and soup:
            # Solo consultar el encabezado de la ficha, no anuncios similares.
            encabezados = soup.find_all(["h1", "h2", "h3"])
            for candidato in encabezados[:5]:
                precio = cls._precio(cls._texto(candidato))
                if precio:
                    break
        if not precio:
            return None

        ubicacion = cls._ubicacion(titulo, texto_enlace)
        vendedor = cls._vendedor(soup) if soup else None
        habitaciones = cls._numero(texto_tarjeta, "Habitaciones")
        banos = cls._numero(texto_tarjeta, "Baños", decimales=True)
        parqueos = cls._numero(texto_tarjeta, "Parqueos")
        tamano = cls._tamano(texto_tarjeta)

        # Si el listado omite características, intentar recuperarlas del anuncio.
        if soup and any(x is None for x in (habitaciones, banos, parqueos, tamano)):
            texto_ficha = soup.get_text(" ", strip=True)
            texto_ficha = texto_ficha.split("Anuncios Similares", 1)[0]
            habitaciones = habitaciones if habitaciones is not None else cls._numero(texto_ficha, "Habitaciones")
            banos = banos if banos is not None else cls._numero(texto_ficha, "Baños", decimales=True)
            parqueos = parqueos if parqueos is not None else cls._numero(texto_ficha, "Parqueos")
            tamano = tamano if tamano is not None else cls._tamano(texto_ficha)

        return Propiedad(
            "SuperCasas", titulo, precio, ubicacion, vendedor,
            tamano, habitaciones, banos, parqueos
        )

    def extraer(self, estatus=None, limite=200):
        """Busca hasta `limite` propiedades, evitando repetir IDs/URLs."""
        if limite <= 0:
            return []

        propiedades = []
        urls_vistas = set()
        paginas_sin_nuevos = 0

        for pagina in range(self.MAX_PAGINAS):
            if len(propiedades) >= limite:
                break

            url_listado = (
                self.LISTADO if pagina == 0
                else f"{self.LISTADO}?PagingPageSkip={pagina}"
            )
            if pagina:
                time.sleep(self.PAUSA_SEGUNDOS)
            html = self._solicitar(url_listado, estatus)
            if not html:
                print("[SuperCasas] No se pudo cargar el listado. Deteniendo.")
                break

            tarjetas = [
                tarjeta for tarjeta in self._tarjetas(html)
                if tarjeta[0] not in urls_vistas
            ]
            if not tarjetas:
                paginas_sin_nuevos += 1
                if paginas_sin_nuevos >= 2:
                    print("[SuperCasas] Dos páginas sin anuncios nuevos; finalizado.")
                    break
                continue
            paginas_sin_nuevos = 0
            print(f"[SuperCasas] Página {pagina+1}: {len(tarjetas)} anuncios nuevos.")

            for url, texto_enlace, texto_tarjeta in tarjetas:
                if len(propiedades) >= limite:
                    break
                urls_vistas.add(url)
                time.sleep(self.PAUSA_SEGUNDOS)
                html_ficha = self._solicitar(url, estatus)
                propiedad = self._parsear_propiedad(
                    html_ficha, texto_enlace, texto_tarjeta
                )
                if propiedad is not None:
                    propiedades.append(propiedad)
                    print(f"[SuperCasas] {len(propiedades)}/{limite}: {url}")

        print(f"[SuperCasas] Total: {len(propiedades)} de {limite}.")
        return propiedades

    def obtener_propiedades(self, limite=200):
        """Compatibilidad con scripts de prueba sin reporte de tiempos."""
        return self.extraer(estatus=None, limite=limite)