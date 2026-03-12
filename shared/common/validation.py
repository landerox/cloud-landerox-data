"""
Contract validation utilities for Data Ingestion.

This module provides base patterns for validating incoming data against
pre-defined contracts (schemas) using Pydantic.
"""

import logging
from typing import Any

from pydantic import BaseModel, ValidationError


def validate_contract[T: BaseModel](
    data: dict[str, Any], contract_class: type[T]
) -> T | None:
    """
    Validates a data dictionary against a Pydantic contract class.

    Returns the validated model instance or None if validation fails.
    Logs errors as structured JSON if logging is configured.
    """
    try:
        return contract_class(**data)
    except ValidationError as e:
        logging.error(
            "Contract validation failed",
            extra={
                "extra_fields": {
                    "errors": e.errors(),
                    "input_data": data,
                    "contract": contract_class.__name__,
                }
            },
        )
        return None
