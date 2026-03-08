"""
Test independiente para verificar el funcionamiento del agente Educador.
Ejecutar desde la carpeta code/:
    python -m tests.test_educador
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_groq import ChatGroq
from agents.educador import EducadorAgent


# Inicializamos el LLM
#llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.LLM_API_KEY, temperature=0)

# Creamos la instancia del agente educador
educador = EducadorAgent(llm)


def test_respuesta_basica():
    """1. Verificar que el agente Educador devuelve una respuesta ante una pregunta sencilla."""
    print("=" * 60)
    print("TEST 1: Respuesta básica del Educador")
    print("=" * 60)
    state = {
        "mensajes": [("user", "¿Qué es una variable en programación?")],
        "user_level": "principiante",
        "contexto": "No disponible",
    }
    try:
        result = educador.run(state)
        assert "mensajes" in result, "La respuesta no contiene la clave 'mensajes'"
        assert len(result["mensajes"]) > 0, "La lista de mensajes está vacía"
        assert "explicaciones" in result, "La respuesta no contiene la clave 'explicaciones'"
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 200 chars): {contenido[:200]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_nivel_avanzado():
    """2. Verificar que el agente adapta la respuesta al nivel avanzado."""
    print("=" * 60)
    print("TEST 2: Respuesta adaptada a nivel avanzado")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Explícame el polimorfismo en Java")],
        "user_level": "avanzado",
        "contexto": "No disponible",
    }
    try:
        result = educador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 200 chars): {contenido[:200]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_con_contexto_rag():
    """3. Verificar que el agente utiliza el contexto RAG proporcionado."""
    print("=" * 60)
    print("TEST 3: Respuesta con contexto RAG")
    print("=" * 60)
    contexto = (
        "En Java, un bucle for se usa para repetir un bloque de código un número "
        "determinado de veces. Su sintaxis es: for (inicialización; condición; incremento) { ... }"
    )
    state = {
        "mensajes": [("user", "No entiendo cómo funciona el bucle for")],
        "user_level": "principiante",
        "contexto": contexto,
    }
    try:
        result = educador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 200 chars): {contenido[:200]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_sin_nivel_usuario():
    """4. Verificar que el agente funciona cuando no se proporciona nivel de usuario (usa el valor por defecto)."""
    print("=" * 60)
    print("TEST 4: Sin nivel de usuario (valor por defecto)")
    print("=" * 60)
    state = {
        "mensajes": [("user", "¿Qué es la herencia en programación orientada a objetos?")],
    }
    try:
        result = educador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 200 chars): {contenido[:200]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_estructura_respuesta():
    """5. Verificar que la estructura de la respuesta contiene las claves esperadas."""
    print("=" * 60)
    print("TEST 5: Estructura de la respuesta")
    print("=" * 60)
    state = {
        "mensajes": [("user", "¿Qué es un array?")],
        "user_level": "principiante",
        "contexto": "No disponible",
    }
    try:
        result = educador.run(state)
        assert isinstance(result, dict), "La respuesta no es un diccionario"
        assert "mensajes" in result, "Falta la clave 'mensajes'"
        assert "explicaciones" in result, "Falta la clave 'explicaciones'"
        assert isinstance(result["mensajes"], list), "'mensajes' no es una lista"
        assert isinstance(result["explicaciones"], str), "'explicaciones' no es un string"
        # Verificar que explicaciones coincide con el contenido del mensaje
        assert result["explicaciones"] == result["mensajes"][0].content, \
            "'explicaciones' no coincide con el contenido del mensaje"
        print("  Claves presentes: mensajes, explicaciones")
        print("  Tipos correctos: mensajes=list, explicaciones=str")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


# ─────────────────────────────────────────────
#  Punto de entrada
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TESTS DEL AGENTE EDUCADOR")
    print("=" * 60 + "\n")

    resultados = {
        "Respuesta básica": test_respuesta_basica(),
        "Nivel avanzado": test_nivel_avanzado(),
        "Contexto RAG": test_con_contexto_rag(),
        "Sin nivel usuario": test_sin_nivel_usuario(),
        "Estructura respuesta": test_estructura_respuesta(),
    }

    print("=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    for nombre, ok in resultados.items():
        estado = "PASS" if ok else "FAIL"
        print(f"  {nombre}: {estado}")

    total = len(resultados)
    pasados = sum(1 for v in resultados.values() if v)
    print(f"\n  Total: {pasados}/{total} tests pasados.")

    if pasados < total:
        sys.exit(1)
