
from fastapi import FastAPI
from .sqlalchemy_database import  lifespan
from . routers import post, user, authentication, like
from fastapi.middleware.cors import CORSMiddleware
# zum starten: fastapi dev app/main.py


app = FastAPI(lifespan=lifespan)

origins = ["https://www.google.com", "*"] #danach kann man in browser console auf google eingeben fetch("http://
app.add_middleware(
    CORSMiddleware, # wenn jemand ein request an app sendet, dann wird zuerst der cors middleware aufgerufen
    allow_origins=origins, # wer ist erlaubt auf die api zuzugreifen
    allow_credentials=True,
    allow_methods=["*"], # man kann hier bestimmte http methoden erlauben, z.b. nur get und post
    allow_headers=["*"], # selbe gilt für header, z.b. nur content type und authorization header erlauben
)

#jeder router ist eine Sammlung von Endpoints
app.include_router(post.router)  #importiert alle routes
app.include_router(user.router)
app.include_router(authentication.router)
app.include_router(like.router)

@app.get("/") # root endpoint
async def root():
    return {"message": "Hello World"}

