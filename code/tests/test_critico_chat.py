"""
Chat interactivo con el agente Crítico.
Permite mantener una conversación en la que envías tu código y el agente lo analiza.

Ejecutar desde la carpeta code/:
    python -m tests.test_critico_chat
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from agents.critico import CriticoAgent


# Inicializamos el LLM y el agente
#llm = ChatGroq(model=os.getenv("LLM_MODEL", "llama3-70b-8192"), temperature=0)
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"), google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0)

critico = CriticoAgent(llm)


def chat():
    """Inicia una conversación interactiva con el agente Crítico."""
    print("\n" + "=" * 60)
    print("  CHAT INTERACTIVO - AGENTE CRÍTICO")
    print("=" * 60)
    print("  Comandos disponibles:")
    print("    salir           -> terminar la conversación")
    print("    nivel:<valor>   -> cambiar nivel (ej: nivel:avanzado)")
    print("    enunciado       -> establecer el enunciado del ejercicio")
    print("    codigo          -> introducir el código a analizar")
    print("                      (escribe 'FIN' en una línea sola para terminar)")
    print("=" * 60 + "\n")

    historial = []
    user_level = "principiante"
    enunciado = "No disponible"
    codigo_alumno = "No disponible"

    while True:
        try:
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nConversación finalizada.")
            break

        if not user_input:
            continue

        if user_input.lower() == "salir":
            print("\nConversación finalizada. ¡Hasta luego!")
            break

        # Comando para cambiar el nivel
        if user_input.lower().startswith("nivel:"):
            user_level = user_input.split(":", 1)[1].strip()
            print(f"  [Nivel cambiado a: {user_level}]\n")
            continue

        # Comando para establecer el enunciado
        if user_input.lower() == "enunciado":
            print("  Escribe el enunciado del ejercicio:")
            enunciado = input("  > ").strip()
            print(f"  [Enunciado establecido]\n")
            continue

        # Comando para introducir código multilínea
        if user_input.lower() == "codigo":
            print("  Pega tu código (escribe 'FIN' en una línea sola para terminar):")
            lineas = []
            while True:
                linea = input("  | ")
                if linea.strip() == "FIN":
                    break
                lineas.append(linea)
            codigo_alumno = "\n".join(lineas)
            print(f"  [Código registrado ({len(lineas)} líneas)]\n")
            continue

        # Mensaje normal: enviamos al agente
        historial.append(HumanMessage(content=user_input))

        state = {
            "mensajes": list(historial),
            "user_level": user_level,
            "enunciado": enunciado,
            "codigo_alumno": codigo_alumno,
        }

        try:
            result = critico.run(state)
            respuesta = result["mensajes"][0]
            historial.append(respuesta)
            print(f"\nCrítico: {respuesta.content}\n")
        except Exception as e:
            print(f"\n  [Error: {e}]\n")


if __name__ == "__main__":
    chat()
