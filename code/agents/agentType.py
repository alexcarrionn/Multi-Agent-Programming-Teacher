from enum import StrEnum 

class AgentType(StrEnum):
    SUPERVISOR = "supervisor"
    EDUCADOR = "educador"
    DEMOSTRADOR = "demonstrador"
    EVALUADOR = "evaluador"
    CRITICO = "critico"