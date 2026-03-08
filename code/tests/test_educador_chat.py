"""
Chat interactivo con el agente Educador.
Permite mantener una conversación en tiempo real para probar su comportamiento.

Ejecutar desde la carpeta code/:
    python -m tests.test_educador_chat
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from agents.educador import EducadorAgent


# Inicializamos el LLM y el agente
#llm = ChatGroq(model=os.getenv("LLM_MODEL", "llama3-70b-8192"), temperature=0)

from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.LLM_API_KEY, temperature=0)
educador = EducadorAgent(llm)


def chat():
    """Inicia una conversación interactiva con el agente Educador."""
    print("\n" + "=" * 60)
    print("  CHAT INTERACTIVO - AGENTE EDUCADOR")
    print("=" * 60)
    print("  Escribe tu mensaje y pulsa Enter.")
    print("  Escribe 'salir' para terminar la conversación.")
    print("  Escribe 'nivel:<valor>' para cambiar tu nivel")
    print("    (ej: nivel:avanzado)")
    print("=" * 60 + "\n")

    # Estado que se mantiene durante toda la conversación
    historial = []
    user_level = "principiante"
    contexto = "No disponible"

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

        # Comando para cambiar el nivel del usuario
        if user_input.lower().startswith("nivel:"):
            user_level = user_input.split(":", 1)[1].strip()
            print(f"  [Nivel cambiado a: {user_level}]\n")
            continue

        # Añadimos el mensaje del usuario al historial
        historial.append(HumanMessage(content=user_input))

        # Construimos el estado para el agente
        state = {
            "mensajes": list(historial),
            "user_level": user_level,
            "contexto": contexto,
        }

        try:
            result = educador.run(state)
            respuesta = result["mensajes"][0]

            # Añadimos la respuesta del agente al historial
            historial.append(respuesta)

            print(f"\nEducador: {respuesta.content}\n")
        except Exception as e:
            print(f"\n  [Error: {e}]\n")


if __name__ == "__main__":
    chat()
