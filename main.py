
"""
Programa principal del scraper inmobiliario.

Permite seleccionar una o todas las plataformas.
Une los scrapers, el procesamiento de datos
y la generación de reportes.
"""

import config

from utils.data_processor import DataProcessor
from utils.reportes import EstatusScraping, Exportador

from scrapers.plusval_scraper import PlusvalScraper
from scrapers.corotos_scraper import CorotosScraper
from scrapers.supercasas_scraper import SuperCasasScraper


# Lista de scrapers disponibles
SCRAPERS = [
    PlusvalScraper(),
    CorotosScraper(),
    SuperCasasScraper()
]


def seleccionar_scrapers():
    """Muestra un menú para seleccionar las páginas."""

    while True:
        print("\n========== SCRAPER INMOBILIARIO RD ==========")
        print("Selecciona dónde quieres buscar:\n")

        print("1. Plusval")
        print("2. Corotos")
        print("3. SuperCasas")
        print("4. Todas las páginas")
        print("0. Salir")

        opcion = input("\nElige una opción: ").strip()

        if opcion == "1":
            return [SCRAPERS[0]]

        elif opcion == "2":
            return [SCRAPERS[1]]

        elif opcion == "3":
            return [SCRAPERS[2]]

        elif opcion == "4":
            return SCRAPERS

        elif opcion == "0":
            return []

        else:
            print("\nOpción inválida. Intenta nuevamente.")


def main():

    # Seleccionar los scrapers
    scrapers_seleccionados = seleccionar_scrapers()

    if len(scrapers_seleccionados) == 0:
        print("\nPrograma finalizado.")
        return

    procesador = DataProcessor()
    estatus = EstatusScraping(config.integrantes)

    estatus.iniciar()

    for s in scrapers_seleccionados:

        print(f"\nExtrayendo propiedades de {s.nombre}...")

        propiedades = s.extraer(
            estatus,
            config.max_propiedades
        )

        for p in propiedades:
            procesador.agregar_propiedad(p)

        print(
            f"{len(propiedades)} propiedades "
            f"extraídas de {s.nombre}"
        )

    estatus.finalizar()

    # Generar tabla y reportes
    tabla = procesador.mostrar_resumen()
    resumen = estatus.mostrar(tabla)

    Exportador("resultados").exportar_todo(tabla, resumen)

    print("\n========== PROCESO FINALIZADO ==========")
    print("Total de propiedades:", len(tabla))
    print("Archivos guardados en: resultados/")


if __name__ == "__main__":
    main()
