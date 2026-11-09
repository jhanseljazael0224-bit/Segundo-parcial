# Segundo-parcial

# 🏠 Scraper Inmobiliario de República Dominicana

## 📌 Descripción del proyecto

Este proyecto consiste en el desarrollo de un **web scraper inmobiliario utilizando Python**, cuyo objetivo es recopilar, organizar y analizar información de propiedades publicadas en diferentes plataformas inmobiliarias de la República Dominicana.

El sistema utiliza técnicas de web scraping para extraer automáticamente información de las páginas **Plusval, Corotos y SuperCasas**, con una meta de **200 propiedades por plataforma, para un total de 600 propiedades**.

El proyecto forma parte de una actividad académica en la que aplicamos conocimientos de programación orientada a objetos, funciones, clases, librerías, procesamiento de datos y generación de reportes.

## 🎯 Objetivos

- Automatizar la extracción de información inmobiliaria.
- Obtener 200 propiedades de cada plataforma.
- Recopilar un total de 600 registros.
- Organizar la información utilizando pandas.
- Generar reportes estadísticos y visualizaciones en HTML.
- Exportar los resultados a Excel, Parquet y JSON.
- Registrar la duración de las solicitudes HTTP y del proceso completo.

## 🛠️ Tecnologías utilizadas

| Tecnología | Función |
|---|---|
| Python | Lenguaje principal del proyecto |
| Requests | Realizar solicitudes HTTP |
| BeautifulSoup (bs4) | Analizar HTML y extraer información |
| Pandas | Organizar y procesar los datos |
| ydata-profiling | Generar reportes estadísticos en HTML |
| Time | Medir la duración de las solicitudes |
| JSON | Almacenar el reporte de estatus |
| Git y GitHub | Control de versiones y colaboración |

## 📊 Información recopilada

Por cada propiedad se obtiene la siguiente información:

1. Fuente de información.
2. Nombre de la propiedad.
3. Precio.
4. Ubicación.
5. Vendedor.
6. Tamaño.
7. Número de habitaciones.
8. Número de baños.
9. Número de parqueos.

Algunos campos pueden aparecer vacíos cuando la plataforma no proporciona esa información.

## 📂 Estructura del proyecto

```text
Segundo-parcial/
│
├── main.py
├── config.py
├── requirements.txt
│
├── scrapers/
│   ├── base_scraper.py
│   ├── plusval_scraper.py
│   ├── corotos_scraper.py       # Pendiente
│   └── supercasas_scraper.py    # Pendiente
│
├── models/
│   └── propiedades.py
│
├── utils/
│   ├── data_processor.py
│   └── reportes.py
│
└── resultados/
```

## ⚙️ Funcionamiento

El sistema se divide en diferentes componentes:

**1. Scrapers:** se encargan de conectarse a las plataformas inmobiliarias y extraer la información mediante Requests y BeautifulSoup.

**2. Modelo Propiedad:** organiza los datos de cada inmueble mediante una clase de Python.

**3. DataProcessor:** recibe las propiedades extraídas y las convierte en un DataFrame utilizando pandas.

**4. EstatusScraping:** registra la fecha, la duración de las solicitudes HTTP, el tiempo total, la cantidad de propiedades obtenidas y las propiedades más cara y más barata.

**5. Exportador:** genera automáticamente los archivos de resultados y el reporte estadístico en HTML mediante ydata-profiling.

## 📁 Archivos generados

Al ejecutar el programa se generan los siguientes archivos en la carpeta `resultados`:

- `propiedades.xlsx`: tabla de propiedades en Excel.
- `propiedades.parquet`: conjunto de datos en formato Parquet.
- `reporte_datos.html`: reporte estadístico con visualizaciones.
- `estatus_scraping.json`: información de ejecución, solicitudes y tiempos.

## 🚀 Instalación y ejecución

**1. Clonar el repositorio:**

```bash
git clone https://github.com/jhanseljazael0224-bit/Segundo-parcial.git
```

**2. Entrar al proyecto:**

```bash
cd Segundo-parcial
```

**3. Instalar las dependencias:**

```bash
pip install -r requirements.txt
```

**4. Ejecutar el programa:**

```bash
python main.py
```

El programa ejecutará los scrapers habilitados en `main.py` y generará los reportes correspondientes.

## 📈 Estado del desarrollo

| Plataforma | Objetivo | Estado |
|---|---|---|
| Plusval | 200 propiedades | ✅ Implementado y probado |
| Corotos | 200 propiedades | ⏳ Pendiente |
| SuperCasas | 200 propiedades | ⏳ Pendiente |
| **Total** | **600 propiedades** | **En desarrollo** |

### Avances realizados

Se ha desarrollado e integrado exitosamente el scraper de **Plusval**, logrando extraer 200 propiedades y generar los reportes correspondientes.

El sistema también permite medir el tiempo de cada solicitud HTTP y procesar los registros utilizando pandas.

Actualmente, el proyecto continúa en desarrollo para incorporar las plataformas Corotos y SuperCasas y completar la recopilación de 600 propiedades.

## 🎓 Finalidad académica

Este proyecto tiene fines exclusivamente educativos y busca demostrar la aplicación práctica de los conocimientos adquiridos en Python, programación orientada a objetos, web scraping, análisis de datos y trabajo colaborativo mediante GitHub.

La recopilación de información debe respetar las condiciones de uso y las restricciones técnicas de cada plataforma.

---

**Proyecto académico — Segundo Parcial | Python y Web Scraping**
