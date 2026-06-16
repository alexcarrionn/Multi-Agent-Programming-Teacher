
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages 
#En esta clase se define el estado del agente, que incluye los mensajes que se le han pasado, 
# información sobre el usuario, contexto RAG, respuestas de los posibles agentes, 
# información sobre la tarea actual y control de flujo entre agentes.

class AgentState(TypedDict):

    # Mensajes que se le ha pasado al agente. 
    mensajes: Annotated[List[BaseMessage], add_messages]
    next: str

    #Respuesta directa del supervisor. 
    respuesta_supervisor: Optional[str]

    #informacion acerca del usuario
    user_level: Optional[str]
    alumno_id: Optional[int]
    idioma: Optional[str]

    #Contexto RAG
    contexto: Optional[str]

    #Respuestas de los posibles agentes.
    explicaciones: Optional[str]
    demostraciones: Optional[str]
    feedback: Optional[str]
    puntuacion: Optional[float]

    #Informacion contexto de la tarea actual
    intencion: Optional[str]
    concepto: Optional[str]
    codigo_alumno: Optional[str]
    enunciado: Optional[str]
    pedir_demostracion: Optional[bool]

    #Flag que el educador setea cuando el alumno ha pedido una pregunta de autoevaluacion.
    #Si esta a True, el workflow salta al final tras el educador sin pasar por el demostrador
    skip_demostrador: Optional[bool]

    #Flag que el evaluador setea cuando rechaza el codigo. Si esta a True, el workflow salta al
    #final tras el evaluador SIN pasar por el critico.
    fuera_de_ambito: Optional[bool]

    #Informacion acerca del nivel del alumno
    cambio_nivel: Optional[bool]
    nuevo_nivel: Optional[str]
    justificacion_cambio_nivel: Optional[str]

    #asignatura que el usuario está cursando
    asignatura: Optional[str]

    #Ponemos el tipo de asignatura para poder adaptar los agentes a cada una de ellas, por ejemplo, si es una asignatura de programacion, el agente critico se centrara en el codigo del alumno, si es una asignatura de usos, el agente critico se centrara en las respuestas del alumno, etc.
    tipo_asignatura: Optional[str]



