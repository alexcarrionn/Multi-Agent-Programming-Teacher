#Esta clase se encarga de almacenar las configuraciones del proyecto, como la base de datos, el puerto, etc.
from dotenv import load_dotenv
import os 

load_dotenv()

class Settings:
    # -- Configuraciones de la base de datos MySQL --

    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB = os.getenv("MYSQL_DB")

        # -- Configuracion del LLM --
    LLM_MODEL = os.getenv("LLM_MODEL")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_URL = os.getenv("LLM_URL")

    if not LLM_MODEL:
        raise ValueError("LLM_MODEL no está definido.")

    if LLM_MODEL.startswith("gpt") and (not LLM_API_KEY or not LLM_URL):
        raise ValueError("LLM_API_KEY o LLM_URL no están definidos para GPT.")

    if LLM_MODEL.startswith("gemini") and not LLM_API_KEY:
        raise ValueError("LLM_API_KEY no está definido para Gemini.")
    
    #Para groq 
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # -- Configuracion de QDRANT --
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

    # Umbral de relevancia (coseno, 0..1) para el retriever. Chunks por debajo se
    # descartan: asi el "portero" de ambito bloquea preguntas fuera del material.
    # Calibrar sin rebuild cambiando solo el .env. Subir si se cuela off-topic,
    # bajar si preguntas legitimas devuelven "no tengo informacion".
    RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.5"))

    # -- Configuracion de la aplicacion --

    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    #-- Configuracion de embeddings --
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

    #-- Configuracion del Frontend --
    JWT_SECRET_KEY = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION")) # Expiración en minutos

    # Brevo SMTP
    BREVO_SMTP_HOST = os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com")
    BREVO_SMTP_PORT = int(os.getenv("BREVO_SMTP_PORT", "587"))
    BREVO_SMTP_LOGIN = os.getenv("BREVO_SMTP_LOGIN")
    BREVO_SMTP_KEY = os.getenv("BREVO_SMTP_KEY")
    BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")   # email verificado en Brevo
    BREVO_SENDER_NAME  = os.getenv("BREVO_SENDER_NAME", "Codi")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # -- CORS --
    # Origenes permitidos (lista separada por comas). Por defecto el FRONTEND_URL
    # (dominio de produccion) mas localhost para desarrollo. Calibrable desde .env
    # sin tocar codigo: en produccion poner p.ej. "https://tudominio.com".
    CORS_ALLOWED_ORIGINS = list(dict.fromkeys(
        o.strip()
        for o in os.getenv(
            "CORS_ALLOWED_ORIGINS", f"{FRONTEND_URL},http://localhost:3000"
        ).split(",")
        if o.strip()
    ))

    # -- Rate limiting (slowapi) --
    # Backend de almacenamiento de los contadores. "memory://" es correcto con un
    # solo proceso uvicorn (caso actual). Si algun dia se arranca con --workers o
    # varias replicas, cada proceso tendria su propio contador: cambiar a Redis con
    # "redis://host:6379" SIN tocar codigo, solo el .env.
    RATE_LIMIT_STORAGE = os.getenv("RATE_LIMIT_STORAGE", "memory://")
    # Activar/desactivar globalmente el rate limiting (util en tests/dev).
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    # Formato de "limits": "5/minute", "100/minute", "20/hour". Varios limites a la
    # vez se separan con ";" (ej. "5/minute;20/hour"). Calibrable sin rebuild.
    # Red de seguridad global aplicada a TODAS las rutas (por usuario-o-IP).
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
    # Endpoints sensibles a fuerza bruta / enumeracion / spam de correo.
    RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute;20/hour")
    # Chat: cada peticion dispara el grafo multi-agente (coste real en tokens LLM).
    RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "20/minute")
    # Subidas de ficheros / formularios de escritura pesados.
    RATE_LIMIT_UPLOAD = os.getenv("RATE_LIMIT_UPLOAD", "20/minute")

    # -- Limites de validacion de entrada --
    # Longitud maxima de un mensaje de chat (evita payloads enormes -> coste LLM).
    MAX_CHAT_MESSAGE_CHARS = int(os.getenv("MAX_CHAT_MESSAGE_CHARS", "4000"))
    # Tamaño maximo del Excel de alumnos autorizados (bytes). 10 MB por defecto.
    MAX_EXCEL_BYTES = int(os.getenv("MAX_EXCEL_BYTES", str(10 * 1024 * 1024)))
    # Numero maximo de filas que se procesan del Excel.
    MAX_EXCEL_ROWS = int(os.getenv("MAX_EXCEL_ROWS", "5000"))
    # Tamaño maximo por documento subido al RAG (bytes). Alineado con nginx (50 MB).
    MAX_DOC_BYTES = int(os.getenv("MAX_DOC_BYTES", str(50 * 1024 * 1024)))

settings = Settings()