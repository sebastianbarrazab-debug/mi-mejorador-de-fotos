from flask import Flask, render_template, request, send_file, jsonify
import os
import cv2
import numpy as np
import uuid
import threading
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def borrar_archivo_automatico(ruta, delay=300):
    time.sleep(delay)
    if os.path.exists(ruta):
        try:
            os.remove(ruta)
        except:
            pass

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/procesar', methods=['POST'])
def procesar():
    if 'foto' not in request.files:
        return jsonify({'error': 'No hay archivo'}), 400
    
    archivo = request.files['foto']
    id_unico = str(uuid.uuid4())
    
    ruta_original = os.path.join(UPLOAD_FOLDER, f"{id_unico}_origen.jpg")
    ruta_mejorada = os.path.join(UPLOAD_FOLDER, f"{id_unico}_mejorada.jpg")
    archivo.save(ruta_original)
    
    # 1. Leer la imagen original
    img = cv2.imread(ruta_original)
    if img is None:
        return jsonify({'error': 'Imagen inválida'}), 400
        
    try:
        # OPTIMIZACIÓN RENDERS: Si la imagen es gigantesca (> 2000px), redimensionarla antes para evitar error de memoria RAM
        alto, ancho = img.shape[:2]
        if max(alto, ancho) > 2500:
            escala = 2500 / max(alto, ancho)
            img = cv2.resize(img, (int(ancho * escala), int(alto * escala)), interpolation=cv2.INTER_AREA)
            alto, ancho = img.shape[:2]

        # 2. Duplicar píxeles con interpolación Lanczos4
        img_gigante = cv2.resize(img, (ancho * 2, alto * 2), interpolation=cv2.INTER_LANCZOS4)
        
        # 3. Filtro de reducción de ruido
        img_suave = cv2.GaussianBlur(img_gigante, (3, 3), 0)
        
        # 4. Enfoque digital avanzado (Máscara de nitidez)
        resultado = cv2.addWeighted(img_gigante, 1.6, img_suave, -0.6, 0)
        
        # Guardar resultado final
        cv2.imwrite(ruta_mejorada, resultado)
    except Exception as e:
        print(f"Error al procesar: {e}")
        return jsonify({'error': 'Fallo al optimizar la imagen'}), 500

    # Eliminar archivos en segundo plano pasado un tiempo
    threading.Thread(target=borrar_archivo_automatico, args=(ruta_original,)).start()
    threading.Thread(target=borrar_archivo_automatico, args=(ruta_mejorada,)).start()

    return jsonify({'descarga_url': f'/descargar/{id_unico}_mejorada.jpg'})

@app.route('/descargar/<filename>')
def descargar(filename):
    ruta_archivo = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(ruta_archivo):
        return send_file(ruta_archivo, as_attachment=True)
    return "El archivo ya expiró o no existe.", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
