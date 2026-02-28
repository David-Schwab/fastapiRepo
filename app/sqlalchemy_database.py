#sql alchemy braucht einen database driver wie psycopg (für postgres)

#SQLAlchemy ist ein ORM (Object-Relational Mapper), also ein Werkzeug, das Python-Objekte auf Datenbank-Tabellen abbildet.

#Du arbeitest mit Python-Klassen statt rohem SQL.
#SQLAlchemy übersetzt Python-Befehle in SQL für die Datenbank.
# asntatt sql queries zu schreiben interagiert man mit einer tabel - class und das ORM übersetzt die funktionen und anfragen in sql im hintergrund
#Datei soll eigentlich heißen database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import settings

DATABASE_URL = f"postgresql+asyncpg://{settings.db_username}:{settings.db_password}@{settings.db_hostname}:{settings.db_port}/{settings.db_name}"



# ----------------------------
# Async Engine & Session Factory
# ----------------------------
engine = create_async_engine( # engine verwaltet die connections und führt sql über Sessions über die database_url aus
    DATABASE_URL, # sagt welche datenbank und welcher treiber
  #  echo=True,        # SQL-Logs in Konsole , # in produktion ausstellen
    pool_size=10,
    max_overflow=5,
)

async_session = sessionmaker( # session fabrik gibt den bauplan für eine connection
    engine, # connection und pool manager # type: ignore
    class_=AsyncSession, # sagt ich arbeite async nicht sync
    expire_on_commit=False, #FastAPI-Standard bei async
    autoflush=False # „schreibe Änderungen zur DB, aber committe noch nicht“
)# type: ignore


# ----------------------------
# Base-Klasse für Models
# ----------------------------
class Base(DeclarativeBase): #erstellt orm registry, sammelt alle models die davon erben und baut daraus die metadaten und verbindet auch die klasse
    pass # pass macht nichts --> ezeugt die klasse ohen attribute oder methoden
#Alles, was von Base erbt, gehört zur selben Datenbank-Welt, Diese von Objekten (Tabellen-)Sammlung nennt SQLAlchemy Metadata.


# ----------------------------
# Lifespan für Tabellen-Erstellung
# ----------------------------
@asynccontextmanager # managed was passieren soll wenn app startet und beendet wird (alles vor yield beim start, alles nach yield beim beenden)
async def lifespan(app: FastAPI): # funktion wird aufgeruden bei app start

    from . import models  #besser hier erst models importieren , nachdem es base schon gibt, weil models.py importiert base, erst dann können die tabellen erstellt werden


    # Tabellen async erstellen
    async with engine.begin() as conn: #engine begin öffnet eine verbindung
        await conn.run_sync(models.Base.metadata.create_all) #Base geht Liste durch und erstellt alle Tabellen, die Base kennt (falls si enocht nicht existieren). kann man löschen wenn man alembic benutzt
        #conn run_sync , weil create all kein async code ist

    app.state.async_session = async_session #session fabrik wird an die app bereitgestellt, damit die app weiß woher sie verbindungen bekommt
    yield # app hier darf app requests annehmen
    await engine.dispose() # bei stopp werden alle offenen verbindungen geschlossen
    print("Engine disposed, App shutdown complete")

# ----------------------------
# Async Dependency
# ----------------------------
async def get_db():
    async with async_session() as session: #eine session wird geholt (engine gibt connection aus pool) # type: ignore
        yield session  #session wird benutzt
        #session bzw verbindung wird zurückgegeben
