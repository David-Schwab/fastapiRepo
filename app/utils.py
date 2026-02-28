from argon2 import PasswordHasher


ph = PasswordHasher(
    time_cost=3, #Mehr = langsamer = sicherer.
    memory_cost=65536, # 64 MB RAM pro Hash Mehr RAM = schwerer zu knacken
    parallelism=4 # Wie viele CPU Threads genutzt werden. Mehr Threads:schneller legitimer Loginfür Angreifer auch schwerer zu optimieren
)


def hasher(password: str):
    hashed_passowrd = ph.hash(password)
    return hashed_passowrd

def verify_passwords(password, hashed_password):
        try:
            return ph.verify(hashed_password, password) # wenn gleich ---> true , anderen false wird eine exception geworfen, deshalb muss man manuell die exception bestimmen
        except:
             return False
  
    