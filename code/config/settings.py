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
    if os.getenv("LLM_MODEL") is None:
        raise ValueError("LLM_MODEL no está definido en las variables de entorno.")
    elif os.getenv("LLM_MODEL").startswith("gpt") and (os.getenv("LLM_API_KEY") is None or os.getenv("LLM_URL") is None):
        raise ValueError("LLM_API_KEY o LLM_URL no están definidos en las variables de entorno para el modelo gpt-oss.")
    elif os.getenv("LLM_MODEL").startswith("gemini") and os.getenv("LLM_API_KEY") is None:
        raise ValueError("LLM_API_KEY no está definido en las variables de entorno para el modelo gemini.")
    elif os.getenv("LLM_MODEL").startswith("gpt"):
        LLM_MODEL = os.getenv("LLM_MODEL")
        LLM_API_KEY = os.getenv("LLM_API_KEY")
        LLM_URL = os.getenv("LLM_URL")
    elif os.getenv("LLM_MODEL").startswith("gemini"):
        LLM_MODEL = os.getenv("LLM_MODEL")
        LLM_API_KEY = os.getenv("LLM_API_KEY")
    
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

settings = Settings()