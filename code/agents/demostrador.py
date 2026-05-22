from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts import get_prompt


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

# Cap defensivo: si el RAG devuelve un contexto enorme, lo truncamos antes de pasarlo al LLM.
_MAX_CONTEXTO_CHARS = 2000


def _ultimo_human_message(mensajes):
    """Devuelve el ultimo mensaje del usuario, o None si no hay."""
    for m in reversed(mensajes):
        if hasattr(m, "type") and m.type == "human":
            return m
        if isinstance(m, tuple) and len(m) >= 2 and m[0] == "user":
            return m
    return None


def _mensajes_para_demostrador(mensajes, tras_educador):
    """Construye el contexto minimo para el demostrador: ultimo mensaje del usuario y,
    si encadena tras el educador, su explicacion del turno actual.
    """
    if not mensajes:
        return []
    ultimo_human = _ultimo_human_message(mensajes)
    if tras_educador:
        #mensajes[-1] es el AIMessage que acaba de generar el educador en este turno
        return [m for m in (ultimo_human, mensajes[-1]) if m is not None]
    return [ultimo_human] if ultimo_human is not None else []


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
    def _get_prompt(self, idioma, tipo, tras_educador):
        modo = "tras_educador" if tras_educador else "directo"
        prompt_text = get_prompt("demostrador", tipo, idioma, modo=modo)
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
        prompt = self._get_prompt(state.get("idioma", "es"), state.get("tipo_asignatura", "programacion"), tras_educador)
        #Construimos la cadena de procesamiento del agente, que incluye el prompt y el llm
        chain = prompt | self.llm
        #Contruimos la respuesta del agente, incluyendo los mensajes previos, el nivel del usuario y el contexto relevante
        response = chain.invoke({
            "mensajes": _mensajes_para_demostrador(mensajes, tras_educador),
            #coge el nivel del usuario del estado, si no esta definido se asume que es principiante
            "user_level": state.get("user_level", "principiante"),
            #coge el concepto a ilustrar del estado, si no esta definido se asume que no hay un concepto específico
            "concepto": state.get("concepto", "No disponible"),
            #coge el contexto del estado, truncado a _MAX_CONTEXTO_CHARS para evitar saturar al LLM
            "contexto": (state.get("contexto") or "No disponible")[:_MAX_CONTEXTO_CHARS],
            "asignatura": state.get("asignatura", "Introduccion_programacion"),
            "tipo_asignatura": state.get("tipo_asignatura", "programacion"),
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
