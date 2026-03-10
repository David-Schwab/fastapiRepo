# für test tutorial

def add(x: int, y: int) -> int:
    return x + y


class InsufficientFunds(Exception): # test erbt von exception, damit wir später sagen können, dass wir erwarten, dass hier ein Fehler auftritt
    pass

class BankAccount():
    def __init__(self, balance = 0):
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if amount>self.balance:
            raise InsufficientFunds("Not enough balance")
        self.balance -= amount

    def collect_interest(self):
        self.balance *= 1.1
