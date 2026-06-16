"""Utilidades de historial compartidas por los agentes.

Los agentes deben responder SOLO al mensaje actual del alumno. Pasar la ventana
`state["mensajes"][-6:]` reinyecta en la entrada del LLM las peticiones anteriores
del propio usuario (p. ej. "insultame", "el clima de hoy", "la altura de los
Pirineos"). El modelo las ve y las contesta, haciendo referencia a lo anterior
("no puedo insultarte ni darte el clima... pero X es..."). Pasar solo el ultimo
mensaje del usuario lo elimina de raiz: el modelo no puede referirse a algo que
no esta en su entrada. Es determinista, no depende de que el modelo "obedezca"
el prompt. Mismo patron que ya usa el demostrador (ver demostrador_contexto_limpio).
"""


def ultimo_mensaje_usuario(mensajes):
    """Devuelve [ultimo mensaje del usuario] (lista de 1) o [] si no hay ninguno.

    Soporta tanto objetos BaseMessage (type == "human") como tuplas ("user", texto).
    Se devuelve como lista para encajar directamente en el MessagesPlaceholder.
    """
    for m in reversed(mensajes or []):
        if hasattr(m, "type") and m.type == "human":
            return [m]
        if isinstance(m, tuple) and len(m) >= 2 and m[0] == "user":
            return [m]
    return []
