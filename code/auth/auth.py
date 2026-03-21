#Este fichero va a servir para poder contener la seguridad de la aplicacion, es decir login, logout, regitro
from datetime import timedelta, datetime, timezone
from typing import Optional
from fastapi import Cookie, HTTPException, status
from jose import JWTError, jwt
from config.settings import settings

#Definimos una funcion para crear el token de acceso, esta funcion va a recibir un diccionario con los datos del usuario y va a devolver un token 
# JWT codificado con esos datos y una fecha de expiracion.
#  El token se codifica utilizando la clave secreta y el algoritmo especificados en la configuracion.
def create_access_token(data: dict) -> str:
    #primero se copia el diccionario de datos para no modificar el original
    to_encode = data.copy()
    #Se establece la fecha de caducidad del token 
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION)
    #Se agrega la fecha de expiracion al diccionario de datos que se va a codificar en el token
    to_encode.update({"exp": expire})
    #Se codifica el token 
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

#Con esta funcion vamos a obtener al usuario actual a partir del token de acceso que se encuentra en las cookies.
def get_current_user(token: Optional[str] = Cookie(None, alias="access_token")) -> dict:
    #Si no hay token en las cookies, se lanza una excepcion de no autenticado
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    try:
        #Si lo hay se descodifica el token utilizando la clave secreta y el algoritmo 
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")