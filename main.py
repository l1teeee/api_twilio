from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
import anthropic

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
CORS(app)

# Configurar Claude (Anthropic)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
claude_client = None

if ANTHROPIC_API_KEY:
    try:
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        print("✅ Claude (Anthropic) configurado correctamente")
    except Exception as e:
        print(f"❌ Error configurando Claude: {e}")
        claude_client = None
else:
    print("⚠️ ANTHROPIC_API_KEY no encontrada")

# Configurar MongoDB Atlas
MONGODB_URI = os.getenv('MONGODB_URI')
try:
    client = MongoClient(MONGODB_URI)
    db = client['whatsapp_dashboard']
    mensajes_collection = db['mensajes']
    print("✅ Conexión a MongoDB Atlas exitosa")

    # Probar conexión
    client.admin.command('ping')
    print("✅ MongoDB Atlas respondiendo correctamente")

except Exception as e:
    print(f"❌ Error conectando a MongoDB Atlas: {e}")
    mensajes_collection = None


# Función para convertir ObjectId a string para JSON
def serializar_mensaje(mensaje):
    if '_id' in mensaje:
        mensaje['_id'] = str(mensaje['_id'])
    return mensaje


def analizar_mensaje_simple(texto_mensaje):
    """Análisis básico por palabras clave - fallback cuando IA no funciona"""
    texto = texto_mensaje.lower()

    # Palabras clave para sentimientos
    palabras_positivas = [
        'excelente', 'bueno', 'delicioso', 'rico', 'sabroso', 'rápido', 'limpio',
        'amable', 'recomiendo', 'genial', 'perfecto', 'increíble', 'fantástico',
        'me gusta', 'me encanta', 'amor', 'buenísimo', 'espectacular'
    ]

    palabras_negativas = [
        'malo', 'terrible', 'horrible', 'pésimo', 'frio', 'frío', 'lento',
        'sucio', 'caro', 'carísimo', 'disgusto', 'odio', 'asco', 'desagradable',
        'no me gusta', 'no me gustó', 'mal servicio', 'decepcionado'
    ]

    # Contar palabras positivas y negativas
    score_positivo = sum(1 for palabra in palabras_positivas if palabra in texto)
    score_negativo = sum(1 for palabra in palabras_negativas if palabra in texto)

    # Determinar sentimiento
    if score_positivo > score_negativo:
        sentimiento = 'positivo'
    elif score_negativo > score_positivo:
        sentimiento = 'negativo'
    else:
        sentimiento = 'neutro'

    # Determinar tema por palabras clave
    if any(word in texto for word in ['servicio', 'mesero', 'mesera', 'atención', 'personal', 'empleado']):
        tema = 'Servicio al Cliente'
    elif any(word in texto for word in
             ['comida', 'sabor', 'calidad', 'plato', 'ensalada', 'carne', 'pollo', 'rico', 'sabroso']):
        tema = 'Calidad del Producto'
    elif any(word in texto for word in ['precio', 'caro', 'barato', 'costo', 'dinero', 'pagar']):
        tema = 'Precio'
    elif any(word in texto for word in ['limpio', 'sucio', 'higiene', 'baño', 'mesa']):
        tema = 'Limpieza'
    else:
        tema = 'Otro'

    # Generar resumen basado en análisis
    if sentimiento == 'positivo':
        resumen = f'Cliente satisfecho con {tema.lower()}'
    elif sentimiento == 'negativo':
        resumen = f'Cliente insatisfecho con {tema.lower()}'
    else:
        resumen = f'Comentario neutral sobre {tema.lower()}'

    return {
        'sentimiento': sentimiento,
        'tema': tema,
        'resumen': resumen
    }


