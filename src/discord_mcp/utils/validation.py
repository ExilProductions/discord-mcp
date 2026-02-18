from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from pydantic.type_adapter import TypeAdapter

T = TypeVar("T", bound=BaseModel)


def validate_data(model_class: type[T], data: dict[str, Any]) -> T:
    try:
        return model_class.model_validate(data)
    except ValidationError as e:
        from discord_mcp.discord.exceptions import ValidationException

        raise ValidationException(errors=e.errors())


def validate_list(model_class: type[T], data: list[dict[str, Any]]) -> list[T]:
    type_adapter: TypeAdapter[list[T]] = TypeAdapter(list[model_class])
    try:
        return type_adapter.validate_python(data)
    except ValidationError as e:
        from discord_mcp.discord.exceptions import ValidationException

        raise ValidationException(errors=e.errors())
