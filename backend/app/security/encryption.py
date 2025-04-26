from sqlalchemy.types import TypeDecorator, String
import os

class EncryptedString(TypeDecorator):
    """Mock encryption class for testing that just passes through values"""
    impl = String
    cache_ok = True

    def __init__(self, length=None):
        super().__init__(length)

    def process_bind_param(self, value: str, dialect) -> str:
        return value

    def process_result_value(self, value: str, dialect) -> str:
        return value 