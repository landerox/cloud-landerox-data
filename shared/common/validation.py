"""Contract validation utilities.

Validates incoming payloads against Pydantic contracts. On failure the
helper raises :class:`ContractValidationError` with structured log context;
callers at the boundary decide DLQ routing (see
``docs/guides/error-handling.md``).
"""

import logging
from typing import Any

from pydantic import BaseModel, ValidationError

from .exceptions import ContractValidationError


def validate_contract[T: BaseModel](data: dict[str, Any], contract_class: type[T]) -> T:
    """Validate ``data`` against ``contract_class``.

    Args:
        data: Mapping of field names to raw values.
        contract_class: Pydantic model the payload must satisfy.

    Returns:
        The validated model instance.

    Raises:
        ContractValidationError: If the payload fails Pydantic validation.
            The original ``ValidationError`` is chained via ``__cause__``.
    """
    try:
        return contract_class(**data)
    except ValidationError as err:
        # Redact input values: pydantic's err.errors() includes the offending
        # field values, which can be PII. Keep only loc/type/msg so the log
        # is triageable without leaking payload content.
        safe_errors = [
            {"loc": list(e["loc"]), "type": e["type"], "msg": e["msg"]}
            for e in err.errors()
        ]
        logging.error(
            "contract validation failed",
            extra={
                "extra_fields": {
                    "reason_code": ContractValidationError.reason_code,
                    "contract": contract_class.__name__,
                    "error_count": len(safe_errors),
                    "errors": safe_errors,
                }
            },
        )
        raise ContractValidationError(
            f"payload does not satisfy contract {contract_class.__name__}"
        ) from err
