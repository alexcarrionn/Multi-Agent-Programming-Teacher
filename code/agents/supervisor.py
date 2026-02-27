from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_groq import ChatGroq
from agentType import AgentType


#definimos nuestro llm
llm = ChatGroq(model="llama3-70b-8192", temperature=0)


# Miembros del equipo
miembros = [AgentType.EDUCADOR.value, AgentType.DEMOSTRADOR.value, AgentType.EVALUADOR.value, AgentType.CRITICO.value]

# Prompt del supervisor
prompt_supervisor = ChatPromptTemplate.from_messages([
    ("system", "Eres un supervisor a cargo de gestionar una conversación entre los siguientes trabajadores: {members}. "
               "Dada la petición del usuario, decide qué trabajador debe actuar a continuación. "
               "Cada trabajador realizará una tarea y responderá con sus resultados. "
               "Cuando el equipo haya terminado, responde con FINISH."),
    MessagesPlaceholder(variable_name="messages"),
    ("system", "Dado el historial de conversaciones, ¿quién debería actuar a continuación? "
               "O, si ha terminado, responde FINISH. "
               "Selecciona uno de: {members}."),
]).partial(members=", ".join(miembros))

# Definir el agente supervisor
def nodo_supervisor(state):
    llm_con_herramientas = llm.bind_functions([
        {"next": member, "description": f"Llamar al {member}"} for member in miembros
    ])
    chain = prompt_supervisor | llm_con_herramientas | JsonOutputFunctionsParser()
    return chain.invoke(state)

