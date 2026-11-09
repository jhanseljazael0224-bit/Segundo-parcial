import pandas as pd

class DataProcessor:
    def __init__(self):
        self.propiedades = []
    
    def agregar_propiedad(self, propiedad):
        self.propiedades.append(propiedad.mostrar_informacion())
        
    def convertir_dataframe(self):
        columnas = [
            "Fuente",
            "Nombre",
            "Precio",
            "Ubicacion",
            "Vendedor",
            "Tamaño",
            "Habitaciones",
            "Baños",
            "Parqueos"
        ]
        return pd.DataFrame(self.propiedades)
    
    def mostrar_resumen(self):
        dataframe = self.convertir_dataframe()
        
        print("\nResumen de propiedades:\n")
        print("-"*40)
        print("Total de propiedades:", len(dataframe))
        return dataframe
    