import pandas as pd
import random

registros = []
productos = ['Laptop HP', 'Mouse Logitech', 'Monitor Dell', 'Teclado Razer', '']

for i in range(1, 1001):
    id_venta = i
    producto = random.choice(productos) 
    cantidad = random.choice([-2, 0, 1, 1, 2, 3, 5]) 
    precio = round(random.uniform(-100, 2000), 2)
    correo = random.choice(['cliente@gmail.com', 'ventas@hotmail.com', 'NO_TIENE', 'correo_sin_arroba.com', None])
    
    registros.append([id_venta, producto, cantidad, precio, correo])

df = pd.DataFrame(registros, columns=['ID_Venta', 'Producto', 'Cantidad', 'Precio_Unitario', 'Correo'])
df.to_csv('ventas_crudas.csv', index=False, encoding='utf-8')

print("[INFO] Generación de dataset sintético completada. Archivo exportado: 'ventas_crudas.csv'.")