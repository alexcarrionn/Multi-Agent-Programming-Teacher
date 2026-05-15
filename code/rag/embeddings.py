from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings
import os

# Cache singleton: BAAI/bge-m3 pesa ~2 GB y tarda varios segundos en cargarse.
# Sin esto, cada create_retriever() reinstancia el modelo entero, y como el supervisor
# llama al retriever para verificar ambito y luego rag_node vuelve a crear otro, se
# cargaba dos veces por turno (visible en LangSmith como ~10-12s "perdidos" por nodo).
_embeddings_instance: HuggingFaceEmbeddings | None = None

# Función para obtener las embeddings utilizando el modelo BAAI/bge-m3, modelo recomendado para tareas de RAG de open source
#el embeddings nos va a servir para convertir el texto en vectores numéricos que puedan ser procesados
#por el modelo de lenguaje y el vectorstore (QDrant Cloud)
def get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is None:
        model_name = settings.EMBEDDING_MODEL
        encode_kwargs = {'normalize_embeddings': True}
        device = os.getenv("EMBEDDING_DEVICE", "cpu")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs=encode_kwargs
        )
    return _embeddings_instance