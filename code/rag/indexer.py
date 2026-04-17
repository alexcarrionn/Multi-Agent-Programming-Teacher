from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_qdrant import QdrantVectorStore
from rag.qDrantClient import client
from qdrant_client.models import FieldCondition, Filter, MatchValue, PayloadSchemaType
from rag.embeddings import get_embeddings
from config.settings import settings

# Función para indexar documentos utilizando el modelo BAAI/bge-m3 y almacenarlos en QDrant Cloud
def index_documents(text: str, source_id: str = "default", content_hash: str | None = None, replace_existing_source: bool = True, file_path: str = ""):
    # Obtener las embeddings utilizando el modelo BAAI/bge-m3
    embeddings_open_source = get_embeddings()

    # Configura el SemanticChuncker con el nuevo modelo
    semantic_chunker = SemanticChunker(
        embeddings_open_source, 
        breakpoint_threshold_type="percentile"
    )

    # Crear los fragmentos semánticos
    semantic_chunks = semantic_chunker.create_documents([text])

    #si el semantic chunk no se ha podido crear, se hace un chunking tradicional utilizando el RecursiveCharacterTextSplitter.
    if not semantic_chunks:
        #Se parte en fragmentos la documentacion
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        semantic_chunks = text_splitter.create_documents([text])
    #aqui añadimos metadatos a los fragmentos semánticos
    for index, chunk in enumerate(semantic_chunks):
        chunk.metadata["source_id"] = source_id
        if content_hash is not None:
            chunk.metadata["content_hash"] = content_hash
        chunk.metadata["chunk_index"] = index
        chunk.metadata["file_path"] = str(file_path)

    #vamos a comprobar si la coleccion existe
    collection_exists = client.collection_exists(settings.QDRANT_COLLECTION)

    # Aseguramos que el índice de payload exista antes de cualquier operación de filtrado
    if collection_exists:
        try:
            client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION,
                field_name="metadata.source_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass  # El índice ya existe

        try:
            client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION,
                field_name="metadata.content_hash",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass  # El índice ya existe

    #si la coleccion existe y tenemos que reemplazarla, eliminamos los puntos que correspondan a la fuente que estamos indexando
    if collection_exists and replace_existing_source:
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.source_id",
                        match=MatchValue(value=source_id),
                    )
                ]
            ),
        )
    # creamos el vectorstore (QDrant Cloud) con el modelo open source
    #si la coleccion no existe la creamos y añadimos los documentos
    if not collection_exists:
        # Crea la colección y añade los primeros documentos
        QdrantVectorStore.from_documents(
            documents=semantic_chunks,
            embedding=embeddings_open_source,
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            collection_name=settings.QDRANT_COLLECTION,
        )
        # Creamos un índice en el campo metadata.source_id para poder filtrar por source_id
        client.create_payload_index(
            collection_name=settings.QDRANT_COLLECTION,
            field_name="metadata.source_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        return 
    
    else:
     # Si ya existe, simplemente usamos el vectorstore para añadir más
        vectorstore = QdrantVectorStore(
            client=client,
            collection_name=settings.QDRANT_COLLECTION,
            embedding=embeddings_open_source,
        )
        vectorstore.add_documents(semantic_chunks)

