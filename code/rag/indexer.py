from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchian_experimental.text_splitter import SemanticChuncker
from langchain_comunity.vectorstores import QdrantVectorStore
from qdrant_client import QdrantClient
from rag.embeddings import get_embeddings
from config.settings import settings

# Función para indexar documentos utilizando el modelo BAAI/bge-m3 y almacenarlos en QDrant Cloud
def index_documents(text: str):
    # Obtener las embeddings utilizando el modelo BAAI/bge-m3
    embeddings_open_source = get_embeddings()

    # Configura el SemanticChuncker con el nuevo modelo
    semantic_chunker = SemanticChunker(
        embeddings_open_source, 
        breakpoint_threshold_type="percentile"
    )

    # Crear los fragmentos semánticos
    semantic_chunks = semantic_chunker.create_documents(texts)

    # cliente para QDrant Cloud
    client = QdrantClient(
        url = settings.QDRANT_URL, 
        api_key=settings.QDRANT_API_KEY,
    )

    # creamos el vectorstore (QDrant Cloud) con el modelo open source

    QdrantVectorStore.from_documents(
        semantic_chunks, 
        embedding=embeddings_open_source, 
        client=client,
        collection_name=settings.QDRANT_COLLECTION
    )
