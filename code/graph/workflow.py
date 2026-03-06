
import os
from agents.supervisor import nodo_supervisor
from .state import AgentState
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.constants import END
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from agents.agentType import AgentType
from agents.educador import EducadorAgent
from agents.demostrador import DemostradorAgent
from agents.critico import CriticoAgent
from agents.evaluador import EvaluadorAgent
from database.repository import guardar_progreso



#Cargamos las variables de entorno
load_dotenv(find_dotenv())

#inicializamos el llm que vamos a usar en este caso llama-3.3-70b-versatilede  groq
#llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

#PODEMOS UTILIZAR TAMB EL GEMINI 3.1 Flash Lite DE GOOGLE
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"), google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0)

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
            AgentType.EDUCADOR.value: AgentType.EDUCADOR.value,
            AgentType.DEMOSTRADOR.value: AgentType.DEMOSTRADOR.value,
            AgentType.CRITICO.value: AgentType.CRITICO.value,
            AgentType.EVALUADOR.value: AgentType.EVALUADOR.value,
            "FINISH": END
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