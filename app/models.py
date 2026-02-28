
from app.sqlalchemy_database import Base
from sqlalchemy import TIMESTAMP, String, func, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

#python True und False immer groß, was es selbst zu verstehen hat, bei server_default klein, weil das text für sql ist

'''ALTE VERSION
class Post(Base):
    __tablename__ = "alchemyposts"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, server_default="True", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
'''
#neue Version 2.0

class Post(Base):
    __tablename__ = "alchemyposts"
#Mapped” heißt es, weil SQLAlchemy ab hier weiß, dass das Python-Feld in der DB existiert und automatisch synchronisiert wird.
    id: Mapped[int] = mapped_column(primary_key=True) # standardmäißg ist nullable = false in alchemy 2.0
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    published: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE")) # man referenziert hier table name und nicht classname
# ondelete  cascade, wenn user gelöscht wird, werden posts mit gelöscht
    post_owner: Mapped["User"] = relationship("User") #damit kann man machen Post.post_owner --> gibt den User zurück




class User(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(primary_key=True)
    email:Mapped[str] = mapped_column(String, unique=True) # muss unique sein
    password:Mapped[str] = mapped_column(String)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class Like(Base):
    __tablename__ = "likes"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True) # zusammengesetzter primary key aus user id und post id
    post_id: Mapped[int] = mapped_column(ForeignKey("alchemyposts.id", ondelete="CASCADE"), primary_key=True)
    # sowohl user_id als auch post_id sind foreign keys, die auf die jeweiligen tabellen verweisen, und beide zusammen bilden den primary key der like tabelle,
    # damit wird sichergestellt dass ein user nur einmal einen post liken kann, weil die kombination aus user_id und post_id einzigartig sein muss
