from config.settings import settings
from langchain_qdrant import QdrantVectorStore
from rag.qDrantClient import client
from rag.embeddings import get_embeddings

#le hemos añadido el collection_name para poder crear diferentes colecciones en QDRant cloud para las diferentes asignaturas.
#top_k=2 (antes 5): con 5 chunks el contexto sumaba ~1800 tokens y, junto con el system prompt.
def create_retriever(top_k: int = 2, collection_name: str = None):

        embeddings_open_source = get_embeddings()

        # el vectorstore es una abstracción que nos permite interactuar con QDrant Cloud de manera más sencilla, 
        #utilizando el modelo de embeddings que hemos definido previamente (BAAI/bge-m3)
        vectorstore = QdrantVectorStore(
            client=client,
            embedding=embeddings_open_source,
            collection_name= collection_name or settings.QDRANT_COLLECTION
        )
        # creamos el retriever. El umbral se lee de settings (.env: RAG_SCORE_THRESHOLD)
        # para poder calibrarlo sin rebuild del contenedor.
        return vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": top_k, "score_threshold": settings.RAG_SCORE_THRESHOLD},
        )
