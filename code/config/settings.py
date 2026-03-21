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

    # -- Configuracion de la aplicacion --

    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    #-- Configuracion de embeddings --
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

    #-- Configuracion del Frontend --
    JWT_SECRET_KEY = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION")) # Expiración en minutos

settings = Settings()