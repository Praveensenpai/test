import random

from faker import Faker

fake = Faker()


def get_fake_user_data():
    valid_countries = [
        "United States",
        "Italy",
        "France",
        "Germany",
        "United Kingdom",
        "Spain",
        "Canada",
        "Australia",
        "Japan",
        "Brazil",
    ]
    valid_languages = ["Inglese"]
    valid_sex = ["Male", "Female"]

    user_data = {
        "surname": fake.last_name(),
        "name": fake.first_name(),
        "sex": random.choice(valid_sex),
        "country": random.choice(valid_countries),
        "city": fake.city(),
        "birthDate": fake.date_of_birth(minimum_age=18, maximum_age=80).strftime(
            "%d/%m/%Y"
        ),
        "email": fake.email(),
        "phone": f"{fake.numerify('##########')}",
        "language": random.choice(valid_languages),
    }

    return user_data


def generate_participants(count: int) -> list[dict[str, str]]:
    participants = []
    for _ in range(count):
        participants.append({"name": fake.first_name(), "surname": fake.last_name()})
    return participants