def analizar_mensaje_con_claude(texto_mensaje):
    """Analiza el sentimiento y tema de un mensaje usando Claude"""
    if not claude_client:
        print("❌ Claude no configurado, usando análisis simple")
        return analizar_mensaje_simple(texto_mensaje)

    try:
        prompt = f"""Analiza este mensaje de un cliente de restaurante/café y responde ÚNICAMENTE con un objeto JSON válido.

Mensaje del cliente: "{texto_mensaje}"

Debes responder SOLO con este formato JSON exacto:

{{
  "sentimiento": "positivo" | "negativo" | "neutro",
  "tema": "Servicio al Cliente" | "Calidad del Producto" | "Precio" | "Limpieza" | "Otro",
  "resumen": "Descripción breve del feedback (máximo 80 caracteres)"
}}

Criterios:
- sentimiento: "positivo" si satisfecho, "negativo" si insatisfecho, "neutro" si neutral
- tema: Clasifica en UNA de las 5 categorías exactas mostradas
- resumen: Descripción concisa del punto principal

Responde ÚNICAMENTE el JSON sin texto adicional:"""

        response = claude_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=150,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Obtener la respuesta
        resultado = response.content[0].text.strip()
        print(f"🔍 Respuesta de Claude: {resultado}")

        # Limpiar respuesta si tiene texto extra
        if '```json' in resultado:
            resultado = resultado.split('```json')[1].split('```')[0].strip()
        elif '```' in resultado:
            resultado = resultado.split('```')[1].split('```')[0].strip()

        # Buscar JSON en la respuesta
        import re
        json_match = re.search(r'\{.*?\}', resultado, re.DOTALL)
        if json_match:
            resultado = json_match.group()

        # Intentar parsear el JSON
        analisis = json.loads(resultado)

        # Validar que tenga los campos requeridos
        if all(key in analisis for key in ['sentimiento', 'tema', 'resumen']):
            print(f"✅ Claude analizó: {analisis['sentimiento']} - {analisis['tema']}")
            return analisis
        else:
            print(f"❌ Respuesta incompleta de Claude, usando análisis simple")
            return analizar_mensaje_simple(texto_mensaje)

    except Exception as e:
        print(f"❌ Error con Claude, usando análisis simple: {e}")
        return analizar_mensaje_simple(texto_mensaje)


def inicializar_datos_prueba():
    """Verificar conexión a MongoDB sin insertar datos de prueba"""
    if mensajes_collection is None:
        print("❌ MongoDB no disponible")
        return

    # Solo mostrar cuántos mensajes hay
    total_mensajes = mensajes_collection.count_documents({})
    print(f"✅ {total_mensajes} mensajes existentes en MongoDB")


@app.route('/')
def home():
    total_mensajes = 0
    if mensajes_collection is not None:
        total_mensajes = mensajes_collection.count_documents({})

    return f"""
    <h1>🚀 WhatsApp Dashboard Backend</h1>
    <p>✅ Servidor funcionando correctamente!</p>
    <p>📱 Webhook disponible en: <code>/webhook</code></p>
    <p>📊 API disponible en: <code>/api/mensajes</code></p>
    <p>💾 Mensajes en MongoDB: <strong>{total_mensajes}</strong></p>
    <p>🔗 Estado MongoDB: <strong>{'Conectado' if mensajes_collection is not None else 'Desconectado'}</strong></p>
    <p>🤖 Estado IA: <strong>{'Claude Activo' if claude_client else 'IA Desactivada'}</strong></p>
    """


