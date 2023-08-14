import random
import string

def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def generate_random_user():
    username = generate_random_string(5)
    email = f"{generate_random_string(5)}@example.com"
    phoneNumber = "123456789"
    dni = "12345678"
    fullName = "Test User"
    password = "testpassword"

    user_data = {
        "username": username,
        "email": email,
        "phoneNumber": phoneNumber,
        "dni": dni,
        "fullName": fullName,
        "password": password
    }

    return user_data