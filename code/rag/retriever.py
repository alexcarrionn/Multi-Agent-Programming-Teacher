from config.settings import settings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from rag.embeddings import get_embeddings

def create_retriever(top_k: int = 5):

        embeddings_open_source = get_embeddings()

        #definimos el cliente de QDrant Cloud y el vectorstore para crear el retriever
        client = QdrantClient(
            url = settings.QDRANT_URL, 
            api_key=settings.QDRANT_API_KEY,
        )

        # el vectorstore es una abstracción que nos permite interactuar con QDrant Cloud de manera más sencilla, 
        #utilizando el modelo de embeddings que hemos definido previamente (BAAI/bge-m3)
        vectorstore = QdrantVectorStore(
            client=client,
            embedding=embeddings_open_source,
            collection_name=settings.QDRANT_COLLECTION
        )
        # creamos el retriever
        return vectorstore.as_retriever(search_kwargs={"k": top_k})
