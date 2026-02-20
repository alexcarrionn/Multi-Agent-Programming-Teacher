from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings
import os

# Función para obtener las embeddings utilizando el modelo BAAI/bge-m3, modelo recomendado para tareas de RAG de open source
#el embeddings nos va a servir para convertir el texto en vectores numéricos que puedan ser procesados 
#por el modelo de lenguaje y el vectorstore (QDrant Cloud)
def get_embeddings():
    model_name = "BAAI/bge-m3"
    encode_kwargs = {'normalize_embeddings': True} 
    device = os.getenv("EMBEDDING_DEVICE", "cpu")
    embeddings_open_source = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': device}, 
        encode_kwargs=encode_kwargs
    )
    return embeddings_open_source