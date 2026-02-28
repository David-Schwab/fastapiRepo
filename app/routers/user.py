
from fastapi import Depends, APIRouter
from fastapi import status, HTTPException
import psycopg
from .. import models, schemas, utils
from ..sqlalchemy_database import get_db
from sqlalchemy.ext.asyncio import AsyncSession



router = APIRouter(
      prefix="/users",
      tags=["Users"] # gruppierung von routes in localhost/docs
)

@router.post("/", status_code = status.HTTP_201_CREATED, response_model= schemas.ResUser)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:

        hashed_password = utils.hasher(user.password) #password wird gehasht
        user.password = hashed_password     #gehashtes passwort wird ersetzt

        result = models.User(**user.model_dump()) # user ist ein pydantic model was als request mitgesendet wurde
        # model.dump convertiert in ein dictionary und ** wandelt es unpacked es in normale argumente (kwargs) : username="david", email="david@example.com", password="hash"
        db.add(result)
        await db.commit()
        await db.refresh(result)
        return  result
    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err

@router.get("/{id}", response_model=schemas.ResUser)
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(models.User, id)

    if user is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
    return user
