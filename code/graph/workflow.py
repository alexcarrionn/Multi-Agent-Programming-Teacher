
import os
from agents.supervisor import nodo_supervisor
from .state import AgentState
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.constants import END
#from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from agents.agentType import AgentType
from agents.educador import EducadorAgent
from agents.demostrador import DemostradorAgent
from agents.critico import CriticoAgent
from agents.evaluador import EvaluadorAgent
from database.repository import guardar_progreso
from rag.retriever import create_retriever
from config.settings import settings



#Cargamos las variables de entorno
load_dotenv(find_dotenv())

#inicializamos el llm que vamos a usar en este caso llama-3.3-70b-versatilede  groq
#llm = ChatGroq(model=settings.LLM_MODEL, temperature=0)

#PODEMOS UTILIZAR TAMB EL GEMINI 3.1 Flash Lite DE GOOGLE
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.LLM_API_KEY, temperature=0)

#Creamos otro nodo para poder guardar el progreso del alumno en la base de datos MySQL, este nodo se ejecuta despues 
#del ciclo que se ejecuta entre el evaluador y el crítico, de esta forma nos aseguramos de que se guarda el progreso del 
# alumno correctamente. 
def nodo_guardar_progreso(state):
    """Nodo que guarda el progreso del alumno en la base de datos tras la evaluación y crítica."""
    alumno_id = state.get("alumno_id")
    enunciado = state.get("enunciado")
    codigo_alumno = state.get("codigo_alumno")
    puntuacion = state.get("puntuacion")
    feedback = state.get("feedback")
    ambito_dificultad = state.get("user_level")

    if alumno_id:
        guardar_progreso(
            alumno_id=alumno_id,
            enunciado_ejercicio=enunciado,
            codigo_alumno=codigo_alumno,
            puntuacion_ejercicio=puntuacion,
            retroalimentacion_ejercicio=feedback,
            ambito_dificultad=ambito_dificultad
        )
    return {}

def rag_node(state):
    """Nodo que se encarga de gestionar el proceso de RAG para obtener información relevante antes de pasar al agente correspondiente."""
   # Para implementar el nodo RAG empezamos creando el retriver 
    retriever = create_retriever()

    #Ahora obtenemos el contexto relevante para la consulta del usuario utilizando el retriever
    concepto = state.get("concepto", "")
    enunciado = state.get("enunciado", "")
    codigo_alumno = state.get("codigo_alumno", "")
    intencion = state.get("intencion", "")

    #Una vez tenemos toda la información necesaria,. hacemos la consulta al retriever para obtener el contexto relevante
    query = "" 

    #Dependiendo de la intencion del ausuario la query va a ser diferente 
    if concepto: 
        query = concepto
    elif enunciado and codigo_alumno:
        query = f"Enunciado: {enunciado}\nCódigo del alumno: {codigo_alumno}"
    elif enunciado:
        query = enunciado
    else: 
        #Si no es ninguna de las anteriores se coge el ultimo mensaje del usuario como query
        mensajes = state.get("mensajes", [])
        for mensaje in reversed(mensajes):
           #Comprobamos si el mensaje es un mensaje de un humano, en ese caso se coge su contenido como query para el RAG
           if hasattr(mensaje, "type") and mensaje.type == "human":
                query = mensaje.content
                break
           #Si el mensaje no es un mensaje de un humano pero es una tupla, se asume que es un mensaje del usuario
           elif isinstance(mensaje, tuple):
                query = mensaje[1]
                break
    #Una vez tenemos la query, hacemos la consulta al retriever para obtener el contexto relevante
    documentos_relevantes = retriever.invoke(query)

    #Comprobamos que se han obetnidos documentos 
    if not documentos_relevantes:
        return {
            "contexto": "",
        }
    
    #Si se han obtenido documentos relevantes, se concatena su contenido para crear el contexto que se le pasará al agente correspondiente
    contexto = "\n".join([doc.page_content for doc in documentos_relevantes])

    return {
        "contexto": contexto,
    }


