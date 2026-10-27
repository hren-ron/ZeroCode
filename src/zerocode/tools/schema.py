from dataclasses import dataclass
from typing import Any

SUPPORTED_TYPES = {
    "string",
    "integer",
    "number",
    "boolean",
    "object",
    "array",
}

@dataclass(frozen=True)
class ToolParameter:
    """Definition of a single tool parameter."""

    name: str
    type: str
    description: str = ""
    required: bool = True

    def __post_init__(self) -> None:

        if not self.name.strip():
            raise ValueError("Parameter name must not be empty")

        if self.type not in SUPPORTED_TYPES:
            raise ValueError(f"Unsupported parameter type: {self.type}")


@dataclass(frozen=True)
class ToolSchema:
    """Schema defining and validating tool arguments."""

    parameters: tuple[ToolParameter, ...] = ()
    allow_extra: bool = False

    def __post_init__(self) -> None:

        if not all(
                isinstance(parameter, ToolParameter)
                for parameter in self.parameters
        ):
            raise TypeError(
                "All parameters must be ToolParameter instances"
            )
        
        names = [parameter.name for parameter in self.parameters]

        if len(names) != len(set(names)):
            raise ValueError("Duplicate parameter names are not allowed")



    def validate(self, arguments: dict[str, Any]) -> None:
        """Validate arguments; return None when validation succeeds."""

        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must be a dictionary")

        parameter_map = {
            parameter.name: parameter
            for parameter in self.parameters
        }

        # Check required parameters.
        for parameter in self.parameters:

            if parameter.required and parameter.name not in arguments:
                raise ValueError(
                    f"Missing required parameter: {parameter.name}"
                )

        # Reject parameters not defined in the schema.
        if not self.allow_extra:
            extra_names = arguments.keys() - parameter_map.keys()

            if extra_names:
                names = ", ".join(sorted(extra_names))
                raise ValueError(f"Unexpected parameter(s): {names}")

        # Validate values that were provided.

        for name, value in arguments.items():
            parameter = parameter_map.get(name)

            # Extra parameters are allowed when allow_extra=True.
            if parameter is None:
                continue

            if not self._matches_type(value, parameter.type):
                raise TypeError(
                    f"Invalid type for parameter '{name}': "
                    f"expected {parameter.type}, "
                    f"got {type(value).__name__}"
                )

    @staticmethod
    def _matches_type(value: Any, expected_type: str) -> bool:
        """Return whether a value matches a supported schema type."""

        if expected_type == "string":
            return isinstance(value, str)

        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)

        if expected_type == "number":
            return (
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
            )

        if expected_type == "boolean":
            return isinstance(value, bool)

        if expected_type == "object":
            return isinstance(value, dict)

        if expected_type == "array":
            return isinstance(value, list)
            # ToolParameter already rejects unsupported types.
        return False


