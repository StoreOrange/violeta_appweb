import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://superuser:1234@localhost:5432/GESTIONDB')

tablas = ['tarea', 'usuario', 'proyecto', 'estado', 'prioridad', 'estado', 'roll']


with pd.ExcelWriter('Gestiondb_ETL.xlsx', engine='openpyxl') as writer:
    for tabla in tablas:
        df = pd.read_sql(f'SELECT * FROM {tabla}', engine)
        df.to_excel(writer, sheet_name=tabla, index=False)


print("Exportación a Excel completada exitosamente.")        
