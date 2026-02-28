import jwt
from .config import settings
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from . import schemas, models
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .sqlalchemy_database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
oauth2_scheme =OAuth2PasswordBearer(tokenUrl= "/login") # wenn depopend(oauth2_scheme) Endpoint erwartet einen JWT-Bearer-Token in der Authorization Header der Form Bearer <token>
#tokenUrl="/login" sagt, wo der Client den Token anfordern soll
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



def create_access_token(data: dict): # data = {"email": "x", "password": "y"}
    to_encode = data.copy() # speichert den payload, oder nur so wenn man nur will das etwas spezielles in den paylpad kommt : to_encode = {"sub": str(user_id), "exp": expire}
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.expire_min) # berechnung wann token expired
    to_encode.update({"exp": expire}) # {"exp": "12345"} wird zum payload ergänzt , wenn zeit überschritten dann token ungültig
    encoded_jwt = jwt.encode(to_encode, settings.secretkey, algorithm=settings.algorithm) # jwt token erstellen
    return encoded_jwt

async def verify_access_token(token: str, credentials_exception):

    try:
        payload = jwt.decode(token, settings.secretkey, algorithms=[settings.algorithm])
        idd = payload.get("sub") # id wird aus dem payyload extrahiert
        if idd is None:
            raise credentials_exception
        token_data = schemas.TokenData(id = idd)    # id aus token data wird der id aus dem schema gleichgesetzt, schema prüft ob id ein string oder none ist
    except InvalidTokenError:
        raise credentials_exception

    return token_data   #token data = (TokenData(id='11'),)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)): # token wird als string aus dem authorization header geholt
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                                detail="Could not validate credentials",
                                                headers={"WWW-Authenticate": "Bearer"},)
        tok= await verify_access_token(token, credentials_exception)
        result = await db.execute(select(models.User).where(models.User.id == int(tok.id))) # gibt ein result objekt zurück, zu int casten weil es vorher string war
        user = result.scalars().first()# result gibt eine liste mit rows , wo jeweils ein user object drin ist
        # result nimmt nur den inhalt aus einer row, also das user object und first gibt das erste ergebnis der liste
        #statt scalars first auch scalar_one_or_none() möglcih
        return user
