from config.settings import settings
from langchain_qdrant import QdrantVectorStore
from rag.qDrantClient import client
from rag.embeddings import get_embeddings

#le hemos añadido el collection_name para poder crear diferentes colecciones en QDRant cloud para las diferentes asignaturas.
def create_retriever(top_k: int = 5, collection_name: str = None):

        embeddings_open_source = get_embeddings()

        # el vectorstore es una abstracción que nos permite interactuar con QDrant Cloud de manera más sencilla, 
        #utilizando el modelo de embeddings que hemos definido previamente (BAAI/bge-m3)
        vectorstore = QdrantVectorStore(
            client=client,
            embedding=embeddings_open_source,
            collection_name= collection_name or settings.QDRANT_COLLECTION
        )
        # creamos el retriever
        return vectorstore.as_retriever(search_kwargs={"k": top_k})
