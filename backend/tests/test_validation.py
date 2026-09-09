import pytest
from fastapi import HTTPException

from app.schemas.api import Definition, Node
from app.services.validation import validate_definition


def test_valid():
    validate_definition(Definition(nodes=[Node(id="a"), Node(id="b", depends_on=["a"])]))


def test_cycle():
    with pytest.raises(HTTPException):
        validate_definition(
            Definition(nodes=[Node(id="a", depends_on=["b"]), Node(id="b", depends_on=["a"])])
        )


def test_missing():
    with pytest.raises(HTTPException):
        validate_definition(Definition(nodes=[Node(id="a", depends_on=["x"])]))
