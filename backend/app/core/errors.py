from dataclasses import dataclass


@dataclass(frozen=True)
class AppError(Exception):
    code: str
    message: str
