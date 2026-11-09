
import re
import time
from urllib.parse import (
    urljoin,
    urlsplit,
    urlunsplit,
    parse_qsl,
    urlencode
)

import requests

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
    def obtener_vendedores(self, enlace):
        try:
            respuesta = self.session.get(
                enlace,
                timeout=30
            )

            respuesta.raise_for_status()

        except requests.RequestException as error:
            print("Error al consultar vendedor:", error)
            return None

        soup = self.analizar_html(respuesta.text)

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

    # Extraer las propiedades de varias páginas
    def obtener_propiedades(self, limite=200):

        if limite <= 0:
            return []

        html = self.obtener_html()

        if not html:
            print("No se pudo descargar Plusval.")
            return []

        soup = self.analizar_html(html)

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
            self.url,
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

            try:
                respuesta = self.session.get(
                    url,
                    timeout=30
                )

                respuesta.raise_for_status()

            except requests.RequestException as error:
                print("Error de conexión:", error)
                break

            duracion = time.perf_counter() - inicio

            soup_pagina = self.analizar_html(
                respuesta.text
            )

            tarjetas = soup_pagina.select("a.property")

            nuevas = 0

            for tarjeta in tarjetas:

                enlace = tarjeta.get("href", "")

                # Ignorar tarjetas sin enlace real
                if not urlsplit(enlace).path.startswith(
                    "/propiedad/"
                ):
                    continue

                enlace_completo = urljoin(
                    respuesta.url,
                    enlace
                )

                # Evitar duplicados
                if enlace_completo in enlaces_vistos:
                    continue

                propiedad = self.extraer_tarjeta(
                    tarjeta
                )

                if propiedad is None:
                    continue

                # Consultar los asesores inmobiliarios
                propiedad.vendedor = self.obtener_vendedores(
                    enlace_completo
                )

                # Guardar una sola vez
                enlaces_vistos.add(enlace_completo)
                propiedades.append(propiedad)

                nuevas += 1

                print(
                    f"Propiedad {len(propiedades)}: "
                    f"{propiedad.nombre[:45]}"
                )

                # Detener al alcanzar el límite
                if len(propiedades) >= limite:
                    break

                # Pausa entre solicitudes de detalles
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

        duracion_total = time.perf_counter() - inicio_total

        print("\n=== RESULTADO FINAL ===")
        print("Total de propiedades:", len(propiedades))
        print(
            "Tiempo total:",
            round(duracion_total, 2),
            "segundos"
        )

        return propiedades
