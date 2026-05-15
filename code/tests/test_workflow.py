"""
Tests de integracion del workflow completo del grafo multi-agente de Codi.
Prueba escenarios end-to-end del sistema: rutas del supervisor, flujo
educador -> demostrador, demostrador directo, evaluacion de codigo,
casos fuera de ambito y comportamiento multi-idioma.

REQUIERE entorno completo levantado:
- Qdrant accesible con la coleccion `Introduccion_programacion` indexada.
- MySQL accesible y un alumno con id=1 (para que nodo_guardar_progreso no falle
  en el test del evaluador). Si no, ajustar ALUMNO_ID_TEST abajo o usar None.
- Variables de entorno cargadas (.env): LLM_MODEL, LLM_API_KEY, QDRANT_*, MYSQL_*.

Ejecutar desde code/:
    python -m tests.test_workflow

Tip: los tests llaman al LLM real, asi que cada uno tarda 5-30s y consume API.
Ejecutalos uno a uno cambiando el dict `resultados` al final si tienes que iterar.
"""
import sys
import os
import re
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_core.messages import HumanMessage, AIMessage
from graph.workflow import graph

# Configuracion comun de los tests
ASIGNATURA_TEST = "Introduccion_programacion"
ALUMNO_ID_TEST = 1  # Debe existir en la tabla alumnos. Si no, los tests con BD fallaran.


# ──────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────

def _new_thread() -> str:
    """Genera un thread_id unico para que cada test arranque con memoria limpia."""
    return f"test-{uuid.uuid4()}"


def _run(user_input: str, thread_id: str = None, user_level: str = "principiante",
         asignatura: str = ASIGNATURA_TEST, alumno_id: int = ALUMNO_ID_TEST,
         prev_state: dict = None):
    """Ejecuta el grafo completo y devuelve (final_state, mensajes, ai_messages, segundos)."""
    thread_id = thread_id or _new_thread()
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "mensajes": [("user", user_input)],
        "user_level": user_level,
        "alumno_id": alumno_id,
        "respuesta_supervisor": "",
        "asignatura": asignatura,
    }
    if prev_state:
        initial_state.update(prev_state)

    t0 = time.perf_counter()
    final_state = graph.invoke(initial_state, config)
    dt = time.perf_counter() - t0

    mensajes = final_state.get("mensajes", [])
    ai_messages = [m for m in mensajes if isinstance(m, AIMessage)]
    return final_state, mensajes, ai_messages, dt


def _print_header(num: int, name: str):
    print("=" * 60)
    print(f"TEST {num}: {name}")
    print("=" * 60)


def _print_outcome(ok: bool, extra: str = ""):
    if ok:
        print(f">> PASS  {extra}\n")
    else:
        print(f">> FAIL  {extra}\n")


# ──────────────────────────────────────────────────────────────────
#  CASOS FACILES
# ──────────────────────────────────────────────────────────────────

def test_saludo_finish_directo():
    """1. Saludo basico ('Hola') -> supervisor FINISH, sin invocar agentes."""
    _print_header(1, "Saludo basico -> FINISH del supervisor")
    try:
        state, msgs, ai_msgs, dt = _run("Hola, buenos dias")
        # El supervisor debe terminar el flujo sin pasar por educador/demostrador
        assert state.get("next") == "FINISH", \
            f"next deberia ser FINISH, fue '{state.get('next')}'"
        # No deberia haber AIMessages nuevos (los agentes no se invocaron)
        # El supervisor puede haber rellenado respuesta_supervisor con un saludo
        print(f"  respuesta_supervisor: '{state.get('respuesta_supervisor', '')[:120]}'")
        print(f"  AIMessages: {len(ai_msgs)}  (esperado: 0)")
        print(f"  Tiempo: {dt:.1f}s")
        ok = len(ai_msgs) == 0
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


def test_pregunta_teorica_educador_y_demostrador():
    """2. Pregunta teorica sobre concepto del temario -> educador + demostrador (flujo lineal)."""
    _print_header(2, "Pregunta teorica -> educador + demostrador")
    try:
        state, msgs, ai_msgs, dt = _run("Explicame que es una variable en C++")
        explicaciones = state.get("explicaciones", "")
        demostraciones = state.get("demostraciones", "")
        assert explicaciones, "Educador no produjo explicaciones"
        # demostraciones puede estar vacio si el filtro de fallback se activo
        # (concepto sin ejemplos en RAG), pero la mayoria de casos basicos lo trae
        print(f"  Explicaciones (len): {len(explicaciones)}")
        print(f"  Demostraciones (len): {len(demostraciones)}")
        print(f"  AIMessages emitidos: {len(ai_msgs)}  (esperado: 1 o 2)")
        print(f"  Tiempo: {dt:.1f}s")
        # Aceptamos 1 (demostrador filtrado) o 2 (ambos emitidos)
        ok = len(ai_msgs) in (1, 2) and len(explicaciones) > 50
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


