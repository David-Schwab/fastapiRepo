import uuid

import jwt
import pytest
from app.schemas import ResUser, Token
from app.config import settings
#tests


def test_root(client):
    response = client.get("/") #client sendet eine get anfrage an den root endpoint
    assert response.status_code == 200 # wir erwarten, dass die antwort einen status code von 200 hat, was bedeutet, dass die anfrage erfolgreich war
    assert response.json() == {"message": "Hello World"} # wir erwarten, dass diese antwort


def test_user_create(client):
    email = f"test_{uuid.uuid4().hex}@example.com"
    response = client.post("/users/", json={"email": email, "password": "testpassword2"})
    print("res:", response.json())
    new_user = ResUser(**response.json()) # wir erstellen ein neues UserCreate Objekt aus der Antwort der API, damit wir die Daten validieren können
    #wenn das schema nicht übereinstimmt, wird hier ein Fehler ausgelöst, weil die API wahrscheinlich eine Fehlermeldung zurückgibt, die nicht dem UserCreate Schema entspricht
    assert response.status_code == 201 # wir erwarten, dass die antwort einen status code von 201 hat, was bedeutet, dass ein neues objekt erstellt wurde

# hier ist es wichtig , dass wird /users/ machen und nicht nur /users, so wie man über postman auf den endpoint zugreift
# fastapi macht automatisch einen redirect von /users zu /users/ , aber bei einem redirect wird der status code 307 zurückgegeben
#der test würde dann fehlschlagen, deshalb muss man hier die URL genau so angeben, wie sie in der API definiert ist


async def test_login_user(async_client, create_user):
    response = await async_client.post("/login", data={"username": create_user["email"], "password": create_user["password"]}) # muss data sein statt json, weil die API erwartet, dass die Daten im form-data Format gesendet werden
    login_user = Token(**response.json()) # wir erstellen ein neues Token Objekt aus der Antwort der API, damit wir die Daten validieren können
    payload = jwt.decode(login_user.access_token, settings.secretkey, algorithms=[settings.algorithm])
    assert int(payload["sub"]) == create_user["id"] # wir erwarten, dass die user_id im payload des Tokens der id des erstellten Users entspricht
    assert login_user.token_type == "bearer" # wir erwarten, dass der token type bearer ist, weil die API das so definiert hat
    assert response.status_code == 200 # wir erwarten, dass die antwort einen status code von 200 hat, was bedeutet, dass die anfrage erfolgreich war
