
import re
import time
from urllib.parse import (
    urljoin,
    urlsplit,
    urlunsplit,
    parse_qsl,
    urlencode
)

from scrapers.base_scraper import BaseScraper
from models.propiedades import Propiedad


class PlusvalScraper(BaseScraper):

    def __init__(self):
        super().__init__(
            "Plusval",
            "https://plusval.com.do/apartamentos/venta"
        )

    # Extraer habitaciones, baños, parqueos y tamaño
    def extraer_caracteristicas(self, tarjeta):
        datos = {}

        elementos = tarjeta.select(
            "ul.property-characteristics li"
        )

        for elemento in elementos:
            etiqueta = elemento.select_one("span.tooltip")

            if etiqueta is None:
                continue

            nombre = etiqueta.get_text(strip=True)
            texto = elemento.get_text(" ", strip=True)

            encontrado = re.search(
                r"\d+(?:[.,]\d+)?",
                texto
            )

            if encontrado:
                numero = float(
                    encontrado.group().replace(",", ".")
                )

                if numero.is_integer():
                    numero = int(numero)

                datos[nombre] = numero

        return datos

    # Extraer los datos principales de cada propiedad
    def extraer_tarjeta(self, tarjeta):

        etiqueta_nombre = tarjeta.select_one("h4")

        etiqueta_ubicacion = tarjeta.select_one(
            "span.label.medium-label"
        )

        etiqueta_precio = tarjeta.select_one(
            ".offer-price h2"
        )

        if etiqueta_precio is None:
            etiqueta_precio = tarjeta.select_one(
                "p.lead.font-pulpBold"
            )

        if etiqueta_nombre is None or etiqueta_precio is None:
            return None

        nombre = etiqueta_nombre.get_text(strip=True)
        precio = etiqueta_precio.get_text(strip=True)

        ubicacion = None

        if etiqueta_ubicacion:
            ubicacion = etiqueta_ubicacion.get_text(
                " ", strip=True
            )

        caracteristicas = self.extraer_caracteristicas(
            tarjeta
        )

        propiedad = Propiedad(
            fuente="Plusval",
            nombre=nombre,
            precio=precio,
            ubicacion=ubicacion,
            vendedor=None,
            tamaño=caracteristicas.get("Construcción"),
            habitaciones=caracteristicas.get("Habitaciones"),
            baños=caracteristicas.get("Baños"),
            parqueos=caracteristicas.get("Parqueos")
        )

        return propiedad

    # Cambiar el número de página en la URL
    def cambiar_pagina(self, url, numero):
        partes = urlsplit(url)

        parametros = parse_qsl(partes.query)

        parametros = [
            (clave, valor)
            for clave, valor in parametros
            if clave != "page"
        ]

        parametros.append(("page", str(numero)))

        return urlunsplit((
            partes.scheme,
            partes.netloc,
            partes.path,
            urlencode(parametros),
            partes.fragment
        ))

    # Obtener los asesores inmobiliarios de una propiedad
    # Ahora registra el tiempo de cada solicitud
    def obtener_vendedores(self, enlace, estatus):

        html = estatus.obtener_html_medido(
            self,
            enlace
        )

        if not html:
            print("No se pudo consultar el vendedor.")
            return None

        soup = self.analizar_html(html)

        if soup is None:
            return None

        etiquetas = soup.select(
            ".associates .agent-preview .agent-information h6"
        )

        nombres = []

        for etiqueta in etiquetas:
            nombre = etiqueta.get_text(strip=True)

            if nombre and nombre not in nombres:
                nombres.append(nombre)

        if nombres:
            return "; ".join(nombres)

        return None

    # Extraer propiedades de varias páginas
    # Método compatible con el main.py del equipo
    def extraer(self, estatus, limite=200):

        if limite <= 0:
            return []

        # Guardamos la URL inicial de Plusval
        url_inicio = (
            "https://plusval.com.do/apartamentos/venta"
        )

        # Primera solicitud, con medición de tiempo
        html = estatus.obtener_html_medido(
            self,
            url_inicio
        )

        if not html:
            print("No se pudo descargar Plusval.")
            return []

        soup = self.analizar_html(html)

        if soup is None:
            return []

        enlace_busqueda = None

        for elemento in soup.select("a[href]"):
            texto = elemento.get_text(
                " ", strip=True
            ).upper()

            if "MÁS APARTAMENTOS LISTOS" in texto:
                enlace_busqueda = elemento.get("href")
                break

        if not enlace_busqueda:
            print("No se encontró el enlace de búsqueda.")
            return []

        url_base = urljoin(
            url_inicio,
            enlace_busqueda
        )

        propiedades = []
        enlaces_vistos = set()

        inicio_total = time.perf_counter()

        # Recorrer un máximo de 15 páginas
        for pagina in range(1, 16):

            if len(propiedades) >= limite:
                break

            url = self.cambiar_pagina(
                url_base,
                pagina
            )

            print(f"\nConsultando página {pagina}...")

            inicio = time.perf_counter()

            # Solicitud registrada por EstatusScraping
            html_pagina = estatus.obtener_html_medido(
                self,
                url
            )

            duracion = time.perf_counter() - inicio

            if not html_pagina:
                print("Error de conexión.")
                break

            soup_pagina = self.analizar_html(
                html_pagina
            )

            if soup_pagina is None:
                break

            tarjetas = soup_pagina.select(
                "a.property"
            )

            nuevas = 0

            for tarjeta in tarjetas:

                enlace = tarjeta.get("href", "")

                # Ignorar tarjetas sin enlace real
                if not urlsplit(enlace).path.startswith(
                    "/propiedad/"
                ):
                    continue

                enlace_completo = urljoin(
                    url,
                    enlace
                )

                # Evitar propiedades duplicadas
                if enlace_completo in enlaces_vistos:
                    continue

                propiedad = self.extraer_tarjeta(
                    tarjeta
                )

                if propiedad is None:
                    continue

                # Consultar vendedores con medición
                propiedad.vendedor = self.obtener_vendedores(
                    enlace_completo,
                    estatus
                )

                # Guardar propiedad una sola vez
                enlaces_vistos.add(enlace_completo)
                propiedades.append(propiedad)

                nuevas += 1

                print(
                    f"Propiedad {len(propiedades)}: "
                    f"{propiedad.nombre[:45]}"
                )

                # Detenerse al alcanzar el límite
                if len(propiedades) >= limite:
                    break

                # Pausa entre solicitudes
                time.sleep(2)

            print(
                "Duración de la página:",
                round(duracion, 2),
                "segundos"
            )

            print("Propiedades nuevas:", nuevas)
            print("Total acumulado:", len(propiedades))

            if nuevas == 0:
                print("No hay propiedades nuevas.")
                break

            if len(propiedades) < limite:
                time.sleep(2)

        duracion_total = (
            time.perf_counter() - inicio_total
        )

        print("\n=== RESULTADO FINAL ===")
        print("Total de propiedades:", len(propiedades))
        print(
            "Tiempo total:",
            round(duracion_total, 2),
            "segundos"
        )

        return propiedades

    # Mantener compatibilidad con nuestras pruebas anteriores
    def obtener_propiedades(self, limite=200):

        from utils.reportes import EstatusScraping

        estatus = EstatusScraping([])
        estatus.iniciar()

        propiedades = self.extraer(
            estatus,
            limite
        )

        estatus.finalizar()

        return propiedades
