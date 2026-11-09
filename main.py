"""
Programa principal del scraper.

Une las partes del proyecto:
1. Cada scraper extrae sus propiedades (Corotos, SuperCasas y Plusval).
2. DataProcessor junta todo en una tabla de pandas.
3. EstatusScraping mide los tiempos y arma el reporte de estatus.
4. Exportador genera el Excel, el Parquet, el HTML de ydata-profiling y el JSON.

Para conectar un scraper, este debe tener un metodo:
    extraer(estatus, limite) -> lista de objetos Propiedad
y dentro debe pedir cada pagina con:
    html = estatus.obtener_html_medido(self, url_de_la_pagina)
para que el tiempo de cada request quede registrado.
"""

import config
from utils.data_processor import DataProcessor
from utils.reportes import EstatusScraping, Exportador

# Cuando esten listos, se importan y se agregan aqui, por ejemplo:
# from scrapers.corotos_scraper import CorotosScraper
# from scrapers.supercasas_scraper import SuperCasasScraper
from scrapers.plusval_scraper import PlusvalScraper
from scrapers.corotos_scraper import CorotosScraper

SCRAPERS = [
    PlusvalScraper(),
    CorotosScraper(),
    #SuperCasasScraper()
]


def main():
    procesador = DataProcessor()
    estatus = EstatusScraping(config.integrantes)

    if len(SCRAPERS) == 0:
        print("No hay scrapers conectados todavia. Agregalos en la lista SCRAPERS de main.py.")
        print("Para probar los reportes con datos de ejemplo, ejecuta: python prueba_reportes.py")
        return

    estatus.iniciar()
    for s in SCRAPERS:
        print(f"\nExtrayendo propiedades de {s.nombre}...")
        propiedades = s.extraer(estatus, config.max_propiedades)
        for p in propiedades:
            procesador.agregar_propiedad(p)
        print(f"{len(propiedades)} propiedades extraidas de {s.nombre}")
    estatus.finalizar()

    tabla = procesador.mostrar_resumen()
    resumen = estatus.mostrar(tabla)
    Exportador("resultados").exportar_todo(tabla, resumen)


if __name__ == "__main__":
    main()
