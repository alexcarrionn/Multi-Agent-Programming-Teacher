from enum import Enum

class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    EDUCADOR = "educador"
    DEMOSTRADOR = "demonstrador"
    EVALUADOR = "evaluador"
    CRITICO = "critico"