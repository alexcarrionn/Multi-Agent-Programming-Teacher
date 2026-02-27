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
from agents.agentType import AgentType
import pandas as pd
from langchain.agents import create_pandas_dataframe_agent
from database.repository import register_alumno, authenticate_alumno


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
        return AgentType.EDUCADOR.value
    elif intencion == "ver ejemplo":
        return AgentType.DEMOSTRADOR.value
    elif intencion == "recibir feedback":
        return AgentType.CRITICO.value
    elif intencion == "evaluar mi código":
        return AgentType.EVALUADOR.value
    else:
        return END
    
#Creamos el grafo de estados del workflow
graph_builder  = StateGraph(AgentState)
#agregamos todos los agentes al grafo de estados, cada uno con su propio nodo
graph_builder.add_node(AgentType.SUPERVISOR.value, supervisor)
graph_builder.add_node(AgentType.EDUCADOR.value, educador)
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


# Funcion para ejecutar el workflow y mostrar las actualizaciones en tiempo real
def stream_graph_updates(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    events = graph.stream(
        {"mensajes": [("user", user_input)]}, config, stream_mode="values"
    )
    for event in events:
        message = event["mensajes"][-1]
        message.pretty_print()

#Funcion en la que el agente supervisor va a comprobar que el email introducido por el alumno esta en el excel que el docente ha proporcionado con los alumnos autorizados para usar el agente docente, si el email no esta en ese excel el alumno no podra registrarse ni iniciar sesion
def comprobacion_email(email: str) -> bool:
    df = pd.read_excel("alumnos_autorizados.xlsx")
    #Creamos el agente de Pandas 
    agent = create_pandas_dataframe_agent(llm, df, verbose=True, allow_dangerous_code=True)
    #Hacemos que el agente busque el email introducido por el alumno en la columna de correos del excel
    response = agent.run(f"¿Está el correo {email} en la columna de correos del excel?")
    if "sí" in response.lower():
        return True
    return False


#Definimos una funcion en la que se registre un usuario
def registrar_alumno():
    email = input("Introduce tu correo: ")
    #Primero comprobamos que el email es de la um 
    if not email.endswith("@um.es"):
        print("Error: el correo introducido no es válido. Por favor, introduce un correo de la Universidad de Murcia (terminado en @um.es).\n")
        return
    #Comprobamos que el email este en el excel puesto por el docente
    comprobacion = comprobacion_email(email)
    if not comprobacion:
        print("Error: el correo introducido no está autorizado para registrarse. Por favor, contacta con tu docente para obtener acceso.\n")
        return
    else: 
        password = input("Introduce tu contraseña: ")
        nombre = input("Introduce tu nombre: ")
        nivel = input("Introduce tu nivel (principiante, intermedio, avanzado): ")
        # Registramos al alumno en la base de datos MySQL
        try:
            register_alumno(email, password, nombre, nivel)
            print("Registro completado con éxito.")
        except ValueError as e:
            print(f"Error en el registro: {e}")


#Funcion principal para ejecutar el workflow del agente docente
if __name__ == "__main__":
    from database.repository import authenticate_alumno
    #Bucle para poder identificar al usuario
    while True:
        user_input = input("Bienvenido al agente docente. Escribe 'iniciar sesion' para comenzar o 'registrarse' para poder crear una cuenta (o 'salir' para salir): ")
        if user_input.lower() == "salir":
            print("Saliendo del agente docente. ¡Hasta luego!")
            break
        elif user_input.lower() == "registrarse":
           registrar_alumno()
        elif user_input.lower() == "iniciar sesion":
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
        else: 
            print("Opción no válida. Por favor, escribe 'iniciar sesion', 'registrarse' o 'salir'.\n")