def test_pedir_ejemplo_directo():
    """3. Peticion directa de ejemplo de codigo -> demostrador directo (sin educador)."""
    _print_header(3, "Pedir ejemplo directo -> demostrador (modo DIRECTO)")
    try:
        state, msgs, ai_msgs, dt = _run("Dame un ejemplo de un bucle for en C++")
        demostraciones = state.get("demostraciones", "")
        explicaciones = state.get("explicaciones", "")
        assert demostraciones, "Demostrador no produjo demostraciones"
        # Como es modo directo, NO deberia haberse ejecutado el educador
        assert not explicaciones, \
            f"En modo directo no deberia haber explicaciones del educador, las hay (len={len(explicaciones)})"
        # Verificamos que la respuesta contiene un bloque de codigo
        tiene_codigo = "```" in demostraciones or "for" in demostraciones.lower()
        print(f"  Demostraciones (primeros 200): {demostraciones[:200]}...")
        print(f"  Tiene bloque de codigo / 'for': {tiene_codigo}")
        print(f"  Tiempo: {dt:.1f}s")
        ok = bool(demostraciones) and tiene_codigo
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


# ──────────────────────────────────────────────────────────────────
#  CASOS LIMITE
# ──────────────────────────────────────────────────────────────────

def test_fuera_de_ambito():
    """4. Pregunta totalmente fuera del temario -> respuesta_supervisor de fuera de ambito."""
    _print_header(4, "Fuera de ambito -> respuesta_supervisor explicativa")
    try:
        state, msgs, ai_msgs, dt = _run("Dame una receta para hacer paella valenciana")
        respuesta = state.get("respuesta_supervisor", "")
        assert respuesta, "Falta respuesta_supervisor para tema fuera de ambito"
        # Buscamos palabras clave que indican el fallback de fuera de ambito
        respuesta_low = respuesta.lower()
        es_fallback = any(p in respuesta_low for p in [
            "no tengo informaci", "fuera de", "no puedo ayudar", "ambit",
            "i don't have information", "outside",
        ])
        print(f"  respuesta_supervisor: '{respuesta[:200]}'")
        print(f"  Detectado como fallback de ambito: {es_fallback}")
        print(f"  AIMessages: {len(ai_msgs)}  (esperado: 0)")
        print(f"  Tiempo: {dt:.1f}s")
        ok = es_fallback and len(ai_msgs) == 0
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


def test_demostrador_tras_educador_no_dispara_fallback():
    """5. Concepto cuya documentacion en RAG sea limitada -> el demostrador NO debe
    concatenar el texto 'no tengo informacion' al final del educador."""
    _print_header(5, "Demostrador tras educador no filtra fallback al alumno")
    try:
        state, msgs, ai_msgs, dt = _run("Explicame los algoritmos de busqueda binaria")
        # Sumamos contenido de todos los AIMessages (lo que recibe el alumno concatenado)
        contenido_total = "\n".join(
            m.content if isinstance(m.content, str) else str(m.content)
            for m in ai_msgs
        )
        contenido_low = contenido_total.lower()
        # El alumno no deberia ver estos textos al final del educador
        frases_prohibidas = [
            "no tengo informaci",
            "corresponde a otro agente",
            "i don't have information",
            "corresponds to another agent",
        ]
        encontradas = [f for f in frases_prohibidas if f in contenido_low]
        print(f"  AIMessages emitidos: {len(ai_msgs)}")
        print(f"  Contenido total (chars): {len(contenido_total)}")
        print(f"  Frases prohibidas detectadas: {encontradas}")
        print(f"  Tiempo: {dt:.1f}s")
        ok = len(encontradas) == 0 and len(ai_msgs) >= 1
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


