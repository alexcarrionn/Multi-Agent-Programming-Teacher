import re
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from prompts import get_prompt
from database.repository import cambio_nivel
from agents.historial import ultimo_mensaje_usuario

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

    #Definimos una funcion para seleccionar el prompt segun el idioma y el tipo de asignatura.
    def _get_prompt(self, idioma, tipo):
        """Selecciona el prompt en el idioma del usuario y el tipo de asignatura."""
        prompt_text = get_prompt("evaluador", tipo, idioma)
        return ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            MessagesPlaceholder(variable_name="mensajes"),
        ])

    #Funcion principal del agente, se encarga de recibir el estado actural y construir una respuesta utilizando el prompt y el llm
    def run(self, state):
        #Seleccionamos el prompt en el idioma del usuario y el tipo de la asignatura activa
        prompt = self._get_prompt(
            state.get("idioma", "es"),
            state.get("tipo_asignatura", "programacion"),
        )
        #Construimos la cadena de procesamiento del agente, que incluye el prompt y el llm
        chain = prompt | self.llm
        #Contruimos la respuesta del agente, incluyendo los mensajes previos, el nivel del usuario y el contexto relevante
        response = chain.invoke({
            #Solo el mensaje actual del alumno (ver agents/historial.py).
            "mensajes": ultimo_mensaje_usuario(state["mensajes"]),
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
        puntuacion_num = None

        #Extraemos la nota numerica del texto. Buscamos el primer patron "X/10" (entero o
        #decimal con punto o coma). Si el LLM ignora la regla y devuelve otra escala
        #(p.ej. "23/25"), no se encontrara match y guardaremos None.
        nota_match = re.search(r"\b(\d+(?:[.,]\d+)?)\s*/\s*10\b", contenido)
        if nota_match:
            try:
                puntuacion_num = float(nota_match.group(1).replace(",", "."))
                #Clamp defensivo por si el LLM saca un "11/10" o algo raro
                if puntuacion_num < 0:
                    puntuacion_num = 0.0
                elif puntuacion_num > 10:
                    puntuacion_num = 10.0
            except ValueError:
                puntuacion_num = None
        #Marcador de control: el evaluador lo emite cuando rechaza sin nota. Lo usa el grafo para saltarse al
        #critico.
        fuera_match = re.search(r"fuera_de_ambito\s*:\s*(true|false)", contenido, re.IGNORECASE)
        fuera_de_ambito = bool(fuera_match and fuera_match.group(1).strip().lower() == "true")

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
        contenido_limpio = re.sub(r"^-?\s*fuera_de_ambito\s*:\s*.+$\n?", "", contenido_limpio, flags=re.MULTILINE)
        contenido_limpio = contenido_limpio.strip()

        #Devolvemos la respuesta limpia y los campos de cambio de nivel para que se actualicen en el estado del grafo.
        #puntuacion guarda el valor numerico (float 0-10) extraido del texto; el texto completo
        #de la evaluacion ya viaja en "mensajes" y se persiste tal cual en "feedback" via el critico.
        return {
            "mensajes": [AIMessage(content=contenido_limpio)],
            "puntuacion": puntuacion_num,
            "cambio_nivel": cambio,
            "nuevo_nivel": nuevo_nivel_val,
            "justificacion_cambio_nivel": justificacion,
            "fuera_de_ambito": fuera_de_ambito,
        }