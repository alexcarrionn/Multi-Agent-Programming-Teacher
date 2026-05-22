
import json
import asyncio
from agents.supervisor import nodo_supervisor
from .state import AgentState
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.constants import END
#from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from agents.agentType import AgentType
from agents.educador import EducadorAgent
from agents.demostrador import DemostradorAgent
from agents.critico import CriticoAgent
from agents.evaluador import EvaluadorAgent
from database.repository import guardar_progreso, guardar_interaccion
from rag.retriever import create_retriever
from config.settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage



#Cargamos las variables de entorno
load_dotenv(find_dotenv())

#inicializamos el llm que vamos a usar en este caso llama-3.3-70b-versatilede  groq
#llm = ChatGroq(model=settings.LLM_MODEL, temperature=0)

if settings.LLM_MODEL.startswith("gemini"):
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.LLM_API_KEY,
        temperature=0,
        request_timeout=120,
        max_tokens=1024,
    )
elif settings.LLM_MODEL.startswith("gpt"):
    llm = ChatOpenAI(
        model=settings.LLM_MODEL.replace("gpt-oss/", ""),
        base_url=settings.LLM_URL,
        api_key=settings.LLM_API_KEY,
        temperature=0.2,
        request_timeout=120,
        #gpt-oss consume tokens en reasoning interno (<think>...) que no salen al content.
        #Con 1024 se agotaba todo el budget razonando y devolvia content vacio (ver LangSmith).
        #4096 es el techo razonable; mas alto empieza a dar latencia mala y riesgo OOM en local.
        max_tokens=4096,
        frequency_penalty=0.5,
    )

#Creamos otro nodo para poder guardar el progreso del alumno en la base de datos MySQL, este nodo se ejecuta despues 
#del ciclo que se ejecuta entre el evaluador y el crítico, de esta forma nos aseguramos de que se guarda el progreso del 
# alumno correctamente. 
def nodo_guardar_progreso(state):
    """Nodo que guarda el progreso del alumno en la base de datos tras la evaluación y crítica."""
    alumno_id = state.get("alumno_id")
    enunciado = state.get("enunciado")
    codigo_alumno = state.get("codigo_alumno")
    puntuacion = state.get("puntuacion")
    feedback = state.get("feedback")
    ambito_dificultad = state.get("user_level")
    asignatura = state.get("asignatura")

    if alumno_id:
        #La puntuacion en el state es ahora un float (extraido en el evaluador con regex).
        #La columna SQL es longText, asi que la serializamos a string antes de insertar.
        puntuacion_str = str(puntuacion) if puntuacion is not None else None
        guardar_progreso(
            alumno_id=alumno_id,
            enunciado_ejercicio=enunciado,
            codigo_alumno=codigo_alumno,
            puntuacion_ejercicio=puntuacion_str,
            retroalimentacion_ejercicio=feedback,
            ambito_dificultad=ambito_dificultad,
            asignatura=asignatura
        )
    return {}

def rag_node(state):
    """Nodo que se encarga de gestionar el proceso de RAG para obtener información relevante antes de pasar al agente correspondiente."""
    asignatura = state.get("asignatura")
    retriever = create_retriever(collection_name=asignatura)
    #Ahora obtenemos el contexto relevante para la consulta del usuario utilizando el retriever
    concepto = state.get("concepto", "")
    enunciado = state.get("enunciado", "")
    codigo_alumno = state.get("codigo_alumno", "")

    #Una vez tenemos toda la información necesaria,. hacemos la consulta al retriever para obtener el contexto relevante
    query = "" 

    #Dependiendo de la intencion del ausuario la query va a ser diferente 
    if concepto: 
        query = concepto
    elif enunciado and codigo_alumno:
        query = f"Enunciado: {enunciado}\nCódigo del alumno: {codigo_alumno}"
    elif enunciado:
        query = enunciado
    else: 
        #Si no es ninguna de las anteriores se coge el ultimo mensaje del usuario como query
        mensajes = state.get("mensajes", [])
        for mensaje in reversed(mensajes):
           #Comprobamos si el mensaje es un mensaje de un humano, en ese caso se coge su contenido como query para el RAG
           if hasattr(mensaje, "type") and mensaje.type == "human":
                query = mensaje.content
                break
           #Si el mensaje no es un mensaje de un humano pero es una tupla, se asume que es un mensaje del usuario
           elif isinstance(mensaje, tuple):
                query = mensaje[1]
                break
    #Una vez tenemos la query, hacemos la consulta al retriever para obtener el contexto relevante
    documentos_relevantes = retriever.invoke(query)

    #Comprobamos que se han obetnidos documentos 
    if not documentos_relevantes:
        return {
            "contexto": "",
        }
    
    #Si se han obtenido documentos relevantes, se concatena su contenido para crear el contexto que se le pasará al agente correspondiente
    contexto = "\n".join([doc.page_content for doc in documentos_relevantes])

    return {
        "contexto": contexto,
    }


