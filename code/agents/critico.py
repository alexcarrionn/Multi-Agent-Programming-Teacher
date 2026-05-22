from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from prompts import get_prompt

class CriticoAgent:

    def __init__(self, llm):
        # Inicializamos el agente con el prompt especifico y el llm
        self.llm = llm

    def _get_prompt(self, idioma, tipo_asignatura):
        """Selecciona el prompt en el idioma del usuario."""
        prompt_text = get_prompt("critico", tipo_asignatura, idioma)
        return ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            MessagesPlaceholder(variable_name="mensajes"),
        ])
    #Funcion principal del agente, se encarga de recibir el estado actural y construir una respuesta utilizando el prompt y el llm
    def run(self, state):
        #Seleccionamos el prompt en el idioma del usuario
        prompt = self._get_prompt(state.get("idioma", "es"), state.get("tipo_asignatura", "programacion"))
        #Construimos la cadena de procesamiento del agente, que incluye el prompt y el llm
        chain = prompt | self.llm
        #Contruimos la respuesta del agente, incluyendo los mensajes previos, el nivel del usuario y el contexto relevante
        response = chain.invoke({
            "mensajes": state["mensajes"][-6:],
            #coge el nivel del usuario del estado, si no esta definido se asume que es principiante
            "user_level": state.get("user_level", "principiante"),
            #coge el enunciado del estado, si no esta definido se asume que no hay enunciado relevante
            "enunciado": state.get("enunciado", "No disponible"), 
            #coge el codigo del alumno del estado, si no esta definido se asume que no hay codigo disponible
            "codigo_alumno": state.get("codigo_alumno", "No disponible"), 
            #coge el contexto adicional del estado, si no esta definido se asume que no hay contexto adicional relevante
            "contexto": state.get("contexto", "No disponible"),
            "asignatura": state.get("asignatura", "Introduccion_programacion"),
            "tipo_asignatura": state.get("tipo_asignatura", "programacion"),
        })
        #Devolvemos la respuesta del agente, incluyendo tanto los mensajes generados como las explicaciones que el agente considere relevantes para el usuario.
        return {
            "mensajes": [response],
            "feedback": response.content
        } 