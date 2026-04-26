from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts.educador_prompts import AGENTE_EDUCADOR_PROMPT_ES, AGENTE_EDUCADOR_PROMPT_EN

class EducadorAgent:

    def __init__(self, llm):
        # Inicializamos el agente con el prompt especifico y el llm
        self.llm = llm

    def _get_prompt(self, idioma):
        """Selecciona el prompt en el idioma del usuario."""
        prompt_text = AGENTE_EDUCADOR_PROMPT_EN if idioma == "en" else AGENTE_EDUCADOR_PROMPT_ES
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
            #coge el contexto del estado, si no esta definido se asume que no hay contexto relevante
            "contexto": state.get("contexto", "No disponible"),
            "asignatura": state.get("asignatura", "Introduccion_programacion"),
        })
        #Devolvemos la respuesta del agente, incluyendo tanto los mensajes generados como las explicaciones que el agente considere relevantes para el usuario.
        return {
            "mensajes": [response],
            "explicaciones": response.content
        } 