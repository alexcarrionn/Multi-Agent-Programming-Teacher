"""
Chat interactivo con el agente Demostrador.
Permite pedir ejemplos de código de forma conversacional.

Ejecutar desde la carpeta code/:
    python -m tests.test_demostrador_chat
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

#from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from agents.demostrador import DemostradorAgent
from config.settings import settings

# Inicializamos el LLM y el agente
#llm = ChatGroq(model=os.getenv("LLM_MODEL", "llama3-70b-8192"), temperature=0)

from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.LLM_API_KEY, temperature=0)
demostrador = DemostradorAgent(llm)


def chat():
    """Inicia una conversación interactiva con el agente Demostrador."""
    print("\n" + "=" * 60)
    print("  CHAT INTERACTIVO - AGENTE DEMOSTRADOR")
    print("=" * 60)
    print("  Comandos disponibles:")
    print("    salir              -> terminar la conversación")
    print("    nivel:<valor>      -> cambiar nivel (ej: nivel:avanzado)")
    print("    concepto:<valor>   -> establecer concepto a ilustrar")
    print("                         (ej: concepto:bucles while)")
    print("  Cualquier otro texto se envía como mensaje al agente.")
    print("=" * 60 + "\n")

    historial = []
    user_level = "principiante"
    concepto = "No disponible"
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

        # Comando para cambiar el nivel
        if user_input.lower().startswith("nivel:"):
            user_level = user_input.split(":", 1)[1].strip()
            print(f"  [Nivel cambiado a: {user_level}]\n")
            continue

        # Comando para establecer el concepto
        if user_input.lower().startswith("concepto:"):
            concepto = user_input.split(":", 1)[1].strip()
            print(f"  [Concepto establecido: {concepto}]\n")
            continue

        # Mensaje normal: enviamos al agente
        historial.append(HumanMessage(content=user_input))

        state = {
            "mensajes": list(historial),
            "user_level": user_level,
            "concepto": concepto,
            "contexto": contexto,
        }

        try:
            result = demostrador.run(state)
            respuesta = result["mensajes"][0]
            historial.append(respuesta)
            print(f"\nDemostrador: {respuesta.content}\n")
        except Exception as e:
            print(f"\n  [Error: {e}]\n")


if __name__ == "__main__":
    chat()
