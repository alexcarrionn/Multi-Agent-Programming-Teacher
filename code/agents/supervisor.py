from langchain_groq import ChatGroq
from agents.agentType import AgentType
from typing import Literal
from typing_extensions import TypedDict
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
llm = ChatOpenAI(model=settings.LLM_MODEL.replace("ollama/", ""), base_url=settings.LLM_URL,api_key=settings.LLM_API_KEY,temperature=0.2)


# Miembros del equipo
miembros = [AgentType.EDUCADOR.value, AgentType.DEMOSTRADOR.value, AgentType.EVALUADOR.value, AgentType.CRITICO.value]

#Definimos el Schema de salida estructurada - el LLM devuelve el agente destino y extrae enunciado/código si los hay
"""
class Router(TypedDict):
    next_agent: Literal["educador", "demostrador", "evaluador", "critico", "FINISH"]
    enunciado: str
    codigo_alumno: str
    idioma: Literal["es", "en"]
 """   
class Router(BaseModel):
    next_agent: Literal["educador", "demostrador", "evaluador", "critico", "FINISH"] = Field(description="El siguiente agente que debe actuar o FINISH.")
    enunciado: str = Field(default="")
    codigo_alumno: str = Field(default="")
    idioma: str = Field(default="es")

#Definimos el prompt del supervisor, que se encargará de decidir que agente debe actuar 
prompt_supervisor = ChatPromptTemplate.from_messages([
    ("system", AGENTE_SUPERVISOR_PROMPT),
    MessagesPlaceholder(variable_name="mensajes"),
]).partial(members=", ".join(miembros))

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
    try: 
        data = json.loads(response.content)
    except:
        raise ValueError(f"Respuesta no válida del LLM: {response.content}")

    #Devolvemos la respuesta del supervisor, que incluye el siguiente agente a ejecutar o FINISH si el workflow ha terminado
    #Tambien extraemos el enunciado y el codigo del alumno si los hay en el mensaje
    result = {
        "next": data["next_agent"].lower() if data["next_agent"] != "FINISH" else "FINISH"
    }

    #definimos el enunciado y el codigo del alumno en el estado (con gemini se usa directamente response)
    if data.get("enunciado"):
        result["enunciado"] = data["enunciado"]
    if data.get("codigo_alumno"):
        result["codigo_alumno"] = data["codigo_alumno"]
    #Detectamos el idioma del mensaje del usuario y lo guardamos en el estado
    result["idioma"] = data.get("idioma", "es")
    return result
