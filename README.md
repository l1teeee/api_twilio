# WhatsApp Dashboard - Análisis de Sentimientos en Tiempo Real

Sistema completo de análisis de feedback de clientes que recibe mensajes vía WhatsApp, los analiza automáticamente con IA, y visualiza insights de negocio en tiempo real.

## Descripción

Dashboard interactivo que permite a negocios locales (restaurantes, cafés, etc.) recolectar feedback de clientes através de WhatsApp y convertirlo automáticamente en inteligencia de negocio accionable mediante análisis de sentimientos con IA.

## Características

- Recepción automática de mensajes vía WhatsApp usando Twilio
- Análisis de sentimientos con IA (Claude/Anthropic)
- Clasificación por temas (Servicio, Calidad, Precio, Limpieza)
- Almacenamiento persistente en MongoDB Atlas
- API REST para integración con frontend
- Sistema de fallback para análisis cuando IA no está disponible

## Stack Tecnológico para Desarrollo

### Backend
- **Python 3.11+** - Lenguaje principal
- **Flask** - Framework web minimalista para prototipado rápido
- **MongoDB Atlas** - Base de datos NoSQL en la nube (desarrollo)
- **Twilio API** - Integración con WhatsApp (sandbox para desarrollo)
- **Claude (Anthropic)** - Modelo de lenguaje para análisis
- **ngrok** - Túnel HTTP para desarrollo local

### Entorno de Desarrollo
- **PyCharm** - IDE principal de desarrollo
- **python-dotenv** - Gestión de variables de entorno para desarrollo
- **flask-cors** - Manejo de CORS para desarrollo del frontend

## Instalación para Desarrollo

### Prerrequisitos
- Python 3.11 o superior
- PyCharm (recomendado)
- Cuenta de Twilio (plan gratuito)
- Cuenta de MongoDB Atlas (tier gratuito)
- Cuenta de Anthropic para Claude API
- ngrok instalado

### Configuración del Entorno de Desarrollo

```bash
# Navegar al directorio del proyecto
cd api-twilio

# Crear entorno virtual en PyCharm
# File → Settings → Project → Python Interpreter → Add Interpreter → Virtualenv Environment → New

# O desde terminal:
python -m venv venv

# Activar entorno virtual (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install flask flask-cors python-dotenv twilio pymongo anthropic
```

### Variables de Entorno para Desarrollo

Crear archivo `.env` en la raíz del proyecto `api-twilio/`:

```env
# Twilio (Sandbox para desarrollo)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+14155238886

# Tu número personal de desarrollo
YOUR_PHONE_NUMBER=+503xxxxxxxx

# MongoDB Atlas (cluster gratuito)
MONGODB_URI=mongodb+srv://usuario:password@cluster0.xxxxx.mongodb.net/whatsapp_dashboard?retryWrites=true&w=majority

# Claude API (créditos de desarrollo)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxx
```

### Configuración de Servicios para Desarrollo

#### Twilio WhatsApp Sandbox (Desarrollo)
1. Console de Twilio → Messaging → Settings → WhatsApp Sandbox
2. Obtener número de sandbox y código de activación
3. Activar tu número personal para pruebas
4. Configurar webhook (después del paso de ngrok)

#### MongoDB Atlas (Desarrollo)
1. Crear cluster gratuito M0
2. Network Access → Add IP → Allow Access from Anywhere (0.0.0.0/0)
3. Database Access → Add User para desarrollo
4. Connect → Choose connection method → Connect your application

#### Claude API (Desarrollo)
1. Anthropic Console → API Keys
2. Create Key para desarrollo
3. Agregar créditos mínimos para testing

### Ejecutar en Modo Desarrollo

#### 1. Iniciar el Servidor Flask
```bash
# Desde PyCharm: Click derecho en main.py → Run
# O desde terminal:
cd api-twilio
python main.py
```

Salida esperada:
```
✅ Claude (Anthropic) configurado correctamente
✅ Conexión a MongoDB Atlas exitosa
🚀 Iniciando WhatsApp Dashboard Backend...
📱 Webhook disponible en: http://localhost:5000/webhook
* Debug mode: on
```

#### 2. Exponer Servidor con ngrok (Desarrollo)
```bash
# En terminal separado
ngrok http 5000
```

Copiar URL generada (ej: `https://abc123.ngrok.io`)

#### 3. Configurar Webhook en Twilio
- Twilio Sandbox Settings
- "When a message comes in": `https://abc123.ngrok.io/webhook`
- Method: POST
- Save Configuration

## Estructura del Proyecto de Desarrollo

```
api-twilio/
├── main.py              # Aplicación Flask principal
├── .env                 # Variables de entorno (desarrollo)
├── .env.example         # Plantilla para otros desarrolladores
├── requirements.txt     # Dependencias del proyecto
├── venv/               # Entorno virtual (no commitear)
└── .gitignore          # Archivos ignorados
```

## Flujo de Desarrollo

### Testing Manual
1. **Enviar mensaje** a número de Twilio desde WhatsApp
2. **Verificar consola** Flask para logs de procesamiento
3. **Comprobar MongoDB** Atlas para datos guardados
4. **Probar APIs** en `http://localhost:5000/api/mensajes`

