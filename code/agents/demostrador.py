from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts.demostrador_prompts import (
    AGENTE_DEMOSTRADOR_PROMPT_ES_DIRECTO,
    AGENTE_DEMOSTRADOR_PROMPT_ES_TRAS_EDUCADOR,
    AGENTE_DEMOSTRADOR_PROMPT_EN_DIRECTO,
    AGENTE_DEMOSTRADOR_PROMPT_EN_TRAS_EDUCADOR,
)


# Substrings distintivos del fallback del demostrador. Solo se filtran cuando venimos
# tras el educador (para que no se concatene al mensaje del educador). Cuando el usuario
# pide directamente al demostrador, el fallback es la respuesta correcta y debe llegar.
_FALLBACK_MARKERS_DEMOSTRADOR = (
    "no tengo informaci",            # ES
    "corresponde a otro agente",     # ES
    "i don't have information",      # EN
    "corresponds to another agent",  # EN
)

# Substrings del fallback del educador ("no tengo informacion sobre ese tema en los
# materiales..."). Si el educador disparo su fallback, no tiene sentido que el demostrador
# entre detras inventando un ejemplo (queda incoherente para el alumno).
_FALLBACK_MARKERS_EDUCADOR = (
    "no tengo informaci",       # ES
    "i don't have information", # EN
)


def _educador_disparo_fallback(mensajes) -> bool:
    """True si el ultimo AIMessage (el del educador) es el fallback de 'no tengo informacion'."""
    if not mensajes:
        return False
    ultimo = mensajes[-1]
    if not isinstance(ultimo, AIMessage):
        return False
    contenido = ultimo.content
    if isinstance(contenido, list):
        contenido = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in contenido)
    if not isinstance(contenido, str):
        return False
    lower = contenido.lower()
    return any(marker in lower for marker in _FALLBACK_MARKERS_EDUCADOR)


class DemostradorAgent:

    def __init__(self, llm):
        # Inicializamos el agente con el prompt especifico y el llm
        self.llm = llm

    #Definimos una funcion para seleccionar el prompt segun el idioma y el modo (directo / tras educador).
    def _get_prompt(self, idioma, tras_educador):
        """Selecciona el prompt en el idioma del usuario y el modo de invocacion."""
        if tras_educador:
            prompt_text = (
                AGENTE_DEMOSTRADOR_PROMPT_EN_TRAS_EDUCADOR
                if idioma == "en"
                else AGENTE_DEMOSTRADOR_PROMPT_ES_TRAS_EDUCADOR
            )
        else:
            prompt_text = (
                AGENTE_DEMOSTRADOR_PROMPT_EN_DIRECTO
                if idioma == "en"
                else AGENTE_DEMOSTRADOR_PROMPT_ES_DIRECTO
            )
        return ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            MessagesPlaceholder(variable_name="mensajes"),
        ])

    #Funcion principal del agente, se encarga de recibir el estado actural y construir una respuesta utilizando el prompt y el llm
    def run(self, state):
        #Detectamos si venimos tras otro agente (educador): el ultimo mensaje del state es un AIMessage.
        #Si es HumanMessage (o tuple del user), el demostrador es el primero en responder este turno.
        mensajes = state.get("mensajes", [])
        tras_educador = bool(mensajes) and isinstance(mensajes[-1], AIMessage)

        #Si venimos tras el educador y este disparo su propio fallback de "no tengo informacion",
        #no llamamos al LLM ni emitimos nada: el alumno solo veria el mensaje del educador, evitando
        #la incoherencia de que el demostrador invente un ejemplo cuando el educador acaba de decir
        #que no tiene material.
        if tras_educador and _educador_disparo_fallback(mensajes):
            return {}

        #Seleccionamos el prompt en el idioma del usuario y el modo
        prompt = self._get_prompt(state.get("idioma", "es"), tras_educador)
        #Construimos la cadena de procesamiento del agente, que incluye el prompt y el llm
        chain = prompt | self.llm
        #Contruimos la respuesta del agente, incluyendo los mensajes previos, el nivel del usuario y el contexto relevante
        response = chain.invoke({
            "mensajes": mensajes[-6:],
            #coge el nivel del usuario del estado, si no esta definido se asume que es principiante
            "user_level": state.get("user_level", "principiante"),
            #coge el concepto a ilustrar del estado, si no esta definido se asume que no hay un concepto específico
            "concepto": state.get("concepto", "No disponible"),
            #coge el contexto del estado, si no esta definido se asume que no hay contexto relevante
            "contexto": state.get("contexto", "No disponible"),
            "asignatura": state.get("asignatura", "Introduccion_programacion"),
        })
        #Solo cuando venimos tras el educador filtramos el fallback (para no concatenar texto
        #raro al educador). En modo directo el fallback es la respuesta legitima al alumno.
        contenido = response.content
        if tras_educador and isinstance(contenido, str):
            lower = contenido.lower()
            if any(marker in lower for marker in _FALLBACK_MARKERS_DEMOSTRADOR):
                return {}

        #Devolvemos la respuesta del agente, incluyendo tanto los mensajes generados como las demostraciones.
        return {
            "mensajes": [response],
            "demostraciones": contenido
        }
