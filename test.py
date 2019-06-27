import string
from random import choice

letters = [choice(string.ascii_letters+string.digits) for _ in range(10)]


print("".join(letters))