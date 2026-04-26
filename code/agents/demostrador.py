from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts.demostrador_prompts import AGENTE_DEMOSTRADOR_PROMPT_ES, AGENTE_DEMOSTRADOR_PROMPT_EN


class DemostradorAgent:

    def __init__(self, llm):
        # Inicializamos el agente con el prompt especifico y el llm
        self.llm = llm

    #Definimos una funcion para seleccionar el prompt segun el idioma del usuario. 
    def _get_prompt(self, idioma):
        """Selecciona el prompt en el idioma del usuario."""
         #Si el idioma esta en ingles, seleccionamos el prompt en ingles, si el idioma esta en español seleccionamos el prompt en español, por defecto se selecciona el prompt en español
        prompt_text = AGENTE_DEMOSTRADOR_PROMPT_EN if idioma == "en" else AGENTE_DEMOSTRADOR_PROMPT_ES
        return ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            MessagesPlaceholder(variable_name="mensajes"),
        ])
    
    #Funcion principal del agente, se encarga de recibir el estado actural y construir una respuesta utilizando el prompt y el llm
    def run(self, state):
        #Seleccionamos el prompt en el idioma del usuario
        prompt = self._get_prompt(state.get("idioma", "es"))
        #Construimos la cadena de procesamiento del agente, que incluye el prompt y el llm
        chain = prompt | self.llm
        #Contruimos la respuesta del agente, incluyendo los mensajes previos, el nivel del usuario y el contexto relevante
        response = chain.invoke({
            "mensajes": state["mensajes"][-6:],
            #coge el nivel del usuario del estado, si no esta definido se asume que es principiante
            "user_level": state.get("user_level", "principiante"),
            #coge el concepto a ilustrar del estado, si no esta definido se asume que no hay un concepto específico
            "concepto": state.get("concepto", "No disponible"),
            #coge el contexto del estado, si no esta definido se asume que no hay contexto relevante
            "contexto": state.get("contexto", "No disponible"),
            "asignatura": state.get("asignatura", "Introduccion_programacion"),
        })
        #Devolvemos la respuesta del agente, incluyendo tanto los mensajes generados como las demostraciones. 
        return {
            "mensajes": [response],
            "demostraciones": response.content
        } 