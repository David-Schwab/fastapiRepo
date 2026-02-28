
from sqlalchemy.exc import IntegrityError

from fastapi import APIRouter
from fastapi import Depends, status, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas
from .. import models, schemas, oauth2
from ..sqlalchemy_database import get_db


router = APIRouter(
    prefix="/likes", # damit man das nicht pberall schreiben muss , danach reicht "/"
    tags=["Likes"]
)

@router.post("/", status_code = status.HTTP_201_CREATED )
async def like_post(like: schemas.Like , db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    post = await db.get(models.Post, like.post_id)
    if post is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {like.post_id} not found"
        )

    if like.dir == 1:
        result = models.Like(user_id = current_user.id, post_id = like.post_id)
        db.add(result)
        try:
            await db.commit()
            return {"message": "Post liked"}
        except IntegrityError:  # z.B. PrimaryKey / Unique Constraint
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already liked this post"
            )

    elif like.dir == 0:
        result = await db.get(models.Like, (current_user.id, like.post_id)) # zusammengesetzter primary key aus user id und post id
        if result is None:
            raise HTTPException(
                    status_code= status.HTTP_404_NOT_FOUND,
                    detail=f"Like not found"
                )
        await db.delete(result)
        await db.commit()
        return {"message": "Post unliked"}