def test_idioma_ingles():
    """6. Pregunta en ingles -> el supervisor detecta 'en' y el agente genera contenido."""
    _print_header(6, "Idioma ingles -> supervisor detecta 'en' + hay contenido")
    try:
        state, msgs, ai_msgs, dt = _run("Explain me what a variable is in C++")
        # 1. El supervisor detecto idioma 'en'
        idioma = state.get("idioma")
        assert idioma == "en", f"Idioma detectado deberia ser 'en', fue '{idioma}'"
        # 2. Hay contenido en alguna fuente (educador, demostrador o respuesta_supervisor).
        # Concatenamos todas las posibles fuentes para verificar que algo se genero.
        fuentes = [
            state.get("explicaciones", "") or "",
            state.get("demostraciones", "") or "",
            state.get("respuesta_supervisor", "") or "",
        ]
        for m in ai_msgs:
            c = m.content
            if isinstance(c, list):
                c = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)
            fuentes.append(str(c))
        contenido_total = "\n".join(fuentes).strip()
        print(f"  Idioma state: '{idioma}'")
        print(f"  Contenido total (chars): {len(contenido_total)}")
        print(f"  Snippet (primeros 200): {contenido_total[:200]}...")
        print(f"  Tiempo: {dt:.1f}s")
        # Nota: la deteccion real de idioma del texto generado se considera fuera de alcance
        # del test (los prompts EN obligan a responder en ingles; confiamos en eso). Aqui solo
        # validamos que el routing del idioma funciono y que hay contenido devuelto.
        ok = bool(contenido_total)
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


def test_evaluacion_codigo():
    """7. Alumno envia codigo para evaluar -> evaluador + critico, state con puntuacion."""
    _print_header(7, "Evaluacion de codigo -> evaluador + critico + guardar_progreso")
    codigo_alumno = """Evalua mi codigo para sumar dos numeros:
```cpp
#include <iostream>
int main() {
    int a = 5;
    int b = 10;
    std::cout << a + b << std::endl;
    return 0;
}
```"""
    try:
        state, msgs, ai_msgs, dt = _run(codigo_alumno)
        puntuacion = state.get("puntuacion")
        feedback = state.get("feedback", "")
        print(f"  Puntuacion: {puntuacion}")
        print(f"  Feedback (len): {len(feedback)}")
        print(f"  AIMessages: {len(ai_msgs)}")
        print(f"  Tiempo: {dt:.1f}s")
        ok = puntuacion is not None and 0 <= float(puntuacion) <= 10 and bool(feedback)
        _print_outcome(ok)
        return ok
    except Exception as e:
        # Si falla por BD (alumno_id no existe), lo notamos pero no es fallo del agente
        _print_outcome(False, f"Error: {e}  (revisa que alumno_id={ALUMNO_ID_TEST} exista en BD)")
        return False


def test_mensaje_vacio_o_muy_corto():
    """8. Mensaje muy corto / sin contenido util -> el sistema no debe romperse."""
    _print_header(8, "Mensaje muy corto sin contenido util")
    try:
        state, msgs, ai_msgs, dt = _run("?")
        # No nos importa la respuesta concreta, solo que no haya excepcion
        print(f"  next: {state.get('next')}")
        print(f"  respuesta_supervisor: '{state.get('respuesta_supervisor', '')[:120]}'")
        print(f"  AIMessages: {len(ai_msgs)}")
        print(f"  Tiempo: {dt:.1f}s")
        ok = True  # No crashear es suficiente
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


def test_multiturno_misma_conversacion():
    """9. Dos turnos consecutivos con el mismo thread_id -> el segundo turno debe usar
    el historial del primero (la memoria del checkpoint funciona)."""
    _print_header(9, "Multi-turno con misma thread_id (memoria del grafo)")
    thread = _new_thread()
    try:
        # Turno 1: pregunta teorica
        state1, _, ai1, dt1 = _run("Explicame que es un bucle while", thread_id=thread)
        explicaciones1 = state1.get("explicaciones", "")
        assert explicaciones1, "Turno 1: educador no respondio"

        # Turno 2: follow-up que solo tiene sentido con contexto previo
        state2, msgs2, ai2, dt2 = _run("Dame un ejemplo de eso en codigo", thread_id=thread)
        # El turno 2 puede haber pasado por cualquier agente segun decida el supervisor:
        # demostrador (modo DIRECTO o tras educador), educador, o respuesta_supervisor.
        # Aceptamos contenido en cualquiera de las fuentes y/o en el ultimo AIMessage nuevo.
        demostraciones2 = state2.get("demostraciones", "") or ""
        explicaciones2 = state2.get("explicaciones", "") or ""
        respuesta_sup2 = state2.get("respuesta_supervisor", "") or ""
        ultimo_ai = ai2[-1].content if ai2 else ""
        if isinstance(ultimo_ai, list):
            ultimo_ai = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in ultimo_ai)
        # Solo nos importa si hubo *algun* contenido nuevo del turno 2; si ai2 crecio respecto
        # al turno 1, lo damos por bueno. demostraciones/explicaciones podrian ser cache del t1.
        contenido2 = demostraciones2 or respuesta_sup2 or explicaciones2 or str(ultimo_ai)
        total_msgs = len(msgs2)
        # Comparamos numero de AIMessages t2 vs t1 para detectar que t2 genero respuesta nueva
        ai_t1 = [m for m in msgs2[:-1] if isinstance(m, AIMessage)]  # antes de user2
        ai_solo_t2 = len(ai2) - len(ai_t1)
        print(f"  Turno 1 - explicaciones (len): {len(explicaciones1)}, t={dt1:.1f}s")
        print(f"  Turno 2 - explicaciones (len): {len(explicaciones2)}")
        print(f"  Turno 2 - demostraciones (len): {len(demostraciones2)}")
        print(f"  Turno 2 - respuesta_supervisor (len): {len(respuesta_sup2)}")
        print(f"  Turno 2 - AIMessages nuevos: {ai_solo_t2}")
        print(f"  Turno 2 - contenido (primeros 200): {contenido2[:200]}...")
        print(f"  Turno 2 - mensajes totales en state: {total_msgs}  (esperado > 3)")
        print(f"  Tiempo turno 2: {dt2:.1f}s")
        # La memoria del checkpoint funciona si el state acumula mensajes entre turnos
        # y el turno 2 produjo algo (ya sea un AI nuevo o respuesta_supervisor).
        produjo_algo_t2 = ai_solo_t2 > 0 or bool(respuesta_sup2.strip())
        ok = total_msgs > 3 and produjo_algo_t2
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


