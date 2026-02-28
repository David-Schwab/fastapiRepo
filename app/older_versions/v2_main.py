from random import randrange
from typing import Optional
from fastapi import FastAPI , Depends
from fastapi import Body, Response, status, HTTPException
from pydantic import BaseModel 
import psycopg # psycopg documentation
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool

#bei datenbank operationen --> await




# ---------- Models ----------
class Post(BaseModel):
    title: str
    content: str
    published: bool = True
# ---------- Lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):  #lifespan ist eine funktion die bei server start und server stopp ausgeführt wird. Alles vor yield wird beim Server start ausgeführt, also der pool erstellt
    async with AsyncConnectionPool( # async with öffnet ressource, also den pool, schließt wieder wenn wir fertig sind (nach yield)
        "postgresql://postgres:david@localhost/fastapiDatabase",
        min_size=1,
        max_size=10, #mindestens eine und maximal 10 gleichzeitige verbindungen
        kwargs={"row_factory": dict_row} #key word arguments wird an die connections übergeben, die kennen row_factory , dict_row macht aus ausgabe ein dictionary
    ) as pool: # Erstellt einen Pool von PostgreSQL-Verbindungen, also mehrere gleichzeitige Verbindungen, die der Server wiederverwenden kann.
        app.state.pool = pool #Speichert den Pool in der App, sodass alle Endpoints darauf zugreifen können: app.state globaler speicher
        yield   # alles nach yield wird bei server stopp ausgeführt
        print("Pool geschlossen")
    # Ctrl+C in der Konsole oder uvicorn beendet wird , werden verbindungen geschlossen und speicher freigegeben

app = FastAPI(lifespan=lifespan) # statt fastapi selbst machen zu lassen , eigene lifespan einfügen

# ---------- Dependency ----------
async def get_db(): #wird bei jedem request an datenbank aufgerufen
    conn = await app.state.pool.getconn() # holt connection aus dem pool , entweder neue erschaffen, eine geholt, oder auf eine gewartet
    try:
        await conn.set_autocommit(False) #schaltet Autocommit aus, damit du manuell commit() oder rollback() machen kannst.
        yield conn # yield conn übergibt die Connection an den Endpoint, der sie dann benutzen kann. HiER arbeitet der Endpoint
        print("connection wird zurückgegeben")
    finally:
        await app.state.pool.putconn(conn) # finally wird immer ausgeführt, egal was passiert:Ob der Endpoint erfolgreich läuft Ob ein Fehler geworfen wird ,Zweck hier: die Connection zurück in den Pool geben
        

# ---------- Routes ----------
@app.get("/")
def root():
    return {"Hello": "Wo"}      

@app.get("/posts")
async def get_posts(db=Depends(get_db)): # die funktion ist abhängig von get_db , braucht eine db connection aus dem poll abhängig gleich dependecy deswegen Depends: speichert verbindung in der variablen db
   # Depends ist eine anweisung an fast api , "besorg mir das bitte bevor du mich aufrufst"
   # Wenn dieser Endpoint aufgerufen wird, dann rufe ich get_db auf“ , deshalb nicht get_db() schreiben
    try:
        async with db.cursor() as cur: # db.cursor() erzeugt einen cursor auf der erhaltenen connection , mit async with, wird cursor geschlossen wenn fertig
            await cur.execute("SELECT * FROM posts") #heißt schicke den sql befehl an postgres und lass ihn dort ausführen
            rows = await cur.fetchall()  #alle ergebnisse holen- Der Cursor weiß, wo die Daten sind und wie man sie liest – er ist nicht die Daten
        return {"data": rows} 
    except psycopg.Error as err: #psycopg.Error → fängt alle DB-Fehler ,except Exception fängt alles, nicht nur DB-Fehler.
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err #tatsächlichen fehler im log speichern wird nicht dem client gezeigt, taucht nur im Server-Log
    
@app.post("/posts", status_code = status.HTTP_201_CREATED)
async def create_post(post: Post , db=Depends(get_db)): #Post ist ein Pydantic-Model, das FastAPI sagt: „Erwarte ein JSON-Objekt im Body, das so aussieht wie Post.“
    try:                                                #FastAPI validiert die Daten vorher automatisch. Wenn z. B. published fehlt oder kein bool ist, bekommt der Client direkt einen 422 Unprocessable Entity.'
        async with db.cursor() as cur:
            await cur.execute('''INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *''',         # statt %s hätte man auch direkt post.title machen können aber dann gefahr von sql injection , client könnte sql query im body senden
                              (post.title, post.content, post.published)) 
            new_post = await cur.fetchone()
            await db.commit()
            return {"data": new_post}
    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
    

@app.get("/posts/{id}")
async def get_postsbyid(id: int , db=Depends(get_db)): #hier muss id ein int sein, weil sonst der user x beliebige dinge angeben könnte, man will aber einen zahlenwert haben
    try:
        async with db.cursor() as cur: 
            await cur.execute('''SELECT * FROM posts WHERE id = %s''',
                              (id,)) # execute erwartet --> execute(sql: str, params: Sequence[Any]) , params ist eine Sequenz also etwas, worüber man laufen kann z.B. Tupel oder liste
            #psycopg braucht immer eine Liste von Werten, selbst wenn es nur einer ist (einheitlich), Ein Tupel ist eine unveränderliche Werteliste. 
            rows = await cur.fetchone() 
            if rows is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
        return {"data": rows} 
    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
    
@app.delete("/posts/{id}")
async def delete_post(id: int , db=Depends(get_db)): 
    try:
        async with db.cursor() as cur: 
            await cur.execute('''DELETE FROM posts WHERE id = %s RETURNING *''',
                              (id,)) 
            rows = await cur.fetchone() 
            if rows is None:
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
        await db.commit()
        return {"data": rows} 
    except psycopg.Error as err:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err
    
@app.put("/posts/{id}")
async def update_post(id: int , post: Post , db=Depends(get_db)): 
    try:
        async with db.cursor() as cur: 
            await cur.execute('''UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING *''',
                              (post.title, post.content, post.published, id)) 
            rows = await cur.fetchone() 
            if rows is None:
               # await db.rollback()
                raise HTTPException(
                        status_code= status.HTTP_404_NOT_FOUND,
                        detail=f"Post with id: {id} not found"
                        )
        await db.commit()
        return {"data": rows} 
    except psycopg.Error as err:
       # await db.rollback() , macht psycopg automatisch
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database temporarily unavailable"
        ) from err