def _build_graph():    
    """Construye y compila el grafo de estados del workflow."""
    #Creamos el grafo de estados del workflow
    graph_builder  = StateGraph(AgentState)
    #agregamos todos los agentes al grafo de estados, cada uno con su propio nodo
    educador_agent = EducadorAgent(llm)
    critico_agent = CriticoAgent(llm)
    demostrador_agent = DemostradorAgent(llm)
    evaluador_agent = EvaluadorAgent(llm)

    graph_builder.add_node(AgentType.SUPERVISOR.value, nodo_supervisor)
    graph_builder.add_node(AgentType.EDUCADOR.value, educador_agent.run)
    graph_builder.add_node("rag", rag_node)
    graph_builder.add_node(AgentType.DEMOSTRADOR.value, demostrador_agent.run)
    graph_builder.add_node(AgentType.CRITICO.value, critico_agent.run)
    graph_builder.add_node(AgentType.EVALUADOR.value, evaluador_agent.run)
    graph_builder.add_node("guardar_progreso", nodo_guardar_progreso)

    """Establecemos el punto de entrada del workflow, en este caso el supervisor es el encargado de recibir el mensaje del usuario y 
    ecidir a que agente enviar el mensaje dependiendo de lo que quiera hacer el usuario"""

    graph_builder.set_entry_point(AgentType.SUPERVISOR.value)

    #conectamos los nodos entre si, estableciendo el flujo de trabajo
    #el supervisor gracias a esto podra decidir a que agente enviar el mensaje del usuario segun la intencion que tenga
    graph_builder.add_conditional_edges(
        AgentType.SUPERVISOR.value,
        lambda state: state["next"],
        {
            AgentType.EDUCADOR.value: "rag",
            AgentType.DEMOSTRADOR.value: "rag",
            AgentType.CRITICO.value:"rag",
            AgentType.EVALUADOR.value: "rag",
            "FINISH": END
        }
    )
    #una vez el nodo RAG ha obtenido el contexto relevante, se redirige al agente correspondiente
    graph_builder.add_conditional_edges(
        "rag",
        lambda state: state["next"],
        {
            AgentType.EDUCADOR.value: AgentType.EDUCADOR.value,
            AgentType.DEMOSTRADOR.value: AgentType.DEMOSTRADOR.value,
            AgentType.CRITICO.value: AgentType.CRITICO.value,
            AgentType.EVALUADOR.value: AgentType.EVALUADOR.value,
        }
    )
    #educador puede pedirle un ejemplo al demostrador y ya salir 
    graph_builder.add_edge(AgentType.EDUCADOR.value, AgentType.DEMOSTRADOR.value)
    graph_builder.add_edge(AgentType.DEMOSTRADOR.value, END)

    #el evaluador evalúa el código y pasa al critico, que da feedback, y luego se guarda el progreso
    graph_builder.add_edge(AgentType.EVALUADOR.value, AgentType.CRITICO.value)
    graph_builder.add_edge(AgentType.CRITICO.value, "guardar_progreso")
    graph_builder.add_edge("guardar_progreso", END)
    
    #añadimos memoria al grafo para que los agentes puedan recordar las interacciones anteriores
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    return graph

# Construimos el grafo a nivel de módulo para que esté disponible en stream_graph_updates
graph = _build_graph()

# Funcion para ejecutar el workflow y mostrar las actualizaciones en tiempo real
def stream_graph_updates(user_input: str, thread_id: str, user_level: str, alumno_id: int):
    config = {"configurable": {"thread_id": thread_id}}

    events = graph.stream(
        {"mensajes": [("user", user_input)], "alumno_id": alumno_id, "user_level": user_level}, config, stream_mode="values"
    )
    for event in events:
        message = event["mensajes"][-1]
        message.pretty_print()