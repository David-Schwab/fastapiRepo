from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, conint


# am besten verschiedene scheams für verschieden  sachen

class Post(BaseModel):# pydantic model-> definiert structure von req und res, hier in dem beispiel geht ein request nur durch wenn auch title und content angegeben sind
    title: str
    content: str
    published: bool = True # published muss nicht angegeben weil default = True

class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True

class PostCreate(PostBase): # geht auch so , dann wird von postbase geerbt
    pass
'''class CreatePost(BaseModel):
        title: str
        content: str
        published: bool = True

    class UpdatePost(BaseModel):
        title: str
        content: str
        published: bool # für update psot gezwungen ein published anzugegeben
'''

###response schemas

class ResPost(PostBase): # created_at wird nicht gezeigt
    id: int # erbt Rest von Postbase
    user_id: int
    post_owner: ResUser # dieses response schema gibt als post owner ein user zurück, indem fall in form des pydandtic models ResUser
    model_config = ConfigDict(from_attributes=True) # muss nicht unbedingt stehen

class ResPostWithLikes(BaseModel):
    Post: ResPost   # muss groß geschrieben sein, weil das model Post heißt groß geschrieben. Und als Response
    number_likes: int
################################################# User

class UserCreate(BaseModel):
    email: EmailStr # validiert ob die eingabe auch eine email ist
    password: str

class ResUser(BaseModel): # kein passwort übergeben
    id: int
    email: EmailStr
    created_at: datetime

#############################################################

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str   # id kann ein string sein oder nicht enthalten


class Like(BaseModel):
    post_id: int
    dir: int #conint(ge=0, le=1)   # 1 für like, 0 für dislike, damit
