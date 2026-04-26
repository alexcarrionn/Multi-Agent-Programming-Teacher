import re
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from prompts.evaluador_prompts import AGENTE_EVALUADOR_PROMPT_ES, AGENTE_EVALUADOR_PROMPT_EN
from database.repository import cambio_nivel

NIVELES_VALIDOS = {
    "principiante": "principiante",
    "intermedio": "intermedio",
    "avanzado": "avanzado",
    "beginner": "beginner",
    "intermediate": "intermediate",
    "advanced": "advanced",
}


class EvaluadorAgent:

    def __init__(self, llm):
        # Inicializamos el agente con el prompt especifico y el llm
        self.llm = llm

    #Definimos una funcion para seleccionar el prompt segun el idioma del usuario. 
    def _get_prompt(self, idioma):
        """Selecciona el prompt en el idioma del usuario."""
        #Si el idioma esta en ingles, seleccionamos el prompt en ingles, si el idioma esta en español seleccionamos el prompt en español, por defecto se selecciona el prompt en español
        prompt_text = AGENTE_EVALUADOR_PROMPT_EN if idioma == "en" else AGENTE_EVALUADOR_PROMPT_ES
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
            #coge el enunciado del estado, si no esta definido se asume que no hay enunciado relevante
            "enunciado": state.get("enunciado", "No disponible"), 
            #coge el codigo del alumno del estado, si no esta definido se asume que no hay codigo disponible
            "codigo_alumno": state.get("codigo_alumno", "No disponible"), 
            #coge el contexto adicional del estado, si no esta definido se asume que no hay contexto adicional relevante
            "contexto": state.get("contexto", "No disponible"),
            "asignatura": state.get("asignatura", "Introduccion_programacion"),
        })
        #Extraemos los metadatos de cambio de nivel con regex para mayor robustez, en esta parte lo que se va a hacer es 
        #Extraer la informacion que no queremos del mensaje y poder saber si el agente ha decidido cambiar el nivel del alumno
        contenido = response.content
        cambio = False
        nuevo_nivel_val = None
        justificacion = None
        #Extraemos la informacion de cambio de nivel utilizando expresiones regulares para buscar patrones específicos en el mensaje del agente
        cambio_match = re.search(r"cambio_nivel\s*:\s*(true|false)", contenido, re.IGNORECASE)
        nivel_match = re.search(r"nuevo_nivel\s*:\s*(.+)", contenido, re.IGNORECASE)
        justificacion_match = re.search(r"justificacion_cambio_nivel\s*:\s*(.+)", contenido, re.IGNORECASE)
        #Comprobamos si el agente ha indicado que se debe realizar el cambio de nivel y si el nuevo nivel es válido
        if cambio_match and cambio_match.group(1).strip().lower() == "true" and nivel_match:
            nivel_raw = nivel_match.group(1).strip().lower().rstrip(".")
            nuevo_nivel_val = NIVELES_VALIDOS.get(nivel_raw)
            #Si el nuevo nivel es valido se cambia en la base de datos
            if nuevo_nivel_val:
                cambio = True
                justificacion = justificacion_match.group(1).strip() if justificacion_match else ""
                cambio_nivel(nuevo_nivel_val, state["alumno_id"])

        #Limpiamos los marcadores de control para que no sean visibles al alumno
        contenido_limpio = re.sub(r"^-?\s*justificacion_cambio_nivel\s*:\s*.+$\n?", "", contenido, flags=re.MULTILINE)
        contenido_limpio = re.sub(r"^-?\s*nuevo_nivel\s*:\s*.+$\n?", "", contenido_limpio, flags=re.MULTILINE)
        contenido_limpio = re.sub(r"^-?\s*cambio_nivel\s*:\s*.+$\n?", "", contenido_limpio, flags=re.MULTILINE)
        contenido_limpio = contenido_limpio.strip()

        #Devolvemos la respuesta limpia y los campos de cambio de nivel para que se actualicen en el estado del grafo
        return {
            "mensajes": [AIMessage(content=contenido_limpio)],
            "puntuacion": contenido_limpio,
            "cambio_nivel": cambio,
            "nuevo_nivel": nuevo_nivel_val,
            "justificacion_cambio_nivel": justificacion,
        } 