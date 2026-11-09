
from pathlib import Path

from scrapers.plusval_scraper import PlusvalScraper
from utils.data_processor import DataProcessor


# Crear el scraper
scraper = PlusvalScraper()

# Obtener solamente 3 propiedades de prueba
propiedades = scraper.obtener_propiedades(limite=200)

# Crear el procesador de datos
procesador = DataProcessor()

# Agregar las propiedades encontradas
for propiedad in propiedades:
    procesador.agregar_propiedad(propiedad)

# Convertir a tabla pandas
tabla = procesador.mostrar_resumen()

# Mostrar las propiedades en la terminal
print("\n=== PROPIEDADES ENCONTRADAS ===")

if not tabla.empty:

    print(tabla.to_string(index=False))

    # Crear carpeta de resultados
    Path("resultados").mkdir(exist_ok=True)

    # Guardar archivo Excel de prueba
    tabla.to_excel(
        "resultados/plusval_completo_200.xlsx",
        index=False
    )

    print("\nExcel guardado correctamente.")

else:
    print("No se encontraron propiedades.")
