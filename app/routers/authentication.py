
from fastapi import  Depends, APIRouter
from fastapi import  status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from ..oauth2 import create_access_token # psycopg documentation
from .. import models, schemas
from ..sqlalchemy_database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .. utils import verify_passwords


router = APIRouter(
    tags=["authentication"]
)



@router.post("/login", response_model=schemas.Token)
async def login(user_zugang: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
     #db.get geht nur mit primary_key, OAuth2PasswordRequestForm funktioniert in Postman als form-data (Key=“username”, Key=“password”), nicht JSON
    query = await db.execute(select(models.User).where(models.User.email == user_zugang.username)) # Ouath2passwordrequestform speichert username: und password: , muss auf postman nicht mehr als raw data sondern form-data übegeben werden
    user = query.scalar_one_or_none() # gibt ein ergebnis oder none

    if user is None:
        raise HTTPException(
                        status_code= status.HTTP_403_FORBIDDEN,
                        detail=f"Invalid Credentials"           #nicht offenlegen was falsch ist
                        )

    if not verify_passwords(user_zugang.password, user.password):
        raise HTTPException(
                        status_code= status.HTTP_403_FORBIDDEN,
                        detail=f"Invalid Credentials"
                        )

    access_token = create_access_token(data={"sub": str(user.id)}) # id wird standardmäßig sub für subject genannt, standard auch string

    return {"access_token": access_token, "token_type": "bearer"}
