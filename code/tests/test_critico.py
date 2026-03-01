"""
Test independiente para verificar el funcionamiento del agente Crítico.
Ejecutar desde la carpeta code/:
    python -m tests.test_critico
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_groq import ChatGroq
from agents.critico import CriticoAgent


# Inicializamos el LLM y el agente
llm = ChatGroq(model=os.getenv("LLM_MODEL", "llama3-70b-8192"), temperature=0)
critico = CriticoAgent(llm)


def test_respuesta_basica():
    """1. Verificar que el agente Crítico devuelve una respuesta ante código sencillo."""
    print("=" * 60)
    print("TEST 1: Respuesta básica del Crítico")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Revisa mi código por favor")],
        "user_level": "principiante",
        "enunciado": "Escribe un programa en Java que imprima los números del 1 al 10.",
        "codigo_alumno": (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        for (int i = 1; i <= 10; i++) {\n"
            "            System.out.println(i);\n"
            "        }\n"
            "    }\n"
            "}"
        ),
    }
    try:
        result = critico.run(state)
        assert "mensajes" in result, "La respuesta no contiene la clave 'mensajes'"
        assert len(result["mensajes"]) > 0, "La lista de mensajes está vacía"
        assert "explicaciones" in result, "La respuesta no contiene la clave 'explicaciones'"
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_codigo_con_errores():
    """2. Verificar que el agente detecta errores en código incorrecto."""
    print("=" * 60)
    print("TEST 2: Detección de errores en código incorrecto")
    print("=" * 60)
    state = {
        "mensajes": [("user", "¿Está bien mi código?")],
        "user_level": "principiante",
        "enunciado": "Escribe un programa en Java que calcule la suma de los números del 1 al 100.",
        "codigo_alumno": (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        int suma = 0\n"  # falta punto y coma
            "        for (int i = 1; i <= 100; i++)\n"  # falta llave
            "            suma += i;\n"
            "        System.out.println(suma)\n"  # falta punto y coma
            "    }\n"
            "}"
        ),
    }
    try:
        result = critico.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_nivel_avanzado():
    """3. Verificar que el agente adapta el feedback al nivel avanzado."""
    print("=" * 60)
    print("TEST 3: Feedback adaptado a nivel avanzado")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Analiza mi implementación")],
        "user_level": "avanzado",
        "enunciado": "Implementa un método que ordene un array de enteros usando QuickSort.",
        "codigo_alumno": (
            "public class QuickSort {\n"
            "    public static void quickSort(int[] arr, int low, int high) {\n"
            "        if (low < high) {\n"
            "            int pi = partition(arr, low, high);\n"
            "            quickSort(arr, low, pi - 1);\n"
            "            quickSort(arr, pi + 1, high);\n"
            "        }\n"
            "    }\n"
            "    static int partition(int[] arr, int low, int high) {\n"
            "        int pivot = arr[high];\n"
            "        int i = low - 1;\n"
            "        for (int j = low; j < high; j++) {\n"
            "            if (arr[j] < pivot) {\n"
            "                i++;\n"
            "                int temp = arr[i]; arr[i] = arr[j]; arr[j] = temp;\n"
            "            }\n"
            "        }\n"
            "        int temp = arr[i+1]; arr[i+1] = arr[high]; arr[high] = temp;\n"
            "        return i + 1;\n"
            "    }\n"
            "}"
        ),
    }
    try:
        result = critico.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_sin_enunciado_ni_codigo():
    """4. Verificar que el agente funciona con valores por defecto (sin enunciado ni código)."""
    print("=" * 60)
    print("TEST 4: Sin enunciado ni código (valores por defecto)")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Revisa mi código")],
    }
    try:
        result = critico.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
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
        "mensajes": [("user", "Mira este código")],
        "user_level": "principiante",
        "enunciado": "Imprime Hola Mundo",
        "codigo_alumno": 'System.out.println("Hola Mundo");',
    }
    try:
        result = critico.run(state)
        assert isinstance(result, dict), "La respuesta no es un diccionario"
        assert "mensajes" in result, "Falta la clave 'mensajes'"
        assert "explicaciones" in result, "Falta la clave 'explicaciones'"
        assert isinstance(result["mensajes"], list), "'mensajes' no es una lista"
        assert isinstance(result["explicaciones"], str), "'explicaciones' no es un string"
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
    print("  TESTS DEL AGENTE CRÍTICO")
    print("=" * 60 + "\n")

    resultados = {
        "Respuesta básica": test_respuesta_basica(),
        "Código con errores": test_codigo_con_errores(),
        "Nivel avanzado": test_nivel_avanzado(),
        "Sin enunciado ni código": test_sin_enunciado_ni_codigo(),
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
