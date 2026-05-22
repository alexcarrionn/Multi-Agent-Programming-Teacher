def get_prompt(agente: str, tipo: str, idioma: str, modo: str | None = None) -> str:
      # importa dinámicamente prompts.<tipo>.<agente>_prompts
    try:
        module = __import__(f"prompts.{tipo}.{agente}_prompts", fromlist=[''])
    except ImportError as e:
        raise ImportError(f"No se pudo importar el módulo para el agente '{agente}', tipo '{tipo}'. Detalles: {e}")
      # devuelve la constante AGENTE_<AGENTE>_PROMPT_<IDIOMA>[_<MODO>]
    prompt_name = f"AGENTE_{agente.upper()}_PROMPT_{idioma.upper()}"
    if modo:
        prompt_name += f"_{modo.upper()}"
    try:
        return getattr(module, prompt_name)
    except AttributeError:
        raise AttributeError(f"No se encontró la constante '{prompt_name}' en el módulo '{module.__name__}'")