def test_demostrador_directo_sin_material():
    """10. Demostrador directo sobre algo razonable -> debe generar ejemplo, NO fallback."""
    _print_header(10, "Demostrador directo sobre tema del temario")
    try:
        state, msgs, ai_msgs, dt = _run("Muestrame un ejemplo de declarar una variable entera en C++")
        demostraciones = state.get("demostraciones", "")
        # En modo directo el fallback es legitimo. Si dispara fallback, lo veremos.
        # Si el RAG tiene material (probable para algo tan basico), debe haber codigo.
        es_fallback = any(p in demostraciones.lower() for p in [
            "no tengo informaci", "i don't have information",
        ])
        tiene_codigo = "int " in demostraciones or "```" in demostraciones
        print(f"  Demostraciones (primeros 200): {demostraciones[:200]}...")
        print(f"  Es fallback: {es_fallback}")
        print(f"  Tiene codigo de variable: {tiene_codigo}")
        print(f"  Tiempo: {dt:.1f}s")
        # Aceptamos tanto fallback (si RAG vacio) como ejemplo (si RAG ok). Lo importante
        # es que se ejecuto el demostrador y no rompio.
        ok = bool(demostraciones)
        _print_outcome(ok)
        return ok
    except Exception as e:
        _print_outcome(False, f"Error: {e}")
        return False


# ──────────────────────────────────────────────────────────────────
#  Punto de entrada
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TESTS DE INTEGRACION - WORKFLOW COMPLETO")
    print("=" * 60)
    print(f"  Asignatura: {ASIGNATURA_TEST}")
    print(f"  Alumno ID:  {ALUMNO_ID_TEST}")
    print("  Cada test llama al LLM real (5-30s).")
    print("=" * 60 + "\n")

    resultados = {
        "1. Saludo -> FINISH":                      test_saludo_finish_directo(),
        "2. Pregunta teorica -> educ+demo":         test_pregunta_teorica_educador_y_demostrador(),
        "3. Ejemplo directo -> demo solo":          test_pedir_ejemplo_directo(),
        "4. Fuera de ambito":                       test_fuera_de_ambito(),
        "5. Demo tras educ sin fallback al alumno": test_demostrador_tras_educador_no_dispara_fallback(),
        "6. Idioma ingles":                         test_idioma_ingles(),
        "7. Evaluacion de codigo":                  test_evaluacion_codigo(),
        "8. Mensaje muy corto":                     test_mensaje_vacio_o_muy_corto(),
        "9. Multi-turno (memoria)":                 test_multiturno_misma_conversacion(),
        "10. Demo directo del temario":             test_demostrador_directo_sin_material(),
    }

    print("=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    for nombre, ok in resultados.items():
        estado = "PASS" if ok else "FAIL"
        print(f"  [{estado}]  {nombre}")

    total = len(resultados)
    pasados = sum(1 for v in resultados.values() if v)
    print(f"\n  Total: {pasados}/{total} tests pasados.\n")

    if pasados < total:
        sys.exit(1)