@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint que recibe mensajes de WhatsApp via Twilio"""
    try:
        # Obtener datos del mensaje de Twilio
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        body = request.form.get('Body')

        print(f"📱 Mensaje recibido de {from_number}: {body}")

        # Crear documento base del mensaje para MongoDB
        mensaje = {
            'texto_mensaje': body,
            'numero_remitente': from_number,
            'numero_destino': to_number,
            'timestamp': datetime.now().isoformat(),
            'sentimiento': 'neutro',  # Valor por defecto
            'tema': 'Otro',  # Valor por defecto
            'resumen': 'Mensaje pendiente de análisis'  # Valor por defecto
        }

        # Analizar con Claude
        print("🤖 Analizando mensaje con IA...")
        analisis_ia = analizar_mensaje_con_claude(body)

        if analisis_ia:
            # Actualizar con los resultados de la IA
            mensaje['sentimiento'] = analisis_ia['sentimiento']
            mensaje['tema'] = analisis_ia['tema']
            mensaje['resumen'] = analisis_ia['resumen']
            print(f"✅ IA completó análisis: {analisis_ia['sentimiento']} - {analisis_ia['tema']}")
        else:
            print("⚠️ IA no disponible, usando valores por defecto")

        # Guardar en MongoDB
        if mensajes_collection is not None:
            try:
                result = mensajes_collection.insert_one(mensaje)
                print(f"✅ Mensaje guardado en MongoDB con ID: {result.inserted_id}")
                total = mensajes_collection.count_documents({})
                print(f"📊 Total mensajes en base de datos: {total}")
            except Exception as e:
                print(f"❌ Error guardando en MongoDB: {e}")
        else:
            print("❌ MongoDB no disponible, mensaje no guardado")

        return "OK", 200

    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        return "Error", 500


@app.route('/api/mensajes', methods=['GET'])
def get_mensajes():
    """Endpoint para que el frontend obtenga todos los mensajes"""
    if mensajes_collection is None:
        return jsonify({'error': 'MongoDB no disponible', 'mensajes': []})

    try:
        # Obtener todos los mensajes, ordenados por timestamp (más recientes primero)
        mensajes = list(mensajes_collection.find().sort('timestamp', -1))

        # Convertir ObjectId a string para JSON
        mensajes_serializados = [serializar_mensaje(msg) for msg in mensajes]

        return jsonify({
            'total': len(mensajes_serializados),
            'mensajes': mensajes_serializados
        })

    except Exception as e:
        print(f"❌ Error obteniendo mensajes: {e}")
        return jsonify({'error': str(e), 'mensajes': []})


@app.route('/api/sentimientos', methods=['GET'])
def get_sentimientos():
    """Endpoint para obtener estadísticas de sentimientos"""
    if mensajes_collection is None:
        return jsonify({'positivo': 0, 'negativo': 0, 'neutro': 0})

    try:
        pipeline = [
            {
                '$group': {
                    '_id': '$sentimiento',
                    'count': {'$sum': 1}
                }
            }
        ]

        result = list(mensajes_collection.aggregate(pipeline))

        stats = {'positivo': 0, 'negativo': 0, 'neutro': 0}
        for item in result:
            sentimiento = item['_id']
            if sentimiento in stats:
                stats[sentimiento] = item['count']

        return jsonify(stats)

    except Exception as e:
        print(f"❌ Error obteniendo estadísticas de sentimientos: {e}")
        return jsonify({'positivo': 0, 'negativo': 0, 'neutro': 0})


@app.route('/api/temas', methods=['GET'])
def get_temas():
    """Endpoint para obtener estadísticas de temas"""
    if mensajes_collection is None:
        return jsonify({})

    try:
        pipeline = [
            {
                '$group': {
                    '_id': '$tema',
                    'count': {'$sum': 1}
                }
            }
        ]

        result = list(mensajes_collection.aggregate(pipeline))

        temas = {}
        for item in result:
            tema = item['_id']
            temas[tema] = item['count']

        return jsonify(temas)

    except Exception as e:
        print(f"❌ Error obteniendo estadísticas de temas: {e}")
        return jsonify({})


@app.route('/test', methods=['POST', 'GET'])
def test_endpoint():
    """Endpoint de prueba para verificar que funciona"""
    if request.method == 'POST':
        data = request.get_json()
        print(f"📋 Test data recibida: {data}")
        return jsonify({"status": "success", "received": data})
    else:
        total_mensajes = 0
        if mensajes_collection is not None:
            total_mensajes = mensajes_collection.count_documents({})

        return jsonify({
            "status": "success",
            "message": "Servidor funcionando correctamente",
            "total_mensajes": total_mensajes,
            "mongodb_status": "connected" if mensajes_collection is not None else "disconnected",
            "claude_status": "active" if claude_client else "inactive"
        })


if __name__ == '__main__':
    print("🚀 Iniciando WhatsApp Dashboard Backend...")
    print("📱 Webhook disponible en: http://localhost:5000/webhook")
    print("📊 API mensajes en: http://localhost:5000/api/mensajes")
    print("🔗 Dashboard en: http://localhost:5000")
    print(f"🤖 IA: {'Claude Activo' if claude_client else 'Análisis Simple Activo'}")

    # Cargar datos de prueba si es necesario
    inicializar_datos_prueba()

    # Ejecutar en modo debug para desarrollo
    app.run(debug=True, host='0.0.0.0', port=5000)