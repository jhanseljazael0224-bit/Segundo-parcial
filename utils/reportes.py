"""
Modulo de reportes y exportacion del scraper.

Contiene:
- EstatusScraping: mide el tiempo de cada request con la libreria time y arma
  el reporte de estatus (fecha, autores, tiempos, total, mas cara y mas barata).
- Exportador: exporta la tabla a Excel y Parquet, el reporte de ydata-profiling
  a HTML y el estatus a JSON.
"""

import json
import os
import re
import time
from datetime import datetime

import pandas as pd


TASA_DOLAR = 60  # pesos dominicanos por dolar (aproximado), para comparar precios en RD$ y US$


def limpiar_precio(precio, tasa=TASA_DOLAR):
    """Convierte un precio como 'US$ 150,000' o 'RD$ 8,500,000.00' en dolares (numero).
    Si el precio esta en pesos (RD$), lo divide entre la tasa para poder compararlo.
    Devuelve None si no se puede convertir."""
    if precio is None:
        return None
    if isinstance(precio, (int, float)):
        return float(precio)

    texto = str(precio).replace(",", "")
    numeros = re.findall(r"\d+(?:\.\d+)?", texto)
    if not numeros:
        return None
    valor = float(numeros[0])
    if "RD" in texto.upper():
        valor = valor / tasa
    return valor


class EstatusScraping:
    """Lleva el control del tiempo del scraping y genera el reporte de estatus."""

    def __init__(self, autores):
        self.autores = autores
        self.requests = []          # una entrada por cada request realizado
        self.inicio = None
        self.fin = None

    def iniciar(self):
        """Marca el inicio del scraping."""
        self.inicio = time.time()

    def finalizar(self):
        """Marca el final del scraping."""
        self.fin = time.time()

    def registrar_request(self, fuente, url, segundos, exito=True):
        """Guarda el tiempo que tardo un request."""
        self.requests.append({
            "fuente": fuente,
            "url": url,
            "segundos": round(segundos, 3),
            "exito": exito,
        })

    def obtener_html_medido(self, scraper, url=None):
        """Llama a scraper.obtener_html() midiendo cuanto tarda.
        Si se pasa una url (por ejemplo, la pagina 2 del listado), se usa esa."""
        if url:
            scraper.url = url

        t0 = time.time()
        html = scraper.obtener_html()
        t1 = time.time()

        self.registrar_request(scraper.nombre, scraper.url, t1 - t0, exito=html is not None)
        return html

    def duracion_total(self):
        """Segundos entre iniciar() y finalizar()."""
        if self.inicio is None:
            return 0
        fin = self.fin if self.fin is not None else time.time()
        return round(fin - self.inicio, 3)

    def _propiedad_extremo(self, df, mas_cara=True):
        """Busca la propiedad mas cara o la mas barata de la tabla."""
        if df.empty or "Precio" not in df.columns:
            return None

        precios = df["Precio"].apply(limpiar_precio)
        if precios.dropna().empty:
            return None

        i = precios.idxmax() if mas_cara else precios.idxmin()
        fila = df.loc[i]
        return {
            "fuente": str(fila.get("Fuente de info", "")),
            "nombre": str(fila.get("Nombre", "")),
            "precio": str(fila.get("Precio", "")),
            "ubicacion": str(fila.get("Ubicación", "")),
        }

    def generar(self, df):
        """Arma el diccionario con el reporte de estatus del scraping."""
        tiempos = [r["segundos"] for r in self.requests]
        por_fuente = {}
        if "Fuente de info" in df.columns:
            por_fuente = df["Fuente de info"].value_counts().to_dict()

        return {
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "autores": self.autores,
            "tiempo_duracion_total_seg": self.duracion_total(),
            "total_requests": len(self.requests),
            "tiempo_promedio_por_request_seg": round(sum(tiempos) / len(tiempos), 3) if tiempos else 0,
            "tiempos_por_request": self.requests,
            "numero_propiedades_scrapeadas": len(df),
            "propiedades_por_fuente": por_fuente,
            "propiedad_mas_cara": self._propiedad_extremo(df, mas_cara=True),
            "propiedad_mas_barata": self._propiedad_extremo(df, mas_cara=False),
        }

    def mostrar(self, df):
        """Muestra un resumen del estatus por consola."""
        est = self.generar(df)
        print("\n========== ESTATUS DEL SCRAPING ==========")
        print("Fecha y hora:", est["fecha_hora"])
        print("Autores:", ", ".join(est["autores"]))
        print("Duracion total:", est["tiempo_duracion_total_seg"], "seg")
        print("Requests realizados:", est["total_requests"])
        print("Promedio por request:", est["tiempo_promedio_por_request_seg"], "seg")
        print("Propiedades scrapeadas:", est["numero_propiedades_scrapeadas"])
        print("Mas cara:", est["propiedad_mas_cara"])
        print("Mas barata:", est["propiedad_mas_barata"])
        print("==========================================")
        return est


class Exportador:
    """Exporta los resultados del scraping a distintos formatos."""

    def __init__(self, carpeta="resultados"):
        self.carpeta = carpeta
        os.makedirs(self.carpeta, exist_ok=True)

    def _ruta(self, nombre):
        return os.path.join(self.carpeta, nombre)

    def a_excel(self, df, nombre="propiedades.xlsx"):
        ruta = self._ruta(nombre)
        df.to_excel(ruta, index=False)
        print("Excel exportado:", ruta)
        return ruta

    def a_parquet(self, df, nombre="propiedades.parquet"):
        ruta = self._ruta(nombre)
        # Parquet necesita tipos consistentes en cada columna, por eso se pasa todo a texto
        df.astype(str).to_parquet(ruta, index=False)
        print("Parquet exportado:", ruta)
        return ruta

    def a_perfil_html(self, df, nombre="reporte_datos.html", titulo="Reporte de propiedades RD"):
        from ydata_profiling import ProfileReport

        ruta = self._ruta(nombre)
        perfil = ProfileReport(df, title=titulo, explorative=True)
        perfil.to_file(ruta)
        print("Reporte ydata-profiling exportado:", ruta)
        return ruta

    def a_json(self, estatus, nombre="estatus_scraping.json"):
        ruta = self._ruta(nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(estatus, f, ensure_ascii=False, indent=4, default=str)
        print("JSON de estatus exportado:", ruta)
        return ruta

    def exportar_todo(self, df, estatus):
        """Genera los 4 archivos que pide el proyecto."""
        return {
            "excel": self.a_excel(df),
            "parquet": self.a_parquet(df),
            "html": self.a_perfil_html(df),
            "json": self.a_json(estatus),
        }
