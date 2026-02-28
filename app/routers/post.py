
from ast import stmt
from itertools import count
from typing import  List, Optional
from fastapi import  Depends, APIRouter
from fastapi import  status, HTTPException
import psycopg # psycopg documentation
from .. import models, schemas, oauth2
from ..sqlalchemy_database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from .. import oauth2


router = APIRouter(
    prefix="/sqlalchemys", # damit man das nicht pberall schreiben muss , danach reicht "/"
    tags=["Posts"]
)


@router.get("/", response_model=List[schemas.ResPostWithLikes]) # response model ist eine liste von posts, weil
async def get_postsnew(db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user), number_posts: int = 2, skip: int = 1, search: Optional[str]= None):
    #number posts default = 2 , um zu ändern in url query angeben :URL?number_posts=4&skip&search=   --> search optional, standardmäßig kein search
    try:
        stmt = select(models.Post,func.count(models.Like.post_id).label("number_likes")).outerjoin(models.Like).where(models.Post.user_id == current_user.id)
        if search: # wenn nicht none
            stmt = stmt.where(models.Post.title.ilike(f"%{search}%")) # ilike case insensitive , mit den % sagt man das das search wort überall auftauchen kann
       # result = await db.execute(select(models.Post)) # man kpnnte hier noch .where(models.Post.user_id == current_user.id) machen um nur posts vom jeweiligen user angezeigt zu bekommen
        stmt = stmt.group_by(models.Post.id).limit(number_posts).offset(skip)
        # .limit() limitiert die anzahl an ergebnissen, offset() überspringt ergebnisse
        result = await db.execute(stmt)

        posts = result.all() # hier all machen , weil scalars nur das erste element zurückgibt, aber hier haben wir ja 2 elemente (post, number_likes) , deshalb all damit beide elemente zurückgegeben werden,
        #dann ist posts eine liste von tuples [(post, number_likes), (post, number_likes)]

        return posts

    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err

@router.post("/", status_code = status.HTTP_201_CREATED, response_model= schemas.ResPost) # type hint nicht zwigend, auch current_user = Depends möglich
async def create_posts(post: schemas.Post, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)): # user muss eingeloggt sein um ein post zu machen , funktion get_current_user wird aufgerufen, am ende wird eine id zurückgegeben
    try:
        result = models.Post(user_id = current_user.id, **post.model_dump()) # result : <app.models.Post object at 0x00000154E10B86E0> # erstellt ein Post objekt
        # anstatt das:title=post.title, content=post.content, published=post.published kann man das schreiben **post.dump()
        # user_id dem post zuweisen , je nachdem welcher user den post erstellt hat, einfach kwarg hinzufügen
        print("email", current_user.email)
        db.add(result)# „Session, merk sich Objekt, wir wollen es später einfügen.“  kein INPUT ODER output, kein await , bei db.insert direkte ausführung
         # erst hier await
        await db.commit()
        await db.refresh(result)# gleich wie RETURNING * , um neuen post anzeigen zu lassen
        return result
    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err

@router.put("/{id}", response_model=schemas.ResPost)
async def change_post(id: int, post: schemas.Post, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    try:

        result =await db.get(models.Post, id)   # geht nur mit primary key
       # result = await db.execute(
       # select(models.Post).where(models.Post.id == id)
       # )
       # upd_post = result.scalar_one_or_none()

        if result is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )

        if result.user_id != current_user.id:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform requested action"
            )

        updated_post = post.model_dump()
        # updated_post = {'title': 'new2', 'content': 'new2', 'published': True} , model_dump macht es zu dictionary alles was übergeben wurde bzw default ist
        for key, value in updated_post.items():
            setattr(result, key, value) # ersetzt mit key und dessen wert die felder im eintrag der geupdated werden soll

        await db.commit()
        await db.refresh(result)
        return result
    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err


@router.get("/{id}", response_model=schemas.ResPostWithLikes)
async def get_pbyid(id: int , db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    try:
        stmt = select(models.Post, func.count(models.Like.post_id).label("number_likes")).outerjoin(models.Like).where(models.Post.id == id)

        # Row(
           # Post=<Post ORM object>, im schema die selben namen, schema erwartet genau das
           # number_likes=3
        #)
        stmt = stmt.group_by(models.Post.id)
        result = await db.execute(stmt)
        post = result.first() #  das erste erbenis

    # bei id eigentlich so besser result = await db.get(models.Post, id)
        if post is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )

        return post

    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err

@router.delete("/{id}", response_model=schemas.ResPost)
async def delete_post(id: int , db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    try:
#result = await db.execute(select(models.Post).where(models.Post.id == id)) # man könnte hier shcon delete machen, aber sonst kann man den post nicht anzeigen
#post = result.scalars().first() # first gibt das erste element der liste zurück, wenn man eh nach id filter und es nur ein einziges ergebnis gibt ist folgendes besser:
        post = await db.get(models.Post, id) # besser wenn man nach id sucht
        if post is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
        if post.user_id != current_user.id:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform requested action"
            )

        await db.delete(post)
        await db.commit()

        return post
    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