def _build_graph():
    """Construye y compila el grafo de estados del workflow."""
    #Creamos el grafo de estados del workflow
    graph_builder  = StateGraph(AgentState)
    #agregamos todos los agentes al grafo de estados, cada uno con su propio nodo
    educador_agent = EducadorAgent(llm)
    critico_agent = CriticoAgent(llm)
    demostrador_agent = DemostradorAgent(llm)
    evaluador_agent = EvaluadorAgent(llm)

    graph_builder.add_node(AgentType.SUPERVISOR.value, nodo_supervisor)
    graph_builder.add_node(AgentType.EDUCADOR.value, educador_agent.run)
    graph_builder.add_node("rag", rag_node)
    graph_builder.add_node(AgentType.DEMOSTRADOR.value, demostrador_agent.run)
    graph_builder.add_node(AgentType.CRITICO.value, critico_agent.run)
    graph_builder.add_node(AgentType.EVALUADOR.value, evaluador_agent.run)
    graph_builder.add_node("guardar_progreso", nodo_guardar_progreso)

    """Establecemos el punto de entrada del workflow, en este caso el supervisor es el encargado de recibir el mensaje del usuario y 
    ecidir a que agente enviar el mensaje dependiendo de lo que quiera hacer el usuario"""

    graph_builder.set_entry_point(AgentType.SUPERVISOR.value)

    #conectamos los nodos entre si, estableciendo el flujo de trabajo
    #el supervisor gracias a esto podra decidir a que agente enviar el mensaje del usuario segun la intencion que tenga
    graph_builder.add_conditional_edges(
        AgentType.SUPERVISOR.value,
        lambda state: state["next"],
        {
            AgentType.EDUCADOR.value: "rag",
            AgentType.DEMOSTRADOR.value: "rag",
            AgentType.CRITICO.value:"rag",
            AgentType.EVALUADOR.value: "rag",
            "FINISH": END
        }
    )
    #una vez el nodo RAG ha obtenido el contexto relevante, se redirige al agente correspondiente
    graph_builder.add_conditional_edges(
        "rag",
        lambda state: state["next"],
        {
            AgentType.EDUCADOR.value: AgentType.EDUCADOR.value,
            AgentType.DEMOSTRADOR.value: AgentType.DEMOSTRADOR.value,
            AgentType.CRITICO.value: AgentType.CRITICO.value,
            AgentType.EVALUADOR.value: AgentType.EVALUADOR.value,
        }
    )
    #Tras el educador, ramificamos: por defecto encadenamos al demostrador para que
    #complemente la explicacion con un ejemplo. Pero si el educador ha detectado que el
    #alumno pidio una pregunta de autoevaluacion (skip_demostrador=True), saltamos al
    #final del grafo: no tiene sentido ilustrar una pregunta con un ejemplo.
    graph_builder.add_conditional_edges(
        AgentType.EDUCADOR.value,
        lambda state: END if state.get("skip_demostrador") else AgentType.DEMOSTRADOR.value,
        {
            END: END,
            AgentType.DEMOSTRADOR.value: AgentType.DEMOSTRADOR.value,
        },
    )
    graph_builder.add_edge(AgentType.DEMOSTRADOR.value, END)

    #el evaluador evalúa el código y pasa al critico, que da feedback, y luego se guarda el progreso
    graph_builder.add_edge(AgentType.EVALUADOR.value, AgentType.CRITICO.value)
    graph_builder.add_edge(AgentType.CRITICO.value, "guardar_progreso")
    graph_builder.add_edge("guardar_progreso", END)
    
    #añadimos memoria al grafo para que los agentes puedan recordar las interacciones anteriores
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    return graph

# Construimos el grafo a nivel de módulo para que esté disponible en stream_graph_updates
graph = _build_graph()

