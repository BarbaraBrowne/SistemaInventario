import sqlite3
import pandas as pd
import cv2
import pytesseract
from pyzbar.pyzbar import decode
from datetime import datetime, timedelta
import os
import re

# Configuración de Tesseract (para OCR)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Ajusta esta ruta según tu instalación

# Crear o conectar a la base de datos
conn = sqlite3.connect('inventario.db')
cursor = conn.cursor()

# Crear tabla de inventario
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_barra TEXT NOT NULL,
    nombre_producto TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    local TEXT NOT NULL
)
''')
conn.commit()

# Función para registrar un producto
def registrar_producto(codigo_barra, nombre_producto, fecha_vencimiento, cantidad, local):
    cursor.execute('''
    INSERT INTO inventario (codigo_barra, nombre_producto, fecha_vencimiento, cantidad, local)
    VALUES (?, ?, ?, ?, ?)
    ''', (codigo_barra, nombre_producto, fecha_vencimiento, cantidad, local))
    conn.commit()
    print(f"Producto '{nombre_producto}' registrado exitosamente.")

# Función para escanear código de barras
def escanear_codigo(imagen_path):
    imagen = cv2.imread(imagen_path)
    codigos = decode(imagen)
    for codigo in codigos:
        return codigo.data.decode('utf-8')
    return None

# Función para extraer fecha de vencimiento con OCR
def extraer_fecha_vencimiento(imagen_path):
    imagen = cv2.imread(imagen_path)
    texto = pytesseract.image_to_string(imagen)
    # Busca fechas en formato DD/MM/AAAA o similar
    fechas = re.findall(r'\d{2}/\d{2}/\d{4}', texto)
    return fechas[0] if fechas else None

# Procesar imágenes en una carpeta
def procesar_imagenes(carpeta_imagenes):
    extensiones_validas = ['.jpg', '.jpeg', '.png']
    carpeta_procesadas = os.path.join(carpeta_imagenes, 'procesadas')
    os.makedirs(carpeta_procesadas, exist_ok=True)

    for archivo in os.listdir(carpeta_imagenes):
        ruta_completa = os.path.join(carpeta_imagenes, archivo)
        if os.path.isfile(ruta_completa) and os.path.splitext(archivo)[1].lower() in extensiones_validas:
            print(f"Procesando imagen: {archivo}")
            codigo_barra = escanear_codigo(ruta_completa)
            fecha_vencimiento = extraer_fecha_vencimiento(ruta_completa)

            if codigo_barra and fecha_vencimiento:
                registrar_producto(codigo_barra, "Producto Desconocido", fecha_vencimiento, 1, "Local Desconocido")
            else:
                print(f"No se pudo extraer información completa de {archivo}")

            # Mover imagen procesada
            nueva_ruta = os.path.join(carpeta_procesadas, archivo)
            os.rename(ruta_completa, nueva_ruta)

# Función para generar alertas de vencimiento
def generar_alertas(dias=7):
    hoy = datetime.now()
    limite = hoy + timedelta(days=dias)
    cursor.execute('''
    SELECT * FROM inventario WHERE fecha_vencimiento <= ?
    ''', (limite.strftime('%Y-%m-%d'),))
    productos = cursor.fetchall()
    if productos:
        print("Productos próximos a vencer:")
        for prod in productos:
            print(f"{prod[2]} - Vence el {prod[3]} - Cantidad: {prod[4]} - Local: {prod[5]}")
    else:
        print("No hay productos próximos a vencer en los próximos días.")

# Función para exportar inventario a Excel
def exportar_inventario():
    cursor.execute('SELECT * FROM inventario')
    datos = cursor.fetchall()
    columnas = ['ID', 'Código de Barra', 'Nombre del Producto', 'Fecha de Vencimiento', 'Cantidad', 'Local']
    df = pd.DataFrame(datos, columns=columnas)
    df.to_excel('inventario.xlsx', index=False)
    print("Inventario exportado a 'inventario.xlsx'.")

# Ejemplo de uso
if __name__ == "__main__":
    carpeta_imagenes = 'imagenes'  # Carpeta donde se encuentran las imágenes a procesar
    procesar_imagenes(carpeta_imagenes)

    # Generar alertas de vencimiento
    generar_alertas()

    # Exportar inventario
    exportar_inventario()

# Cerrar conexión a la base de datos
conn.close()

