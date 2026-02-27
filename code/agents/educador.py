from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts.educador_prompts import AGENTE_EDUCADOR_PROMPT

class EducadorAgent:

    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", AGENTE_EDUCADOR_PROMPT),
            ("system", "Nivel del alumno: {user_level}"),
            ("system", "Contexto relevante:\n{contexto}"),
            MessagesPlaceholder(variable_name="messages"),
        ])

    def run(self, state):
        chain = self.prompt | self.llm

        response = chain.invoke({
            "messages": state["mensajes"],
            "user_level": state.get("user_level", "intermedio"),
            "contexto": state.get("contexto", "No disponible")
        })

        return {
            "mensajes": [response],
            "explicaciones": response.content
        }