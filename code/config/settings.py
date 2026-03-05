#Esta clase se encarga de almacenar las configuraciones del proyecto, como la base de datos, el puerto, etc.
from dotenv import load_dotenv
import os 

load_dotenv()

class Settings:
    # -- Configuraciones de la base de datos MySQL --

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB = os.getenv("MYSQL_DB", "agentes_db")

    # -- Configuracion del LLM --
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_API_KEY = os.getenv("LLM_API_KEY")

    # -- Configuracion de QDRANT --
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "ip_documents")

    # -- Configuracion de la aplicacion --

    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    #-- Configuracion de embeddings --
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

settings = Settings()