from langchain_groq import ChatGroq
from agents.agentType import AgentType
from typing import Literal
from typing_extensions import TypedDict
from rag.retriever import create_retriever
from prompts.supervisor_prompts import AGENTE_SUPERVISOR_PROMPT
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import json

#definimos nuestro llm según el modelo configurado
'''if settings.LLM_MODEL.startswith("gemini"):
    llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.LLM_API_KEY, temperature=0)
elif settings.LLM_MODEL.startswith("gpt"):
    llm = ChatOpenAI(model=settings.LLM_MODEL, base_url=settings.LLM_URL, api_key=settings.LLM_API_KEY, temperature=0.2)
elif settings.LLM_MODEL.startswith("groq"):
    llm = ChatGroq(model=settings.LLM_MODEL, temperature=0)
'''
#llm = ChatOpenAI(model=settings.LLM_MODEL.replace("ollama/", ""), base_url=settings.LLM_URL,api_key=settings.LLM_API_KEY,temperature=0.2)
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.LLM_API_KEY, temperature=0)

# Miembros del equipo
miembros = [AgentType.EDUCADOR.value, AgentType.DEMOSTRADOR.value, AgentType.EVALUADOR.value, AgentType.CRITICO.value]

# Agentes que necesitan contexto de la asignatura
AGENTES_EDUCATIVOS = {
    AgentType.EDUCADOR.value,
    AgentType.DEMOSTRADOR.value,
    AgentType.EVALUADOR.value,
    AgentType.CRITICO.value,
}
 
# Mínimo de documentos relevantes que debe encontrar el RAG para considerar que la pregunta está en el ámbito
MIN_DOCS_RELEVANTES = 1
 
class Router(BaseModel):
    next_agent: Literal["educador", "demostrador", "evaluador", "critico", "FINISH"] = Field(description="El siguiente agente que debe actuar o FINISH.")
    enunciado: str = Field(default="")
    codigo_alumno: str = Field(default="")
    idioma: str = Field(default="es")
    respuesta: str = Field(default="", description="Respuesta que el supervisor quiere que se le de al alumno, solo se usará si el supervisor decide que la pregunta no está en el ámbito o si el alumno ha terminado el workflow y se le quiere dar una respuesta final.")

#Definimos el prompt del supervisor, que se encargará de decidir que agente debe actuar 
prompt_supervisor = ChatPromptTemplate.from_messages([
    ("system", AGENTE_SUPERVISOR_PROMPT),
    MessagesPlaceholder(variable_name="mensajes"),
]).partial(members=", ".join(miembros))


def _ultimo_mensaje_usuario(state) -> str:
    """Extrae el contenido del último mensaje del usuario del estado."""
    #Para cada mensaje del estado los recorremos de atrás hacia adelante, si encontramos un mensaje que sea del usuario lo devolvemos, 
    # si no devolvemos una cadena vacía
    for mensaje in reversed(state.get("mensajes", [])):
        if hasattr(mensaje, "type") and mensaje.type == "human":
            return mensaje.content
        elif isinstance(mensaje, tuple) and mensaje[0] == "user":
            return mensaje[1]
    return ""

def _ckeck_mensaje_ambito(query : str) -> bool:
    if not query.strip():
        return False
    try: 
        retriver = create_retriever()
        docs = retriver.get_relevant_documents(query, top_k=MIN_DOCS_RELEVANTES)
        return len(docs) >= MIN_DOCS_RELEVANTES
    except Exception: 
        # Si el retriever falla por cualquier motivo, pasamos para no bloquear 
        return True


#Funcion princiapl del supervisor, se encarga de recibir el estado actual y construir una respuesta utilizando el prompt y el llm
def nodo_supervisor(state):
    #Construimos la cadena de procesamiento del supervisor, que incluye el prompt y el llm
    chain = prompt_supervisor | llm
    #con gemini u otro que no sea ollama
    #chain = prompt_supervisor | llm.with_structured_output(Router)
    #Contruimos la respuesta del supervisor, incluyendo los mensajes previos
    response = chain.invoke({
        "mensajes": state["mensajes"]
    })

    #Con gemini esta parte no haría falta porque el modelo ya lo devuelve como un objeto estructurado. 
    raw_content = (response.content or "").strip()
    # Toleramos respuestas con fences ```json ... ``` para evitar caídas por formato.
    if raw_content.startswith("```"):
        lines = raw_content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_content = "\n".join(lines).strip()

    try:
        data = json.loads(raw_content)
    except Exception:
        raise ValueError(f"Respuesta no válida del LLM: {response.content}")

    # Defaults defensivos para evitar KeyError si falta alguna clave en la salida del LLM.
    data.setdefault("next_agent", "FINISH")
    data.setdefault("enunciado", "")
    data.setdefault("codigo_alumno", "")
    data.setdefault("idioma", "es")
    data.setdefault("respuesta", "")

    next_agent = data.get("next_agent", "FINISH").lower()
    idioma = data.get("idioma", "es")

    #Si el supervisor decide delegar a un agente, comprobamos que la pregunta este en el contexto 
    if next_agent in AGENTES_EDUCATIVOS:
        query = data.get("enunciado") or data.get("codigo_alumno") or _ultimo_mensaje_usuario(state)
        if not _ckeck_mensaje_ambito(query):
            respuestas_fuera_ambito = {
                "es": "Lo siento, no tengo información sobre ese tema en el material de la asignatura. Solo puedo ayudarte con los contenidos de Introducción a la Programación. ¿Tienes alguna duda sobre los temas de la asignatura?",
                "en": "Sorry, I don't have information about that topic in the course material. I can only help you with the contents of Introduction to Programming. Do you have any questions about the course topics?",
            }
            return {
                "next": "FINISH",
                "respuesta_supervisor": respuestas_fuera_ambito.get(
                    idioma,
                    respuestas_fuera_ambito["es"]
                ),
                "idioma": idioma,
            }

    #Devolvemos la respuesta del supervisor, que incluye el siguiente agente a ejecutar o FINISH si el workflow ha terminado
    #Tambien extraemos el enunciado y el codigo del alumno si los hay en el mensaje
    result = {
        "next": data["next_agent"].lower() if data["next_agent"] != "FINISH" else "FINISH",
        "idioma": idioma,
        "respuesta_supervisor": "",
    }

    #definimos el enunciado y el codigo del alumno en el estado (con gemini se usa directamente response)
    if data.get("enunciado"):
        result["enunciado"] = data["enunciado"]
    if data.get("codigo_alumno"):
        result["codigo_alumno"] = data["codigo_alumno"]

    # Si el supervisor responde directamente (FINISH con respuesta), guardamos la respuesta en el estado
    respuesta_directa = data.get("respuesta", "").strip()
    if respuesta_directa:
        result["respuesta_supervisor"] = respuesta_directa
    return result
