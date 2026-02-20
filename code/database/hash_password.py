from passlib.context import CryptContext

#Creamos el contexto de encriptacion 
context = CryptContext(schemes=["pbkdf2_sha256"], 
                        default="pbkdf2_sha256", 
                        pbkdf2_sha256__default_rounds=50000
                    )

def hash_password(password: str) -> str:
    """Hashea una contraseña utilizando el contexto de encriptación definido."""
    return context.hash(password)   

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña sin formato coincide con la contraseña hasheada."""
    return context.verify(plain_password, hashed_password)

