import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool  # ← NEU
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.oauth2 import create_access_token
from app.sqlalchemy_database import Base, get_db
import uuid
from app import models

TEST_DATABASE_URL      = "postgresql+asyncpg://postgres:david@localhost:5432/fastapi_test_db"
TEST_DATABASE_URL_SYNC = "postgresql+psycopg2://postgres:david@localhost:5432/fastapi_test_db"

# ← NullPool hinzufügen: keine Verbindungen werden zwischen Tests gecacht
engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool) #Mit NullPool wird nach jedem Test die Verbindung sofort geschlossen
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session: #erstellt eine db verbindung immer wenn get_db aufgerufen wird
        yield session # nach test wird die verbindung automatisch geschlossen, weil wir async with verwenden, yield session gibt die session ab

# Diese Fixture → für direkte DB-Zugriffe in Tests
@pytest.fixture()
async def session():
    async with TestingSessionLocal() as s:
        yield s

app.dependency_overrides[get_db] = override_get_db  #immer wenn get_db von der api aufgerufen wird
# stattdessen override_get_db aufgerufen, damit die tests mit der testdatenbank arbeiten und nicht mit der echten datenbank


#scope = session --> bei jedem gesamt testlauf, default nach jeder funktion, autouse=True --> automatisch für alle tests verwenden
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    sync_engine = create_engine(TEST_DATABASE_URL_SYNC)
    Base.metadata.create_all(bind=sync_engine) #tabelle erstellen
    yield
    Base.metadata.drop_all(bind=sync_engine) #tabelle löschen, damit die tests immer mit einer sauberen datenbank starten
    sync_engine.dispose() # die verbindung zum datenbankserver schließen

@pytest.fixture(autouse=True)
def clean_tables():
    sync_engine = create_engine(TEST_DATABASE_URL_SYNC)
    with sync_engine.begin() as conn:   #with stellt sicher die Verbindung wird am Ende automatisch geschlossen., begin startet eine Transaktion, die am Ende automatisch commited oder rollbacked wird
        for table in reversed(Base.metadata.sorted_tables): #Base.metadata.sorted_tables gibt alle Tabellen in der richtigen Reihenfolge zurück, basierend auf ihren Foreign Keys.
            #reversed() dreht die Reihenfolge um — wichtig weil man zuerst Tabellen mit Foreign Keys leeren muss, bevor man die Tabellen leert auf die sie
            conn.execute(table.delete())
    yield
    sync_engine.dispose()

@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture()
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
#  transport=ASGITransport(app=app) bedeutet: anstatt echte HTTP-Anfragen über das Netzwerk zu schicken, werden die Anfragen direkt an die FastAPI-App weitergeleitet
# — schneller und kein echter Server nötig. base_url="http://test" ist eine Dummy-URL die httpx braucht, hat aber keine echte Bedeutung.




@pytest.fixture()
async def create_user(async_client):
    email = f"test_{uuid.uuid4().hex}@example.com"
    login_data = {"email": email, "password": "testpassword2"}
    response = await async_client.post("/users/", json=login_data)
    assert response.status_code == 201
    test_user = response.json()
    test_user["password"] = login_data["password"]
    return test_user

@pytest.fixture()
async def token(create_user):
    return create_access_token(data={"sub": str(create_user["id"])})

@pytest.fixture()
async def authorized_client(async_client, token):
    async_client.headers = {**async_client.headers, "Authorization": f"Bearer {token}"}
    return async_client



#Die Faustregel ist simpel: brauchst du Fixtures wie create_user, authorized_client oder token? → async_client.
# Diese Fixtures sind alle async, also muss auch der Test async sein.



@pytest.fixture()
async def create_posts(create_user, session):
    posts_data = [
        {"title": "Post 1", "content": "Content 1", "user_id": create_user["id"]},
        {"title": "Post 2", "content": "Content 2", "user_id": create_user["id"]},
        {"title": "Post 3", "content": "Content 3", "user_id": create_user["id"]},
    ]


    mapped_posts = list(map(lambda data: models.Post(**data), posts_data))
    posts = list(mapped_posts)
    session.add_all(posts) #dieses objekt soll später gespeichert werden, spricht noch nicht mit der datenbank deswegen kein await
    await session.commit()
