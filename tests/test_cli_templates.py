"""Every CLI template must render and (for Python templates) be valid Python."""

import ast
import re
from importlib import resources

import pytest

from runapi.cli._templates import class_name_for, render

TEMPLATE_DIR = resources.files("runapi.cli") / "templates"
CONTEXT = {
    "name": "my_widget",
    "class_name": "MyWidget",
    "project_name": "demo",
    "secret_key": "0" * 64,
}


def _all_templates():
    names = []
    for group in TEMPLATE_DIR.iterdir():
        if group.is_dir():
            names += [f"{group.name}/{f.name[: -len('.tmpl')]}" for f in group.iterdir()]
    return sorted(names)


def test_templates_found():
    assert len(_all_templates()) >= 15


@pytest.mark.parametrize("template", _all_templates())
def test_template_renders_cleanly(template):
    text = render(template, **CONTEXT)
    assert not re.search(r"@@\w+@@", text), "unreplaced placeholder"
    if template.endswith(".py") and "crud_service_footer" not in template:
        ast.parse(text)  # syntactically valid Python


def test_crud_footer_is_valid_after_service():
    ast.parse(
        render("generate/service.py", **CONTEXT)
        + render("generate/crud_service_footer.py", **CONTEXT)
    )


def test_render_reports_missing_values():
    with pytest.raises(KeyError, match="class_name"):
        render("generate/schema.py", name="x")


def test_class_name_for():
    assert class_name_for("my-thing_two") == "MyThingTwo"
    assert class_name_for("user") == "User"
