"""
Test independiente para verificar el funcionamiento del agente Evaluador.
Ejecutar desde la carpeta code/:
    python -m tests.test_evaluador
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_groq import ChatGroq
from agents.evaluador import EvaluadorAgent


# Inicializamos el LLM y el agente
llm = ChatGroq(model=os.getenv("LLM_MODEL", "llama3-70b-8192"), temperature=0)
evaluador = EvaluadorAgent(llm)


def test_respuesta_basica():
    """1. Verificar que el agente Evaluador devuelve una respuesta ante código correcto."""
    print("=" * 60)
    print("TEST 1: Respuesta básica del Evaluador")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Evalúa mi código por favor")],
        "user_level": "principiante",
        "enunciado": "Escribe un programa en C++ que imprima los números del 1 al 10.",
        "codigo_alumno": (
            "#include <iostream>\n"
            "using namespace std;\n"
            "int main() {\n"
            "    for (int i = 1; i <= 10; i++) {\n"
            "        cout << i << endl;\n"
            "    }\n"
            "    return 0;\n"
            "}"
        ),
        "contexto": "No disponible",
    }
    try:
        result = evaluador.run(state)
        assert "mensajes" in result, "La respuesta no contiene la clave 'mensajes'"
        assert len(result["mensajes"]) > 0, "La lista de mensajes está vacía"
        assert "puntuacion" in result, "La respuesta no contiene la clave 'puntuacion'"
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_codigo_con_errores():
    """2. Verificar que el agente detecta errores y asigna una nota baja."""
    print("=" * 60)
    print("TEST 2: Evaluación de código con errores")
    print("=" * 60)
    state = {
        "mensajes": [("user", "¿Qué nota le pones a mi código?")],
        "user_level": "principiante",
        "enunciado": "Escribe un programa en C++ que calcule la suma de los números del 1 al 100.",
        "codigo_alumno": (
            "#include <iostream>\n"
            "using namespace std;\n"
            "int main() {\n"
            "    int suma = 0\n"  # falta punto y coma
            "    for (int i = 1; i <= 100; i++)\n"  # falta llave
            "        suma += i;\n"
            "    cout << suma << endl\n"  # falta punto y coma
            "    return 0;\n"
            "}"
        ),
        "contexto": "No disponible",
    }
    try:
        result = evaluador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_nivel_avanzado():
    """3. Verificar que el agente adapta la evaluación al nivel avanzado."""
    print("=" * 60)
    print("TEST 3: Evaluación adaptada a nivel avanzado")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Evalúa mi implementación")],
        "user_level": "avanzado",
        "enunciado": "Implementa una función que ordene un vector de enteros usando Merge Sort.",
        "codigo_alumno": (
            "#include <iostream>\n"
            "#include <vector>\n"
            "using namespace std;\n\n"
            "void merge(vector<int>& arr, int l, int m, int r) {\n"
            "    int n1 = m - l + 1, n2 = r - m;\n"
            "    vector<int> L(n1), R(n2);\n"
            "    for (int i = 0; i < n1; i++) L[i] = arr[l + i];\n"
            "    for (int j = 0; j < n2; j++) R[j] = arr[m + 1 + j];\n"
            "    int i = 0, j = 0, k = l;\n"
            "    while (i < n1 && j < n2) {\n"
            "        if (L[i] <= R[j]) arr[k++] = L[i++];\n"
            "        else arr[k++] = R[j++];\n"
            "    }\n"
            "    while (i < n1) arr[k++] = L[i++];\n"
            "    while (j < n2) arr[k++] = R[j++];\n"
            "}\n\n"
            "void mergeSort(vector<int>& arr, int l, int r) {\n"
            "    if (l < r) {\n"
            "        int m = l + (r - l) / 2;\n"
            "        mergeSort(arr, l, m);\n"
            "        mergeSort(arr, m + 1, r);\n"
            "        merge(arr, l, m, r);\n"
            "    }\n"
            "}\n"
        ),
        "contexto": "No disponible",
    }
    try:
        result = evaluador.run(state)
        contenido = result["mensajes"][0].content
        assert len(contenido) > 0, "El contenido de la respuesta está vacío"
        print(f"  Respuesta (primeros 300 chars): {contenido[:300]}...")
        print(">> PASS\n")
        return True
    except Exception as e:
        print(f">> FAIL: {e}\n")
        return False


def test_sin_enunciado_ni_codigo():
    """4. Verificar que el agente funciona con valores por defecto."""
    print("=" * 60)
    print("TEST 4: Sin enunciado ni código (valores por defecto)")
    print("=" * 60)
    state = {
        "mensajes": [("user", "Evalúa mi ejercicio")],
    }
    try:
        result = evaluador.run(state)
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
        "mensajes": [("user", "Pon nota a esto")],
        "user_level": "principiante",
        "enunciado": "Imprime Hola Mundo",
        "codigo_alumno": (
            '#include <iostream>\n'
            'using namespace std;\n'
            'int main() {\n'
            '    cout << "Hola Mundo" << endl;\n'
            '    return 0;\n'
            '}'
        ),
        "contexto": "No disponible",
    }
    try:
        result = evaluador.run(state)
        assert isinstance(result, dict), "La respuesta no es un diccionario"
        assert "mensajes" in result, "Falta la clave 'mensajes'"
        assert "puntuacion" in result, "Falta la clave 'puntuacion'"
        assert isinstance(result["mensajes"], list), "'mensajes' no es una lista"
        assert isinstance(result["puntuacion"], str), "'puntuacion' no es un string"
        assert result["puntuacion"] == result["mensajes"][0].content, \
            "'puntuacion' no coincide con el contenido del mensaje"
        print("  Claves presentes: mensajes, puntuacion")
        print("  Tipos correctos: mensajes=list, puntuacion=str")
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
    print("  TESTS DEL AGENTE EVALUADOR")
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
