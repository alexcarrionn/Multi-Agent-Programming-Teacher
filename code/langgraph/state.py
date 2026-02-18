from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages 
#En esta clase se define el estado del agente, que incluye los mensajes que se le han pasado, información sobre el usuario, contexto RAG, respuestas de los posibles agentes, información sobre la tarea actual y control de flujo entre agentes.
class AgentState(TypedDict):

    # Mensajes que se le ha pasado al agente. 
    mensajes: Annotated[List[BaseMessage], add_messages]

    #inormacion acerca del usuario
    user_id : Optional[str]
    user_level: Optional[str]

    #Contexto RAG
    contexto: Optional[str]

    #Respuestas de los posibles agentes.
    explicaciones: Optional[str]
    ejemplos: Optional[str]
    feedback: Optional[str]
    evaluacion: Optional[str]
    puntuacion: Optional[float]

    #Informacion contexto de la tarea actual
    intencion: Optional[str]
    concepto: Optional[str]
    codigo_alumno: Optional[str]
    enunciado: Optional[str]

    #Control de flujo entre agentes
    agente_actual: Optional[str]
    necesita_demostraciones: Optional[bool]
    necesita_evaluacion: Optional[bool]
    finalizado: Optional[bool]






