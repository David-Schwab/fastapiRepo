from random import randrange
from typing import Optional, List
from fastapi import FastAPI , Depends
from fastapi import Body, Response, status, HTTPException
from pydantic import BaseModel 
import psycopg # psycopg documentation
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from . import models, schemas, utils
from .sqlalchemy_database import  lifespan, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import Session


app = FastAPI(lifespan=lifespan)


#alte version .query  und sync ###################
'''
@app.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db_sync)):
    posts = db.query(models.Post).all()
    return{"data": posts}
'''

#neue version + async #################
@app.get("/sqlalchemys")
async def get_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Post))  # select statt query
    # das ist result: <sqlalchemy.engine.result.ChunkedIteratorResult object at 0x000001F751F19550>
    posts = result.scalars().all()  # .scalars() holt die ORM-Objekte
   # das ist posts: [<app.models.Post object at 0x0000018EBE538B90>, <app.models.Post object at 0x0000018EBE186E00>, 
    #das ist posts ohen scalars().  [(<app.models.Post object at 0x00000276F09B9010>,), (<app.models.Post object at 0x00000276F09C4B90>,),
    # das ist posts ohne all() : <sqlalchemy.engine.result.ScalarResult object at 0x000002BDA8282890>
    
    return {"data": posts}

#result holt die rohen Daten aus der Datenbank (in SQLAlchemy oft als Zeilen/Row-Objekte).
# scalar : Hol mir die eigentlichen Objekte, die zu den Zeilen gehören, also die Post-Instanzen
# all() nimmt alle Objekte aus dem Result-Objekt und packt sie in eine Python-Liste. [Post(...), Post(...), Post(...)]

@app.post("/sqlalchemys", status_code = status.HTTP_201_CREATED)
async def create_posts(post: schemas.Post, db: AsyncSession = Depends(get_db)):
    try:
        result = models.Post(**post.model_dump()) # result : <app.models.Post object at 0x00000154E10B86E0> # erstellt ein Post objekt
        # anstatt das:title=post.title, content=post.content, published=post.published kann man das schreiben **post.dump()

        db.add(result)# „Session, merk sich Objekt, wir wollen es später einfügen.“  kein INPUT ODER output, kein await , bei db.insert direkte ausführung
        await db.commit() # erst hier await 
        await db.refresh(result)# gleich wie RETURNING * , um neuen post anzeigen zu lassen
        return{"data": result}
    except psycopg.Error as err: 
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err

@app.get("/sqlalchemys/{id}")
async def get_pbyid(id: int , db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(models.Post).where(models.Post.id == id))
        post = result.scalars().first() # nicht all machen (falls man was nach anderem sucht außer id), weil sonst postgres weiter sucht ob noch irgendwo anders ein eintrag mit der id ist, bei first gibt er sofort das erste erbenis

    # bei id eigentlich so besser result = await db.get(models.Post, id)
        if post is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
        return {"data": post}
    except psycopg.Error as err: 
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
    
@app.delete("/sqlalchemys/{id}")
async def delete_post(id: int , db: AsyncSession = Depends(get_db)):
    try:
#result = await db.execute(select(models.Post).where(models.Post.id == id)) # man könnte hier shcon delete machen, aber sonst kann man den post nicht anzeigen
#post = result.scalars().first() # first gibt das erste element der liste zurück, wenn man eh nach id filter und es nur ein einziges ergebnis gibt ist folgendes besser:
        post = await db.get(models.Post, id) # besser wenn man nach id sucht
        if post is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
        await db.delete(post)
        await db.commit()

        return {"data": post}
    except psycopg.Error as err: 
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
    
@app.put("/sqlalchemys/{id}")
async def change_post(id: int, post: schemas.Post, db: AsyncSession = Depends(get_db)):
    try:

        result =await db.get(models.Post, id)
       # result = await db.execute(
       # select(models.Post).where(models.Post.id == id)
       # )
       # upd_post = result.scalar_one_or_none()

        if result is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
        updated_post = post.model_dump()
        # updated_post = {'title': 'new2', 'content': 'new2', 'published': True} , model_dump macht es zu dictionary alles was übergeben wurde bzw default ist
        for key, value in updated_post.items():
            setattr(result, key, value) # ersetzt mit key und dessen wert die felder im eintrag der geupdated werden soll 
        
        await db.commit() 
        await db.refresh(result)
        return{"data": result}
    except psycopg.Error as err: 
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
    

################################################################################################################
@app.get("/alchemynew", response_model=List[schemas.ResPost])
async def get_postsnew(db: AsyncSession = Depends(get_db)):
    try:

        result = await db.execute(select(models.Post))
        posts = result.scalars().all()
        return posts

    except psycopg.Error as err: 
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err

@app.post("/alchemynew", status_code = status.HTTP_201_CREATED, response_model= schemas.ResPost)
async def create_posts(post: schemas.Post, db: AsyncSession = Depends(get_db)):
    try:
        result = models.Post(**post.model_dump()) # result : <app.models.Post object at 0x00000154E10B86E0> # erstellt ein Post objekt
        # anstatt das:title=post.title, content=post.content, published=post.published kann man das schreiben **post.dump()

        db.add(result)# „Session, merk sich Objekt, wir wollen es später einfügen.“  kein INPUT ODER output, kein await , bei db.insert direkte ausführung
        await db.commit() # erst hier await 
        await db.refresh(result)# gleich wie RETURNING * , um neuen post anzeigen zu lassen
        return  result
    except psycopg.Error as err: 
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
    
#################################### user #######################



@app.post("/users", status_code = status.HTTP_201_CREATED, response_model= schemas.ResUser)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:

        hashed_password = utils.hasher(user.password) #password wird gehasht
        user.password = hashed_password     #gehashtes passwort wird ersetzt

        result = models.User(**user.model_dump()) 

        db.add(result)
        await db.commit() 
        await db.refresh(result)
        return  result
    except psycopg.Error as err: 
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
    
@app.get("/users/{id}", response_model=schemas.ResUser)
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(models.User, id)
    
    if user is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
    return user