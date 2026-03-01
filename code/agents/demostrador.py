from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts.demostrador_prompts import AGENTE_DEMOSTRADOR_PROMPT

class DemostradorAgent:

    def __init__(self, llm):
        # Inicializamos el agente con el prompt especifico y el llm
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", AGENTE_DEMOSTRADOR_PROMPT),
            ("system", "Nivel del alumno: {user_level}"),
            ("system", "Concepto a ilustrar: {concepto}"),
            ("system", "Contexto:\n{contexto}"),
            MessagesPlaceholder(variable_name="mensajes"),
        ])
    #Funcion principal del agente, se encarga de recibir el estado actural y construir una respuesta utilizando el prompt y el llm
    def run(self, state):
        #Construimos la cadena de procesamiento del agente, que incluye el prompt y el llm
        chain = self.prompt | self.llm
        #Contruimos la respuesta del agente, incluyendo los mensajes previos, el nivel del usuario y el contexto relevante
        response = chain.invoke({
            "mensajes": state["mensajes"],
            #coge el nivel del usuario del estado, si no esta definido se asume que es principiante
            "user_level": state.get("user_level", "principiante"),
            #coge el concepto a ilustrar del estado, si no esta definido se asume que no hay un concepto específico
            "concepto": state.get("concepto", "No disponible"),
            #coge el contexto del estado, si no esta definido se asume que no hay contexto relevante
            "contexto": state.get("contexto", "No disponible")
        })
        #Devolvemos la respuesta del agente, incluyendo tanto los mensajes generados como las demostraciones. 
        return {
            "mensajes": [response],
            "demostraciones": response.content
        } 