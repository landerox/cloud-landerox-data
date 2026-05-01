"""Unit tests for contract validation utilities."""

from pydantic import BaseModel, ValidationError
import pytest

from shared.common.exceptions import ContractValidationError
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
    assert result.id == 1
    assert result.name == "Gemini"


def test_validate_contract_failure_raises():
    data = {"id": "invalid", "name": "Gemini"}
    with pytest.raises(ContractValidationError) as exc_info:
        validate_contract(data, User)
    assert isinstance(exc_info.value.__cause__, ValidationError)
    assert exc_info.value.reason_code == "schema_invalid"


def test_validate_contract_empty_data_raises():
    with pytest.raises(ContractValidationError):
        validate_contract({}, User)


def test_validate_contract_extra_fields_ignored():
    data = {"id": 1, "name": "Claude", "extra": "ignored"}
    result = validate_contract(data, User)
    assert result.id == 1
    assert not hasattr(result, "extra")


def test_validate_contract_nested_model():
    data = {"user": {"id": 1, "name": "Claude"}, "tags": ["a", "b"]}
    result = validate_contract(data, Nested)
    assert result.user.id == 1
    assert result.tags == ["a", "b"]


def test_validate_contract_nested_model_invalid_raises():
    data = {"user": {"id": "bad"}, "tags": ["a"]}
    with pytest.raises(ContractValidationError):
        validate_contract(data, Nested)
