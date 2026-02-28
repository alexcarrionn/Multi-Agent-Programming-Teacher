import os

from langchain_groq import ChatGroq
from agentType import AgentType
from typing import Literal
from typing_extensions import TypedDict
from prompts.supervisor_prompts import AGENTE_SUPERVISOR_PROMPT
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


#definimos nuestro llm
llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)


# Miembros del equipo
miembros = [AgentType.EDUCADOR.value, AgentType.DEMOSTRADOR.value, AgentType.EVALUADOR.value, AgentType.CRITICO.value]

#Definimos el Schema de salida estructurada - el LLM solo puede devolver uno de estos valores 
class Router(TypedDict):
    next_agent: Literal["EDUCADOR", "DEMOSTRADOR", "EVALUADOR", "CRITICO", "FINISH"]

#Definimos el prompt del supervisor, que se encargará de decidir que agente debe actuar 
prompt_supervisor = ChatPromptTemplate.from_messages([
    ("system", AGENTE_SUPERVISOR_PROMPT),
    MessagesPlaceholder(variable_name="mensajes"),
]).partial(members=", ".join(miembros))

#Funcion princiapl del supervisor, se encarga de recibir el estado actual y construir una respuesta utilizando el prompt y el llm
def nodo_supervisor(state):
    #Construimos la cadena de procesamiento del supervisor, que incluye el prompt y el llm
    chain = prompt_supervisor | llm.with_structured_output(Router)
    #Contruimos la respuesta del supervisor, incluyendo los mensajes previos
    response = chain.invoke({
        "mensajes": state["mensajes"]
    })
    #Devolvemos la respuesta del supervisor, que incluye el siguiente agente a ejecutar o FINISH si el workflow ha terminado
    return {
        "next": response["next_agent"]}