# Funcion para ejecutar el workflow y mostrar las actualizaciones en tiempo real
async def stream_graph_updates(user_input: str, thread_id: str, user_level: str, alumno_id: int, asignatura: str = None, tipo_asignatura: str = "programacion"):
    config = {"configurable": {"thread_id": thread_id}}

    checkpoint = graph.get_state(config)
    mensajes_previos = len(checkpoint.values.get("mensajes", [])) if checkpoint.values else 0

    sent_contents: set[str] = set()
    respuesta_completa: list[str] = []
    ultimo_agente = "codi"
    prev_event: dict = {}

    # Cola productor/consumidor: el productor empuja eventos de graph.astream, el consumidor
    # los emite por SSE. Si pasan 10s sin evento yieldeamos un comentario keepalive para que
    # Node/proxies/navegador no corten la conexion mientras un nodo bloquea (LLM lento, RAG).
    queue: asyncio.Queue = asyncio.Queue()

    async def producer():
        try:
            async for event in graph.astream(
                {"mensajes": [("user", user_input)], "user_level": user_level, "alumno_id": alumno_id, "respuesta_supervisor": "", "asignatura": asignatura, "tipo_asignatura": tipo_asignatura},
                config,
                stream_mode="values",
            ):
                await queue.put(("event", event))
        except Exception as e:
            await queue.put(("error", str(e)))
        finally:
            await queue.put(("done", None))

    producer_task = asyncio.create_task(producer())

    try:
        while True:
            try:
                kind, data = await asyncio.wait_for(queue.get(), timeout=10)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue

            if kind == "done":
                break
            if kind == "error":
                error_payload = json.dumps({"error": data}, ensure_ascii=False)
                yield f"data: {error_payload}\n\n"
                break

            event = data

            # Respuesta directa del supervisor (FINISH con texto)
            respuesta_supervisor = event.get("respuesta_supervisor", "")
            if respuesta_supervisor and respuesta_supervisor not in sent_contents:
                sent_contents.add(respuesta_supervisor)
                payload = json.dumps({"content": respuesta_supervisor, "agent": "codi"}, ensure_ascii=False)
                respuesta_completa.append(respuesta_supervisor)
                ultimo_agente = "codi"
                prev_event = event
                yield f"data: {payload}\n\n"
                continue

            # Respuesta de un agente especializado — solo mensajes nuevos de este turno
            mensajes = event.get("mensajes", [])
            nuevos = mensajes[mensajes_previos:]
            if not nuevos:
                prev_event = event
                continue
            ultimo_mensaje = nuevos[-1]

            if isinstance(ultimo_mensaje, AIMessage) and ultimo_mensaje.content:
                # Gemini puede devolver content como lista de partes [{"type":"text","text":"..."}]
                # en lugar de string. Normalizamos antes del strip() para evitar AttributeError.
                raw_content = ultimo_mensaje.content
                if isinstance(raw_content, list):
                    raw_content = "".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in raw_content
                    )
                content = str(raw_content).strip()
                if content and content not in sent_contents:
                    sent_contents.add(content)
                    agent = _detect_agent(event, prev_event)
                    payload = json.dumps({"content": content, "agent": agent}, ensure_ascii=False)
                    respuesta_completa.append(content)
                    ultimo_agente = agent
                    yield f"data: {payload}\n\n"

            prev_event = event

        yield "data: [DONE]\n\n"

    except (GeneratorExit, asyncio.CancelledError):
        # El cliente cerro la conexion. Cancelamos el productor (fire-and-forget) y
        # propagamos. No await aqui: bloquear el cleanup en Python 3.12 dispara
        # "FATAL: exception not rethrown" porque el async generator se cierra mal.
        producer_task.cancel()
        raise
    except Exception as e:
        producer_task.cancel()
        # Intentamos emitir el error; si el generator ya esta cerrando, lo ignoramos
        # para no romper el cleanup.
        try:
            error_payload = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"
        except (GeneratorExit, RuntimeError):
            pass
    finally:
        # Solo persistencia, sin awaits. El producer_task ya esta cancelado en los
        # except superiores; si llegamos aqui por flujo normal (done), tambien se
        # cancela por si quedo algo pendiente.
        if not producer_task.done():
            producer_task.cancel()

        if respuesta_completa and alumno_id:
            try:
                guardar_interaccion(
                    alumno_id=alumno_id,
                    mensaje_usuario=user_input,
                    respuesta_agente="\n\n".join(respuesta_completa),
                    tipo_interaccion=ultimo_agente,
                    asignatura=asignatura
                )
            except Exception:
                pass

def _detect_agent(event: dict, prev: dict) -> str:
    """Detecta el agente comparando el estado actual con el anterior para ver qué cambió en este turno."""
    if event.get("puntuacion") is not None and event.get("puntuacion") != prev.get("puntuacion"):
        return AgentType.EVALUADOR.value
    if event.get("feedback") and event.get("feedback") != prev.get("feedback"):
        return AgentType.CRITICO.value
    if event.get("explicaciones") and event.get("explicaciones") != prev.get("explicaciones"):
        return AgentType.EDUCADOR.value
    if event.get("demostraciones") and event.get("demostraciones") != prev.get("demostraciones"):
        return AgentType.DEMOSTRADOR.value
    return "codi"