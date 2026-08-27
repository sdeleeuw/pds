from django.contrib.auth import get_user_model

User = get_user_model()


def create_user(**kwargs) -> User:
    defaults = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "password",
    }
    defaults.update(kwargs)
    password = defaults.pop("password")

    return User.objects.create_user(password=password, **defaults)