### Endpoints para Desarrollo
- `GET /` - Estado del servidor y configuración
- `POST /webhook` - Recibe mensajes (usado por Twilio)
- `GET /api/mensajes` - Obtener todos los mensajes
- `GET /api/sentimientos` - Estadísticas de sentimientos  
- `GET /api/temas` - Estadísticas por tema
- `GET /test` - Endpoint de testing

## Decisiones Técnicas para Desarrollo Rápido

### Flask vs Django
**Decisión: Flask**
- Configuración mínima para MVP
- Ideal para APIs simples durante desarrollo
- Hot reloading automático en modo debug
- Menos boilerplate para prototipado

### MongoDB vs SQL
**Decisión: MongoDB Atlas**
- Schema flexible para iteración rápida
- JSON nativo (fácil debugging)
- Atlas elimina configuración de infraestructura
- Tier gratuito suficiente para desarrollo

### Claude vs OpenAI
**Decisión: Claude (Anthropic)**  
- Mejor manejo de español en contexto de restaurantes
- Respuestas JSON más consistentes en desarrollo
- API más simple para integrar
- Créditos iniciales incluidos

### ngrok vs Deploy
**Decisión: ngrok para desarrollo**
- Setup instantáneo sin configuración de servers
- Perfecto para testing con webhooks
- Fácil compartir endpoints durante desarrollo
- No requiere infraestructura

## Ingeniería de Prompts para Desarrollo

### Estrategia Iterativa
El prompt se desarrolló con enfoque en **consistencia y debugging**:

#### Versión 1 (Simple)
```
"Analiza el sentimiento de: [mensaje]"
```
**Problema:** Respuestas inconsistentes

#### Versión 2 (Estructurada)  
```
"Analiza y responde con JSON: {sentimiento: X, tema: Y}"
```
**Problema:** Temas variables, JSON malformado

#### Versión 3 (Actual - Optimizada para desarrollo)
```python
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
```

### Técnicas de Robustez para Desarrollo
- **Parsing defensivo** con regex para extraer JSON
- **Validación de campos** obligatorios
- **Sistema de fallback** con análisis por palabras clave
- **Logging detallado** para debugging

## Debugging y Troubleshooting

### Problemas Comunes en Desarrollo

**ngrok se desconecta:**
```bash
# Reiniciar ngrok
ngrok http 5000
# Actualizar URL en Twilio
```

**MongoDB no conecta:**
```bash
# Verificar en MongoDB Atlas:
# 1. IP whitelist (0.0.0.0/0)
# 2. Usuario y contraseña correctos
# 3. Connection string actualizado
```

**Claude API falla:**
```bash
# Verificar en consola:
❌ Error con Claude, usando análisis simple
# Sistema automáticamente usa fallback
```

**Mensajes no llegan:**
```bash
# Verificar:
# 1. ngrok corriendo
# 2. Webhook URL correcta en Twilio  
# 3. Número activado en sandbox
```

### Logging para Desarrollo
El sistema incluye logging detallado:
```python
print(f"📱 Mensaje recibido de {from_number}: {body}")
print(f"🤖 Analizando mensaje con IA...")
print(f"✅ Claude analizó: {analisis['sentimiento']} - {analisis['tema']}")
```

## Limitaciones de Desarrollo

- **Sandbox WhatsApp:** Solo números pre-aprobados
- **ngrok gratuito:** URL cambia al reiniciar
- **Claude credits:** Consumo por request de desarrollo
- **MongoDB Atlas:** Límites de tier gratuito

## Siguientes Pasos de Desarrollo

1. **Frontend React** con hot reloading
2. **Testing automatizado** con pytest
3. **Docker** para environment consistency  
4. **CI/CD** para deployment automático
5. **Monitoring** con logs estructurados

## Configuración de PyCharm

### Configuración Recomendada
1. **Python Interpreter:** Usar el venv del proyecto
2. **Run Configuration:** main.py con working directory correcto
3. **Environment Variables:** Cargar desde .env
4. **Debugger:** Breakpoints en webhook() para debugging

## Seguridad

- **Variables de entorno** para todas las credenciales
- **API keys** no hardcodeadas en el código
- **CORS configurado** correctamente
- **Validación de entrada** en todos los endpoints
- **Manejo seguro** de errores sin exposición de detalles

## Limitaciones Actuales

- **Sandbox de WhatsApp** - Solo números pre-aprobados
- **ngrok gratuito** - URL cambia en cada reinicio
- **Análisis en español** - Optimizado para español, funcionalidad limitada en otros idiomas

## Próximos Pasos

1. **Frontend React** con gráficos interactivos
2. **WhatsApp Business API** para producción
3. **Análisis de tendencias** temporales
4. **Alertas automáticas** por sentimientos negativos
5. **Dashboard administrativo** con configuraciones

## Soporte

Para problemas o consultas, verificar:
1. **Logs del servidor** para errores específicos
2. **Estado de servicios** externos (Twilio, MongoDB, Anthropic)
3. **Configuración de ngrok** y webhooks
4. **Variables de entorno** correctamente configuradas
