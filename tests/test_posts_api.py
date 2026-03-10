
from app import schemas
from typing import List
import pytest

async def test_get_post(authorized_client, create_posts):
    response = await authorized_client.get("/sqlalchemys/")
    print("res:", response.json())
    post_list = list(map(lambda post: schemas.ResPostWithLikes(**post), response.json())) # wir erstellen eine Liste von ResPost Objekten aus der Antwort der API, damit wir die Daten validieren können
    #response.json gibt eine liste zurück mit dictionarys, da wird durch itereirt und jeder post in der liste entpackt und in das schema ResPostWithLikes gepackt
    assert response.status_code == 200

def test_get_post_unauthorized(client, create_posts):
    response = client.get("/sqlalchemys/")
    assert response.status_code == 401

@pytest.mark.parametrize("title, content, published", [
    ("Test Post 1", "Test Content 1", False),("Test Post 2", "Test Content 2", None), ("Test Post 3", "Test Content 3", True)
])
async def test_create_post(authorized_client, title, content, published):

    body = {"title": title, "content": content}
    if published is not None:               # ← nur hinzufügen wenn angegeben
        body["published"] = published # --> published key word kommt nur in den body wenn auch angegeben, weil sonst ist es default True

    response = await authorized_client.post("/sqlalchemys/", json=body)

    created_post = schemas.ResPost(**response.json()) # wir erstellen ein neues ResPost Objekt aus der Antwort der API, damit wir die Daten validieren können
    assert response.status_code == 201
    assert created_post.title == title
    assert created_post.content == content

def test_create_post_unauthorized(client):
    response = client.post("/sqlalchemys/", json={"title": "Unauthorized Post", "content": "This should fail"})
    assert response.status_code == 401
