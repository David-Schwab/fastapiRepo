from tkinter import E

from app.calculations import add, BankAccount
import pytest

@pytest.fixture # fixture ist eine Funktion, die Testdaten oder Testobjekte bereitstellt, die in mehreren Tests verwendet werden können.
def new_bank_account():
    return BankAccount()

@pytest.mark.parametrize("num1, num2, expected_sum", [(3, 2, 5), (10, 15, 25), (0, 0, 0), (-1, 1, 0)]) # parametrize macht es möglich mehrere testfälle mit unterschiedlichen werten zu testen, müssen tuple listen sein
def test_add(num1, num2, expected_sum):

    assert add(num1, num2) == expected_sum    # assert macht , wenn der wert dahinter True ist, passiert nichts, wenn er False ist , wird ein Fehler ausgelöst


def test_bank_account_zero(new_bank_account): # new_bank_account ist das fixture , das hier als argument übergeben wird, damit ich es in diesem test benutzen kann
   # bank1 = BankAccount(50)            #fixture läuft bevor dieser zeile und erstellt ein neues bankkonto mit balance 0, das dann in new_bank_account gespeichert wird
    assert new_bank_account.balance == 0

def test_bank_account():

    bank1 = BankAccount(50)
    assert bank1.balance == 50

def test_bank_2():
    bank1 = BankAccount(50)
    bank1.withdraw(25)
    assert bank1.balance == 25

def test_bank_3():
    bank1 = BankAccount(50)
    bank1.deposit(25)
    assert bank1.balance == 75


def test_bank_4():          #wir erwarten das hier ien fehler auftritt, weil wir mehr geld abheben als auf dem konto ist
    with pytest.raises(Exception): # mit pytest.raises sagen wir, dass wir erwarten, dass hier ein Fehler auftritt, wenn kein Fehler auftritt, schlägt der Test fehl
        bank1 = BankAccount(10)
        bank1.withdraw(20)
        assert bank1.balance == -10
