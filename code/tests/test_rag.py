"""
Test independiente para verificar el flujo RAG completo:
embeddings -> indexación -> retrieval.
Ejecutar desde la carpeta code/:
    python -m tests.test_rag
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings


SAMPLE_TEXT = """
Python es un lenguaje de programación multiparadigma creado por Guido van Rossum.
Soporta programación orientada a objetos, programación funcional y scripting.
Es ampliamente utilizado en inteligencia artificial, desarrollo web y automatización.
Su sintaxis es clara y legible, lo que lo hace ideal para principiantes.
Las estructuras de datos principales en Python son listas, tuplas, diccionarios y conjuntos.
"""


def test_settings_qdrant():
    """1. Verificar que las variables de Qdrant están configuradas."""
    print("=" * 60)
    print("TEST 1: Variables de configuración Qdrant")
    print("=" * 60)
    required = {
        "QDRANT_URL": settings.QDRANT_URL,
        "QDRANT_API_KEY": settings.QDRANT_API_KEY,
        "QDRANT_COLLECTION": settings.QDRANT_COLLECTION,
    }
    all_ok = True
    for key, value in required.items():
        status = "OK" if value else "FALTA"
        if not value:
            all_ok = False
        # No mostramos el API key completo por seguridad
        display = value if key != "QDRANT_API_KEY" else (value[:8] + "..." if value else None)
        print(f"  {key}: {display} [{status}]")

    if all_ok:
        print(">> PASS: Variables de Qdrant configuradas.\n")
    else:
        print(">> FAIL: Faltan variables de Qdrant.\n")
    return all_ok


def test_embeddings():
    """2. Verificar que se pueden generar embeddings con BAAI/bge-m3."""
    print("=" * 60)
    print("TEST 2: get_embeddings() + embed_query()")
    print("=" * 60)
    try:
        from rag.embeddings import get_embeddings

        embeddings = get_embeddings()
        vector = embeddings.embed_query("Hola mundo")
        assert isinstance(vector, list), "El embedding no es una lista"
        assert len(vector) > 0, "El vector de embedding está vacío"
        print(f"  Modelo cargado correctamente.")
        print(f"  Dimensión del vector: {len(vector)}")
        print(f"  Primeros 5 valores: {vector[:5]}")
        print(">> PASS: Embeddings generados correctamente.\n")
        return True
    except Exception as e:
        print(f">> FAIL: Excepción -> {e}\n")
        return False


def test_qdrant_connection():
    """3. Verificar conexión al servidor Qdrant Cloud."""
    print("=" * 60)
    print("TEST 3: Conexión a Qdrant Cloud")
    print("=" * 60)
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        collections = client.get_collections()
        names = [c.name for c in collections.collections]
        print(f"  Conexión exitosa. Colecciones existentes: {names}")
        print(">> PASS: Qdrant accesible.\n")
        return True
    except Exception as e:
        print(f">> FAIL: Excepción -> {e}\n")
        return False


def test_index_documents():
    """4. Verificar indexación de un documento de prueba."""
    print("=" * 60)
    print("TEST 4: index_documents()")
    print("=" * 60)
    try:
        from rag.indexer import index_documents

        index_documents(
            text=SAMPLE_TEXT,
            source_id="__test_rag__",
            replace_existing_source=True,
        )
        print("  Documento indexado con source_id='__test_rag__'.")
        print(">> PASS: Indexación completada sin errores.\n")
        return True
    except Exception as e:
        print(f">> FAIL: Excepción -> {e}\n")
        return False


def test_retriever():
    """5. Verificar que el retriever devuelve documentos relevantes."""
    print("=" * 60)
    print("TEST 5: create_retriever() + búsqueda")
    print("=" * 60)
    try:
        from rag.retriever import create_retriever

        retriever = create_retriever(top_k=3)
        docs = retriever.invoke("¿Qué paradigmas soporta Python?")
        print(f"  Documentos recuperados: {len(docs)}")
        if docs:
            for i, doc in enumerate(docs):
                preview = doc.page_content[:120].replace("\n", " ")
                print(f"  [{i+1}] {preview}...")
            print(">> PASS: Retriever funcional.\n")
            return True
        else:
            print(">> FAIL: No se recuperó ningún documento.\n")
            return False
    except Exception as e:
        print(f">> FAIL: Excepción -> {e}\n")
        return False


def test_cleanup():
    """6. Limpiar datos de prueba de Qdrant."""
    print("=" * 60)
    print("TEST 6: Limpieza de datos de prueba")
    print("=" * 60)
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import FieldCondition, Filter, MatchValue, PayloadSchemaType

        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        if client.collection_exists(settings.QDRANT_COLLECTION):
            # Aseguramos que el índice existe antes de filtrar
            try:
                client.create_payload_index(
                    collection_name=settings.QDRANT_COLLECTION,
                    field_name="metadata.source_id",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass  # El índice ya existe

            client.delete(
                collection_name=settings.QDRANT_COLLECTION,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.source_id",
                            match=MatchValue(value="__test_rag__"),
                        )
                    ]
                ),
            )
            print("  Datos de prueba eliminados de la colección.")
        else:
            print("  La colección no existe, nada que limpiar.")
        print(">> PASS: Limpieza completada.\n")
        return True
    except Exception as e:
        print(f">> FAIL: Excepción en limpieza -> {e}\n")
        return False


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("   TEST DEL FLUJO RAG COMPLETO")
    print("#" * 60 + "\n")

    results = {}

    results["settings_qdrant"] = test_settings_qdrant()
    if not results["settings_qdrant"]:
        print("Abortando: faltan variables de Qdrant.\n")
        sys.exit(1)

    results["embeddings"] = test_embeddings()
    if not results["embeddings"]:
        print("Abortando: los embeddings no funcionan.\n")
        sys.exit(1)

    results["qdrant_connection"] = test_qdrant_connection()
    if not results["qdrant_connection"]:
        print("Abortando: no se puede conectar a Qdrant.\n")
        sys.exit(1)

    results["index_documents"] = test_index_documents()
    results["retriever"] = test_retriever()
    results["cleanup"] = test_cleanup()

    # Resumen
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n  {passed}/{total} tests pasados.")

    if passed < total:
        sys.exit(1)
