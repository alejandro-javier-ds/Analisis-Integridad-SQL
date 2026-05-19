import pandas as pd
import pyodbc
from sqlalchemy import create_engine 
import urllib 

SERVER_NAME = r'(localdb)\MSSQLLocalDB'
DATABASE_NAME = 'PortafolioDB'

def get_sql_driver():
    available_drivers = pyodbc.drivers()
    target_drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]
    for driver in target_drivers:
        if driver in available_drivers:
            return driver
    return None

def extract_sql_data(server, database):
    driver = get_sql_driver()
    if not driver:
        print("[ERROR] No se encontraron drivers ODBC compatibles.")
        return None
        
    print(f"[INFO] Iniciando extracción de SQL Server: {server} | DB: {database}")
    
    try:
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;" 
        )
        conn = pyodbc.connect(conn_str)
        
        query = "SELECT * FROM dbo.VentasCrudas;"
        df = pd.read_sql(query, conn)
        
        print(f"[INFO] Extracción completada. Volúmen de registros: {len(df)}")
        return df

    except pyodbc.Error as e:
        print(f"[ERROR] Fallo en la infraestructura de conexión: {e}")
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def audit_data(df):
    print(f"[INFO] Iniciando motor de auditoría. Evaluando {len(df)} registros...")
    
    mask_nulos = df.isnull().any(axis=1) | (df['Producto'] == '')
    mask_cantidad = df['Cantidad'] <= 0
    mask_precio = df['Precio_Unitario'] < 0
    mask_correo = ~df['Correo'].astype(str).str.contains(r'^[\w\.-]+@[\w\.-]+\.\w+$', regex=True, na=False)

    df['Is_Corrupt'] = mask_nulos | mask_cantidad | mask_precio | mask_correo
    
    df_clean = df[~df['Is_Corrupt']].drop(columns=['Is_Corrupt']).copy()
    df_corrupt = df[df['Is_Corrupt']].copy()

    print("[INFO] Auditoría finalizada.")
    print(f"[METRICS] Registros validados (Limpios): {len(df_clean)}")
    print(f"[METRICS] Registros anómalos (Basura): {len(df_corrupt)}")
    
    return df_clean, df_corrupt

def load_data_to_sql(df_clean, df_corrupt, server, database):
    driver = get_sql_driver()
    if not driver:
        print("[ERROR] No se pudo obtener el driver para la carga.")
        return

    print(f"[INFO] Iniciando proceso de carga hacia SQL Server...")
    
    try:
        params = urllib.parse.quote_plus(
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
        
        print("[INFO] Indexando 'VentasLimpias'...")
        df_clean.to_sql('VentasLimpias', con=engine, if_exists='replace', index=False)
        
        print("[INFO] Indexando 'VentasBasura'...")
        df_corrupt_out = df_corrupt.drop(columns=['Is_Corrupt'], errors='ignore')
        df_corrupt_out.to_sql('VentasBasura', con=engine, if_exists='replace', index=False)
        
        print("[INFO] Carga completada exitosamente. Pipeline ETL cerrado.")
        
    except Exception as e:
        print(f"[ERROR] Ocurrió un problema durante la carga: {e}")

if __name__ == "__main__":
    df_ventas = extract_sql_data(SERVER_NAME, DATABASE_NAME)
    
    if df_ventas is not None:
        df_clean, df_corrupt = audit_data(df_ventas)
        
        if not df_corrupt.empty:
            print("\n[INFO] Muestra de registros anómalos detectados (Top 5):")
            print(df_corrupt[['ID_Venta', 'Producto', 'Cantidad', 'Precio_Unitario', 'Correo']].head())
            print("-" * 50)
            
        load_data_to_sql(df_clean, df_corrupt, SERVER_NAME, DATABASE_NAME)