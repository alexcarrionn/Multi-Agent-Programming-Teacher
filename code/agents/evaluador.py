from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts.evaluador_prompts import AGENTE_EVALUADOR_PROMPT

class EvaluadorAgent:

    def __init__(self, llm):
        # Inicializamos el agente con el prompt especifico y el llm
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", AGENTE_EVALUADOR_PROMPT),
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
            #coge el enunciado del estado, si no esta definido se asume que no hay enunciado relevante
            "enunciado": state.get("enunciado", "No disponible"), 
            #coge el codigo del alumno del estado, si no esta definido se asume que no hay codigo disponible
            "codigo_alumno": state.get("codigo_alumno", "No disponible"), 
            #coge el contexto adicional del estado, si no esta definido se asume que no hay contexto adicional relevante
            "contexto": state.get("contexto", "No disponible")
        })
        #Devolvemos la respuesta del agente, incluyendo tanto los mensajes generados como las explicaciones que el agente considere relevantes para el usuario.
        return {
            "mensajes": [response],
            "puntuacion": response.content
        } 