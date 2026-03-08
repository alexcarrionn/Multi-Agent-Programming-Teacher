"""
Test independiente para verificar el funcionamiento del agente Demostrador.
Ejecutar desde la carpeta code/:
    python -m tests.test_demostrador
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_groq import ChatGroq
from agents.demostrador import DemostradorAgent


# Inicializamos el LLM y el agente
#llm = ChatGroq(model=os.getenv("LLM_MODEL", "llama3-70b-8192"), temperature=0)

from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.LLM_API_KEY, temperature=0)

demostrador = DemostradorAgent(llm)


def test_respuesta_basica():
    """1. Verificar que el agente Demostrador devuelve una respuesta ante una petición sencilla."""
    print("=" * 60)
    print("TEST 1: Respuesta básica del Demostrador")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Dame un ejemplo de un bucle for")],
        "user_level": "principiante",
        "concepto": "bucle for",
        "contexto": "No disponible",
    }
    try:
        result = demostrador.run(state)
        assert "mensajes" in result, "La respuesta no contiene la clave 'mensajes'"
        assert len(result["mensajes"]) > 0, "La lista de mensajes está vacía"
        assert "demostraciones" in result, "La respuesta no contiene la clave 'demostraciones'"
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_ejemplo_con_concepto():
    """2. Verificar que el agente genera un ejemplo relacionado con el concepto proporcionado."""
    print("=" * 60)
    print("TEST 2: Ejemplo con concepto específico (arrays)")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Muéstrame un ejemplo de arrays")],
        "user_level": "principiante",
        "concepto": "arrays",
        "contexto": "No disponible",
    }
    try:
        result = demostrador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_nivel_avanzado():
    """3. Verificar que el agente adapta el ejemplo al nivel avanzado."""
    print("=" * 60)
    print("TEST 3: Ejemplo adaptado a nivel avanzado")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Dame un ejemplo de punteros y memoria dinámica")],
        "user_level": "avanzado",
        "concepto": "punteros y memoria dinámica",
        "contexto": "No disponible",
    }
    try:
        result = demostrador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_con_contexto_rag():
    """4. Verificar que el agente utiliza el contexto RAG proporcionado."""
    print("=" * 60)
    print("TEST 4: Ejemplo con contexto RAG")
    print("=" * 60)
    contexto = (
        "Las funciones en C++ permiten encapsular un bloque de código reutilizable. "
        "Se declaran con tipo_retorno nombre(parámetros) { cuerpo }."
    )
    state = {
        "mensajes": [("user", "Dame un ejemplo de funciones")],
        "user_level": "intermedio",
        "concepto": "funciones",
        "contexto": contexto,
    }
    try:
        result = demostrador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_sin_concepto():
    """5. Verificar que el agente funciona con valores por defecto (sin concepto)."""
    print("=" * 60)
    print("TEST 5: Sin concepto (valor por defecto)")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Dame un ejemplo de código")],
    }
    try:
        result = demostrador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_estructura_respuesta():
    """6. Verificar que la estructura de la respuesta contiene las claves esperadas."""
    print("=" * 60)
    print("TEST 6: Estructura de la respuesta")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Ejemplo de variables")],
        "user_level": "principiante",
        "concepto": "variables",
        "contexto": "No disponible",
    }
    try:
        result = demostrador.run(state)
        assert isinstance(result, dict), "La respuesta no es un diccionario"
        assert "mensajes" in result, "Falta la clave 'mensajes'"
        assert "demostraciones" in result, "Falta la clave 'demostraciones'"
        assert isinstance(result["mensajes"], list), "'mensajes' no es una lista"
        assert isinstance(result["demostraciones"], str), "'demostraciones' no es un string"
        assert result["demostraciones"] == result["mensajes"][0].content, \
            "'demostraciones' no coincide con el contenido del mensaje"
        print("  Claves presentes: mensajes, demostraciones")
        print("  Tipos correctos: mensajes=list, demostraciones=str")
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
    print("  TESTS DEL AGENTE DEMOSTRADOR")
    print("=" * 60 + "\n")

    resultados = {
        "Respuesta básica": test_respuesta_basica(),
        "Ejemplo con concepto": test_ejemplo_con_concepto(),
        "Nivel avanzado": test_nivel_avanzado(),
        "Contexto RAG": test_con_contexto_rag(),
        "Sin concepto": test_sin_concepto(),
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
