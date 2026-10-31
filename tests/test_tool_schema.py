
import pytest

from zerocode.tools.schema import ToolParameter, ToolSchema


@pytest.fixture
def schema() -> ToolSchema:
    return ToolSchema(
        parameters=(
            ToolParameter(
                name="path",
                type="string",
                description="Path to the file",
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="Text encoding",
                required=False,
            ),
            ToolParameter(
                name="line",
                type="integer",
                required=False,
            ),
        )
    )


def test_validate_accepts_valid_arguments(schema: ToolSchema) -> None:
    schema.validate({"path": "README.md"})
    schema.validate({
        "path": "README.md",
        "encoding": "utf-8",
        "line": 10,
    })


def test_validate_rejects_missing_required_parameter(
    schema: ToolSchema,
) -> None:
    with pytest.raises(ValueError, match="Missing required parameter"):
        schema.validate({})


def test_validate_rejects_unknown_parameter(
    schema: ToolSchema,
) -> None:
    with pytest.raises(ValueError, match="Unexpected parameter"):
        schema.validate({"path": "README.md", "extra": 1})


def test_validate_rejects_wrong_type(schema: ToolSchema) -> None:
    with pytest.raises(TypeError, match="expected string"):
        schema.validate({"path": 123})


def test_integer_rejects_boolean() -> None:
    integer_schema = ToolSchema(
        parameters=(
            ToolParameter(name="count", type="integer"),
        )
    )

    with pytest.raises(TypeError, match="expected integer"):
        integer_schema.validate({"count": True})


def test_number_accepts_integer_and_float() -> None:
    number_schema = ToolSchema(
        parameters=(
            ToolParameter(name="value", type="number"),
        )
    )

    number_schema.validate({"value": 1})
    number_schema.validate({"value": 1.5})


def test_number_rejects_boolean() -> None:
    number_schema = ToolSchema(
        parameters=(
            ToolParameter(name="value", type="number"),
        )
    )

    with pytest.raises(TypeError, match="expected number"):
        number_schema.validate({"value": True})


def test_validate_requires_dictionary(schema: ToolSchema) -> None:
    with pytest.raises(TypeError, match="must be a dictionary"):
        schema.validate(["README.md"])  # type: ignore[arg-type]


def test_schema_rejects_duplicate_parameter_names() -> None:
    with pytest.raises(ValueError, match="Duplicate parameter names"):
        ToolSchema(
            parameters=(
                ToolParameter(name="path", type="string"),
                ToolParameter(name="path", type="integer"),
            )
        )


def test_parameter_rejects_unsupported_type() -> None:
    with pytest.raises(ValueError, match="Unsupported parameter type"):
        ToolParameter(name="path", type="file")


def test_schema_can_allow_extra_parameters() -> None:
    permissive_schema = ToolSchema(
        parameters=(
            ToolParameter(name="path", type="string"),
        ),
        allow_extra=True,
    )

    permissive_schema.validate({
        "path": "README.md",
        "custom_option": 123,
    })

def test_to_json_schema() -> None:
    schema = ToolSchema(
        parameters=(
            ToolParameter(
                name="path",
                type="string",
                description="File path",
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="Text encoding",
                required=False,
            ),
        )
    )

    result = schema.to_json_schema()

    assert result == {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path",
            },
            "encoding": {
                "type": "string",
                "description": "Text encoding",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    }

def test_to_json_schema_without_parameters() -> None:
    schema = ToolSchema()

    result = schema.to_json_schema()

    assert result == {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }