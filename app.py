from flask import Flask, render_template, request, send_file, jsonify
import os
import cv2
import uuid
import threading
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def borrar_archivo_automatico(ruta, delay=300):
    time.sleep(delay)
    if os.path.exists(ruta):
        os.remove(ruta)

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
    
    # MOTOR DE MEJORA VISUAL (RÁPIDO Y EFICIENTE)
    img = cv2.imread(ruta_original)
    if img is None:
        return jsonify({'error': 'Imagen inválida'}), 400
        
    # 1. Quitar ruido manteniendo bordes
    img_filtrada = cv2.bilateralFilter(img, 7, 65, 65)
    # 2. Aumentar nitidez enfocando detalles
    img_borrosa = cv2.GaussianBlur(img_filtrada, (0, 0), 2)
    resultado = cv2.addWeighted(img_filtrada, 1.4, img_borrosa, -0.4, 0)
    
    cv2.imwrite(ruta_mejorada, resultado)

    threading.Thread(target=borrar_archivo_automatico, args=(ruta_original,)).start()
    threading.Thread(target=borrar_archivo_automatico, args=(ruta_mejorada,)).start()

    return jsonify({'descarga_url': f'/descargar/{id_unico}_mejorada.jpg'})

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)