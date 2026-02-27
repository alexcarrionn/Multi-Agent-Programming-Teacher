from .state import AgentState
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.constants import END
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from prompts.demostrador_prompts import AGENTE_DEMOSTRADOR_PROMPT
from prompts.critico_prompts import AGENTE_CRITICO_PROMPT
from prompts.evaluador_prompts import AGENTE_EVALUADOR_PROMPT
from agents.agentType import AgentType
from agents.educador import EducadorAgent



#Cargamos las variables de entorno
load_dotenv(find_dotenv())

#inicializamos el llm que vamos a usar en este caso llama3-70b-8192 de  groq
llm = ChatGroq(model="llama3-70b-8192", temperature=0)

#definimos cada uno de los agentes que van a participar en el workflow, cada uno con su propio prompt
def demostrador(state: AgentState) :
    messages = [SystemMessage(content = AGENTE_DEMOSTRADOR_PROMPT)] + state["mensajes"]
    response = llm.invoke(messages)
    return {"mensajes": [response]}
    
def critico(state: AgentState) :
    messages = [[SystemMessage(content=AGENTE_CRITICO_PROMPT)] + state["mensajes"]]
    response = llm.invoke(messages)
    return {"mensajes": [response]}
    
def evaluador(state: AgentState) :
    messages = [[SystemMessage(content=AGENTE_EVALUADOR_PROMPT)] + state["mensajes"]]
    response = llm.invoke(messages)
    return {"mensajes": [response]}
    
def supervisor(state: AgentState) :
    return {"mensajes": [llm.invoke(state["mensajes"])]}

#Funcion auxiliar que permite que el agente supervisor decida cual es el siguiente agente.
def supervisor_siguiente(state: AgentState) -> str: 
    intencion = state.get("intencion", "")
    if intencion == "aprender":
        return AgentType.EDUCADOR.value
    elif intencion == "ver ejemplo":
        return AgentType.DEMOSTRADOR.value
    elif intencion == "recibir feedback":
        return AgentType.CRITICO.value
    elif intencion == "evaluar mi código":
        return AgentType.EVALUADOR.value
    else:
        return END

def _build_graph():    
    """Construye y compila el grafo de estados del workflow."""
    #Creamos el grafo de estados del workflow
    graph_builder  = StateGraph(AgentState)
    #agregamos todos los agentes al grafo de estados, cada uno con su propio nodo
    educador_agent = EducadorAgent(llm)


    graph_builder.add_node(AgentType.SUPERVISOR.value, supervisor)
    graph_builder.add_node(AgentType.EDUCADOR.value, educador_agent.run)
    graph_builder.add_node(AgentType.DEMOSTRADOR.value, demostrador)
    graph_builder.add_node(AgentType.CRITICO.value, critico)
    graph_builder.add_node(AgentType.EVALUADOR.value, evaluador)

    """Establecemos el punto de entrada del workflow, en este caso el supervisor es el encargado de recibir el mensaje del usuario y 
    ecidir a que agente enviar el mensaje dependiendo de lo que quiera hacer el usuario"""

    graph_builder.set_entry_point(AgentType.SUPERVISOR.value)

    #conectamos los nodos entre si, estableciendo el flujo de trabajo
    #el supervisor gracias a esto podra decidir a que agente enviar el mensaje del usuario segun la intencion que tenga
    graph_builder.add_conditional_edges(AgentType.SUPERVISOR.value, supervisor_siguiente,
                                        {AgentType.EDUCADOR.value: AgentType.EDUCADOR.value, 
                                        AgentType.DEMOSTRADOR.value: AgentType.DEMOSTRADOR.value, 
                                        AgentType.CRITICO.value: AgentType.CRITICO.value, 
                                        AgentType.EVALUADOR.value: AgentType.EVALUADOR.value,
                                            END: END})
    #educador puede pedirle un ejemplo al demostrador y ya salir 
    graph_builder.add_edge(AgentType.EDUCADOR.value, AgentType.DEMOSTRADOR.value)
    graph_builder.add_edge(AgentType.DEMOSTRADOR.value, END)

    #el critico puede pedirle al evaluador que evalúe el código del alumno y salir
    graph_builder.add_edge(AgentType.CRITICO.value, AgentType.EVALUADOR.value)
    graph_builder.add_edge(AgentType.EVALUADOR.value, END)
    
    #añadimos memoria al grafo para que los agentes puedan recordar las interacciones anteriores
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    return graph

# Construimos el grafo a nivel de módulo para que esté disponible en stream_graph_updates
graph = _build_graph()

# Funcion para ejecutar el workflow y mostrar las actualizaciones en tiempo real
def stream_graph_updates(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    events = graph.stream(
        {"mensajes": [("user", user_input)]}, config, stream_mode="values"
    )
    for event in events:
        message = event["mensajes"][-1]
        message.pretty_print()