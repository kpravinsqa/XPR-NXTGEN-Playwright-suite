import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    username: str = os.getenv("TEST_USERNAME", "planner")
    password: str = os.getenv("TEST_PASSWORD", "Plan@123")
    viewer: tuple = ("viewer", "Plan@123")
    default_credentials: dict = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "default_credentials", {"username": self.username, "password": self.password})


settings = Settings()
