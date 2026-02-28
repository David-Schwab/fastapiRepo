from random import randrange
from typing import Optional
from fastapi import FastAPI #python server ist 
from fastapi import Body, Response, status, HTTPException
from pydantic import BaseModel # library

#Python style guide

#Funktionsnamen → klein, mit Unterstrichen → snake_case
#klassen CamelCase --> BlogPost
#variablen snake_case


#fastapi dev app/main.py: zum server starten , strg+c um server zu stoppen
#file, detects the FastAPI app in it, and starts a server using Uvicorn.
#By default, fastapi dev will start with auto-reload enabled for local development.

app = FastAPI()

#lesson1###################################################################################################################################################################################################################

#Ein Decorator ist in Python ein Funktion, die eine andere Funktion verändert oder erweitert, ohne die ursprüngliche Funktion selbst zu ändern.
#Syntax: @name_des_decorators direkt über einer Funktion.

@app.get("/") # wird decorator genannt durch @ zeichen --> wenn get http request gesendet wird  , root path --> '/' = http://127.0.0.1:8000 bzw http://127.0.0.1:8000/ , bei get request auf diese url
async def root(): #async optional , nur wenn funktion auch asychron verwendet wird
    return {"Hello": "Wo"} #fast api convertiert automatisch zu json (universelle sprache von APIs)


#wichtig zu wissen: jedes mal wenn man einen request an seinen api server sendet, geht er von oben nach unten alle path operations durch und nimmt das erste Ergebnis das zutrifft
# falls man bei beiden operations '/' verwendet wird er das erste nehmen
# request GET method url: "/"
@app.get("/showposts ")
def show_post():
    return {"data": "this is your post"}

@app.post("/createposts")
def create_post(body_inhalt: dict = Body(...)): # mit ... sagt man body muss vorhanden sein, inhalt von body wird als dict (dictionary) geparst (umgewandelt) und dann in variable gespeichert
    print(body_inhalt)
    return{"New Post": f"Post title {body_inhalt['title']} content: {body_inhalt['content']}"}

#dictionary :{'title': 'best beaches in florida',
           #   'content': 'check out this beaches'}

#lesson2####################################################################################################################################################################################################################################################################################

#User input soll ein schema haben (daten im body)
#title und content sollen strings sein , alle eingaben werden zu strings konvertiert

class Posts(BaseModel): # Posts extends BaseModel
    title: str #validiert die eingaben
    content: str # sendet automatisch error code wenn was falsch eingegeben wurde oder was fehlt
    published: bool = True # Default ist True gesetzt , falls nicht gegeben
    rating: Optional[int] = None # typ Optional importiert aus library , wenn etwas eingegebn soll es ein int sein, default ist es None


my_posts = [{"title": "post1 title", "content": "post1 content", "id": 1}, {"title": "post2 title", "content": "post2 content", "id": 2}]# liste von dictionarys

@app.get("/myposts")
def myposts():
    return{"data": my_posts} #convertierung in json des dicts

@app.post("/newposts")
def new_post(post: Posts): 
    print(post) #statt dictionary automatisch den inhalt extrahiert: title='best beaches in florida' content='check out this beaches' mit neuer_post.title zugreifbar
    #neuer_post.dict() konvertiert den inhalt immer in ein dicitonary
    return{"data": "new post"}

@app.post("/creposts", status_code= status.HTTP_201_CREATED) # immer status code mitsenden nach erfolg
def cre_posts(postings: Posts):
    postings_dict = postings.model_dump() #mode_dump() neu von pydantic, selbe wie dict(), .model_dump_json() #konvertiert in json, immer das zurückschicken was neu erstellt wurde geht nur bei pydantic Objekten wie Posts
    postings_dict["id"] = randrange(0,10000000)
    my_posts.append(postings_dict)
    return {"data": postings_dict} #Standardpraxis in APIs ist alle Daten in einem Key zu kapseln, z. B. "data"



def find_post(id):
    for post in my_posts:
        if post["id"] == id:
            return post
        
def find_index(id):
    for index, post in enumerate(my_posts): # enumerate speichert den post , als auch den index als tuple
        if post["id"] == id:
            print(index)
            return index

@app.get("/myposts/{id}") # bei zukünftige urls aufpassen wenn man ein anderen path bspw /myposts/latest nennt , wird latest als id interpretiert und dann error, am besten dann noch weiteres feld hinzugügen /abc
def myposts_specific(id: int, res: Response): # : int ist ein hint, welcher datentyp von id erwartet wird. im default ein string , deshalb muss man es konvertieren weil bei find_post integer sonst mit string verglicehn wird
    post = find_post(id)
    if not post:# wenn post leer 
        #res.status_code = status.HTTP_404_NOT_FOUND   # res ist ein Response objekt von fastapi, status code setzen , status. um nicht sich status codes merken zu müssen
        #return {"message": f"post with id: {id} was not found"}# schlechtere version , besser mit httpException library
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"post with id: {id} was not found") # --> besser , status_code und detail müssen so heißen
        #raise stoppt funktion und sendet exception an client, dann Response weglassen in funktion
    return {"data": post}

@app.delete("/myposts/{id}" , status_code= status.HTTP_204_NO_CONTENT) #status code zum löschen
def delete_post(id: int):
    post = find_post(id)
    if not post:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail = f"post with id{id} does not exist")
    my_posts.remove(post) #löscht genau den eintrag
    # bei fast api gibt es einen error wenn man versucht daten zu schicken nach 204 status code, deshalb nicht möglich
    return Response(status_code= status.HTTP_204_NO_CONTENT) # nur so ein response möglich , theoretisch kann man anderen status code nehmen oder nachricht im header senden um im frontend auszulesen: 
#response.headers["X-Message"] = f"Post {id} deleted successfully"



@app.put("/myposts/{id}")
def update_post(id: int , post: Posts):
    index = find_index(id)
    if index is None: # kein if not , weil falls 0 wird es als false behandelt
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail = f"post with id{id} does not exist")
    posting = post.model_dump()
    posting["id"] = id
    my_posts[index] = posting
    return {"data": posting}
