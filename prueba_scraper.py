
from scrapers.base_scraper import BaseScraper 


# Crear nuestro scraper de prueba
scraper = BaseScraper(
    "Página de prueba",
    "https://example.com"
)

# Obtener el HTML
html = scraper.obtener_html()

# Analizar la página
if html:
    soup = scraper.analizar_html(html)

    print("¡Conexión exitosa!")

    if soup.title:
        print("Título:", soup.title.text)

else:
    print("No se pudo conectar con la página.")
