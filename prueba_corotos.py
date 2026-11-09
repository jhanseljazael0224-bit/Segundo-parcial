
from pathlib import Path

from scrapers.corotos_scraper import CorotosScraper
from utils.data_processor import DataProcessor


def main():
    scraper = CorotosScraper()
    propiedades = scraper.obtener_propiedades(limite=3)
    procesador = DataProcessor()

    for propiedad in propiedades:
        procesador.agregar_propiedad(propiedad)

    tabla = procesador.mostrar_resumen()
    print("\nRegistros extraídos:", len(tabla))
    if tabla.empty:
        print("No se encontraron anuncios. Revisa conexión, acceso y HTML de Corotos.")
        return

    print(tabla.to_string(index=False))
    Path("resultados").mkdir(exist_ok=True)
    tabla.to_excel("resultados/corotos_prueba_3.xlsx", index=False)
    print("Excel creado en resultados/corotos_prueba_3.xlsx")


if __name__ == "__main__":
    main()
