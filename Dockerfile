FROM python:3.11-slim

WORKDIR /usr/src/app
#von diesem directory aus wird gearbeitet
COPY requirements.txt .
 #kopiert die requirements.txt in das Arbeitsverzeichnis , . heißt im workdir

RUN python -m pip install --upgrade pip \
    &&  pip install --no-cache-dir -r requirements.txt
#zuerst pip upgraden , dann die benötigten pakete installieren

COPY . .
#kopiert alle dateien des fastapi projekts in das Arbeitsverzeichnis

#docker macht nur das was nötig ist, wenn sich die requirements.txt nicht ändert, wird der pip install schritt nicht erneut ausgeführt, da er bereits im cache ist
#deshalb ist es wichtig, die requirements.txt vor dem kopieren der restlichen dateien zu kopieren, damit der cache genutzt werden kann

CMD ["uvicorn", "app.main:app", "--host","0.0.0.0", "--port", "8000"]
# startet den uvicorn server im container

