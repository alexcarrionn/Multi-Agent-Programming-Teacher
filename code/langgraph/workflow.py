from .state import AgentState
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.constants import END
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from prompts.educador_prompts import AGENTE_EDUCADOR_PROMPT
from prompts.demostrador_prompts import AGENTE_DEMOSTRADOR_PROMPT
from prompts.critico_prompts import AGENTE_CRITICO_PROMPT
from prompts.evaluador_prompts import AGENTE_EVALUADOR_PROMPT


#Cargamos las variables de entorno
load_dotenv(find_dotenv())

#inicializamos el llm que vamos a usar en este caso llama3-70b-8192 de  groq
llm = ChatGroq(model="llama3-70b-8192", temperature=0)

#definimos cada uno de los agentes que van a participar en el workflow, cada uno con su propio prompt
#con ek systen=m message mas el contexto hacemos que los agentes tengan el contexto de la conversacion y no solo el ultimo mensaje del usuario
def educador(state: AgentState) : 
    messages = [[SystemMessage(content=AGENTE_EDUCADOR_PROMPT)] + state["mensajes"]]
    response = llm.invoke(messages)
    return {"mensajes": [response]}
    
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
        return "educador"
    elif intencion == "ver ejemplo":
        return "demostrador"
    elif intencion == "recibir feedback":
        return "critico"
    elif intencion == "evaluar mi código":
        return "evaluador"
    else:
        return END
    
#Creamos el grafo de estados del workflow
graph_builder  = StateGraph(AgentState)
#agregamos todos los agentes al grafo de estados, cada uno con su propio nodo
graph_builder.add_node("supervisor", supervisor)
graph_builder.add_node("educador", educador)
graph_builder.add_node("demostrador", demostrador)
graph_builder.add_node("critico", critico)
graph_builder.add_node("evaluador", evaluador)

"""Establecemos el punto de entrada del workflow, en este caso el supervisor es el encargado de recibir el mensaje del usuario y 
ecidir a que agente enviar el mensaje dependiendo de lo que quiera hacer el usuario"""

graph_builder.set_entry_point("supervisor")

#conectamos los nodos entre si, estableciendo el flujo de trabajo
#el supervisor gracias a esto podra decidir a que agente enviar el mensaje del usuario segun la intencion que tenga
graph_builder.add_conditional_edges("supervisor", supervisor_siguiente,
                                     {"educador": "educador", 
                                      "demostrador": "demostrador", 
                                      "critico": "critico", 
                                      "evaluador": "evaluador",
                                        END: END})
#educador puede pedirle un ejemplo al demostrador y ya salir 
graph_builder.add_edge("educador", "demostrador")
graph_builder.add_edge("demostrador", END)

#el critico puede pedirle al evaluador que evalúe el código del alumno y salir
graph_builder.add_edge("critico", "evaluador")
graph_builder.add_edge("evaluador", END)

#añadimos memoria al grafo para que los agentes puedan recordar las interacciones anteriores
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)


# Funcion para ejecutar el workflow y mostrar las actualizaciones en tiempo real
def stream_graph_updates(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    events = graph.stream(
        {"mensajes": [("user", user_input)]}, config, stream_mode="values"
    )
    for event in events:
        message = event["mensajes"][-1]
        message.pretty_print()

#Funcion principal para ejecutar el workflow del agente docente
if __name__ == "__main__":
    from database.repository import authenticate_alumno
    #Bucle para poder identificar al usuario
    while True:
        email = input("Introduce tu correo: ")
        password = input("Introduce tu contraseña: ")

        # Validamos las credenciales contra la base de datos MySQL
        alumno = authenticate_alumno(email, password)
        if alumno is None:
            print("Error: credenciales incorrectas. Inténtalo de nuevo.\n")
            continue

        print(f"Bienvenido, {alumno.nombre} (nivel: {alumno.nivel or 'sin definir'})\n")

        # Usamos el email como thread_id para persistir la conversación por alumno
        thread_id = alumno.email

        # Bucle de conversación para el alumno autenticado
        while True:
            user_input = input("Introduce tu mensaje (o 'salir'): ")
            if user_input.lower() == "salir":
                print("Saliendo del agente docente. ¡Hasta luego!")
                break
            stream_graph_updates(user_input, thread_id)
        break
