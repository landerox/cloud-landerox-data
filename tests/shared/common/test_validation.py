"""Unit tests for contract validation utilities."""

from pydantic import BaseModel

from shared.common.validation import validate_contract


class User(BaseModel):
    id: int
    name: str


class Nested(BaseModel):
    user: User
    tags: list[str] = []


def test_validate_contract_success():
    data = {"id": 1, "name": "Gemini"}
    result = validate_contract(data, User)
    assert result is not None
    assert result.id == 1
    assert result.name == "Gemini"


def test_validate_contract_failure():
    data = {"id": "invalid", "name": "Gemini"}
    result = validate_contract(data, User)
    assert result is None


def test_validate_contract_empty_data():
    result = validate_contract({}, User)
    assert result is None


def test_validate_contract_extra_fields_ignored():
    data = {"id": 1, "name": "Claude", "extra": "ignored"}
    result = validate_contract(data, User)
    assert result is not None
    assert result.id == 1
    assert not hasattr(result, "extra")


def test_validate_contract_nested_model():
    data = {"user": {"id": 1, "name": "Claude"}, "tags": ["a", "b"]}
    result = validate_contract(data, Nested)
    assert result is not None
    assert result.user.id == 1
    assert result.tags == ["a", "b"]


def test_validate_contract_nested_model_invalid():
    data = {"user": {"id": "bad"}, "tags": ["a"]}
    result = validate_contract(data, Nested)
    assert result is None
