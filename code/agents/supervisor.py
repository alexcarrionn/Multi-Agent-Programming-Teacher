import json
import re
#from langchain_groq import ChatGroq
from agents.agentType import AgentType
from typing import Literal
from rag.retriever import create_retriever
from prompts.supervisor_prompts import AGENTE_SUPERVISOR_PROMPT
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

#Definimos el LLM según el proveedor configurado
if settings.LLM_MODEL.startswith("gemini"):
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.LLM_API_KEY,
        temperature=0,
        request_timeout=120,
        max_tokens=1024,
    )
elif settings.LLM_MODEL.startswith("gpt"):
    llm = ChatOpenAI(
        model=settings.LLM_MODEL.replace("gpt-oss/", ""),
        base_url=settings.LLM_URL,
        api_key=settings.LLM_API_KEY,
        temperature=0.2,
        request_timeout=120,
        max_tokens=1024,
        frequency_penalty=0.3,
    )

#llm = ChatGroq(model=settings.LLM_MODEL, temperature=0, request_timeout=60)
else:
    raise ValueError(f"Modelo no soportado en supervisor: {settings.LLM_MODEL}")

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

def _ckeck_mensaje_ambito(query: str) -> bool:
    if not query.strip():
        return False
    try:
        retriver = create_retriever(top_k=MIN_DOCS_RELEVANTES)
        docs = retriver.invoke(query)
        return len(docs) >= MIN_DOCS_RELEVANTES
    except Exception:
        # Si el retriever falla por cualquier motivo, pasamos para no bloquear
        return True


def _parse_supervisor_response(text: str) -> dict | None:
    """Extrae el dict JSON de la respuesta del LLM, tolerando fences y texto alrededor."""
    text = text.strip()

    # 1. Quitar fences ```json ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 2. Intento directo
    try:
        return json.loads(text)
    except Exception:
        pass

    # 3. Buscar el primer bloque {...} en el texto (el modelo puede añadir texto antes/después)
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None


def _normalizar(texto: str) -> str:
    """Elimina tildes para comparaciones robustas en español."""
    replacements = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"}
    for acentuada, simple in replacements.items():
        texto = texto.replace(acentuada, simple)
    return texto


def _fallback_routing(user_message: str) -> dict:
    """Fallback cuando el LLM no genera JSON válido: usa heurísticas sobre el texto del usuario."""
    msg = _normalizar(user_message.lower())
    if any(w in msg for w in ["ejemplo", "muestrame", "muestra", "show", "example", "demuestra"]):
        next_agent = "demostrador"
    elif any(w in msg for w in ["evalua", "califica", "nota", "puntuacion", "evaluate", "grade"]):
        next_agent = "evaluador"
    elif any(w in msg for w in ["feedback", "mejora", "critica", "revisa", "fallo", "error", "review", "que esta mal", "que falla"]):
        next_agent = "critico"
    elif any(w in msg for w in ["hola", "buenas", "hello", "gracias", "adios", "bye", "thanks"]):
        next_agent = "FINISH"
    else:
        next_agent = "educador"

    return {
        "next_agent": next_agent,
        "enunciado": "",
        "codigo_alumno": "",
        "idioma": "es",
        "respuesta": "",
    }


#Funcion principal del supervisor, se encarga de recibir el estado actual y construir una respuesta utilizando el prompt y el llm
def nodo_supervisor(state):
    chain = prompt_supervisor | llm
    response = chain.invoke({
        "mensajes": state["mensajes"][-6:],
    })

    raw_content = response.content or ""

    # Intentar parsear la respuesta del LLM como JSON
    data = _parse_supervisor_response(raw_content)

    # Si el modelo ignoró el formato JSON, usar heurística sobre el último mensaje del usuario
    if data is None:
        data = _fallback_routing(_ultimo_mensaje_usuario(state))

    # Defaults defensivos por si algún campo quedó vacío.
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

    # Siempre escribimos enunciado y codigo_alumno para limpiar valores de turnos anteriores
    result["enunciado"] = data.get("enunciado", "")
    result["codigo_alumno"] = data.get("codigo_alumno", "")

    # Si el supervisor responde directamente (FINISH con respuesta), guardamos la respuesta en el estado
    respuesta_directa = data.get("respuesta", "").strip()
    if respuesta_directa:
        result["respuesta_supervisor"] = respuesta_directa
    return result
