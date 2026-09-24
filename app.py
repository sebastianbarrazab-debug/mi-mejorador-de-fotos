from flask import Flask, render_template, request, send_file, jsonify
import os
import cv2
import uuid
import threading
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CONFIGURACIÓN INTERNA DE LA INTELIGENCIA ARTIFICIAL (ESPCN)
modelo_ruta = "ESPCN_x2.pb"
sr = cv2.dnn_superres.SuperResolutionInference_create()
sr.readModel(modelo_ruta)
sr.setModel("espcn", 2) # Duplica los píxeles de forma inteligente (2x)

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
    
    # 1. Leer la imagen que subió el usuario
    img = cv2.imread(ruta_original)
    if img is None:
        return jsonify({'error': 'Imagen inválida'}), 400
        
    try:
        # 2. PROCESAMIENTO CON INTELIGENCIA ARTIFICIAL
        # La IA analiza, estira e inventa los píxeles faltantes
        img_ia = sr.upsample(img)
        
        # 3. FILTRO DE ENFOQUE FINAL (Para compactar y limpiar bordes)
        img_borrosa = cv2.GaussianBlur(img_ia, (0, 0), 1)
        resultado = cv2.addWeighted(img_ia, 1.3, img_borrosa, -0.3, 0)
        
        # Guardar resultado en HD
        cv2.imwrite(ruta_mejorada, resultado)
    except Exception as e:
        print(f"Error en IA: {e}")
        return jsonify({'error': 'Fallo al procesar con IA'}), 500

    threading.Thread(target=borrar_archivo_automatico, args=(ruta_original,)).start()
    threading.Thread(target=borrar_archivo_automatico, args=(ruta_mejorada,)).start()

    return jsonify({'descarga_url': f'/descargar/{id_unico}_mejorada.jpg'})

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
