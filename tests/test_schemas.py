"""Schema discovery: registration, nesting, collisions and invalid files."""

import logging
import sys

import pytest

from runapi.schemas import (
    BaseSchema,
    PaginatedResponse,
    PaginationParams,
    SchemaRegistry,
    get_schema,
    list_schemas,
    load_schemas,
)


@pytest.fixture(autouse=True)
def clean_registry():
    SchemaRegistry.clear()
    yield
    SchemaRegistry.clear()
    for name in [m for m in sys.modules if m.startswith("schemas")]:
        del sys.modules[name]


def write(root, rel, body):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


USER = "from pydantic import BaseModel\n\nclass User(BaseModel):\n    name: str\n"


def test_registers_short_and_full_names(tmp_path):
    write(tmp_path, "user.py", USER)
    load_schemas(tmp_path)
    assert get_schema("User") is not None
    assert get_schema("schemas.user.User") is get_schema("User")
    assert {"User", "schemas.user.User"} <= set(list_schemas())


def test_nested_directories_are_discovered(tmp_path):
    write(tmp_path, "billing/invoice.py", USER.replace("User", "Invoice"))
    load_schemas(tmp_path)
    assert get_schema("Invoice") is not None
    assert get_schema("schemas.billing.invoice.Invoice") is not None


def test_missing_directory_returns_empty(tmp_path):
    assert load_schemas(tmp_path / "nope") == {}


def test_private_and_non_model_names_are_ignored(tmp_path):
    write(
        tmp_path,
        "mixed.py",
        "from pydantic import BaseModel\n\n"
        "class _Hidden(BaseModel):\n    x: int\n\n"
        "class Visible(BaseModel):\n    x: int\n\n"
        "class NotAModel:\n    pass\n",
    )
    load_schemas(tmp_path)
    assert get_schema("Visible") is not None
    assert get_schema("_Hidden") is None
    assert get_schema("NotAModel") is None


def test_invalid_file_is_logged_and_others_still_load(tmp_path, caplog):
    write(tmp_path, "good.py", USER)
    write(tmp_path, "broken.py", "this is not python (\n")
    write(tmp_path, "bad_import.py", "import module_that_does_not_exist\n")
    with caplog.at_level(logging.ERROR, logger="runapi.schemas"):
        load_schemas(tmp_path)
    assert get_schema("User") is not None
    failures = [r.getMessage() for r in caplog.records if "Failed to load schema" in r.getMessage()]
    assert len(failures) == 2


def test_duplicate_names_warn_and_last_wins(tmp_path, caplog):
    write(tmp_path, "a.py", USER)
    write(tmp_path, "b.py", USER)
    with caplog.at_level(logging.WARNING, logger="runapi.schemas"):
        load_schemas(tmp_path)
    assert any("collision" in r.getMessage() for r in caplog.records)
    # both stay reachable through their full paths
    assert get_schema("schemas.a.User") is not get_schema("schemas.b.User")
    assert get_schema("User") is get_schema("schemas.b.User")


def test_registry_clear_resets_everything(tmp_path):
    write(tmp_path, "user.py", USER)
    load_schemas(tmp_path)
    SchemaRegistry.clear()
    assert list_schemas() == []
    assert SchemaRegistry.get_module("schemas.user") is None


def test_unknown_schema_is_none():
    assert get_schema("DoesNotExist") is None


# ---- built-in schema classes --------------------------------------------------------------


def test_base_schema_validation_errors():
    from pydantic import ValidationError

    class Item(BaseSchema):
        name: str
        qty: int

    with pytest.raises(ValidationError):
        Item(name="x", qty="not-a-number")
    with pytest.raises(ValidationError):
        Item(qty=1)


def test_pagination_params_bounds_and_offset():
    from pydantic import ValidationError

    params = PaginationParams(page=3, page_size=20)
    assert params.offset == 40 and params.limit == 20
    with pytest.raises(ValidationError):
        PaginationParams(page=0)
    with pytest.raises(ValidationError):
        PaginationParams(page_size=100000)


def test_paginated_response_math():
    result = PaginatedResponse.create(items=[1, 2, 3], total=25, page=2, page_size=10)
    assert result.total == 25 and result.page == 2
    assert result.pages == 3
