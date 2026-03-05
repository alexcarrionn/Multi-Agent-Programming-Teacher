from enum import Enum

class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    EDUCADOR = "educador"
    DEMOSTRADOR = "demostrador"
    EVALUADOR = "evaluador"
    CRITICO = "critico"