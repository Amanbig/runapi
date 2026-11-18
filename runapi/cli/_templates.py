"""Tiny template renderer for the files the CLI generates.

Templates live in ``runapi/cli/templates`` as plain files so they can be read, diffed and
syntax-checked like any other code. Placeholders look like ``@@name@@``.
"""

import re
from importlib import resources
from typing import Dict

_PLACEHOLDER = re.compile(r"@@(\w+)@@")


def render(template: str, **context: str) -> str:
    """Render ``templates/<template>.tmpl`` replacing every ``@@key@@`` from ``context``."""
    text = (resources.files("runapi.cli") / "templates" / f"{template}.tmpl").read_text(
        encoding="utf-8"
    )
    missing = set(_PLACEHOLDER.findall(text)) - set(context)
    if missing:
        raise KeyError(f"Template {template!r} needs values for: {', '.join(sorted(missing))}")
    values: Dict[str, str] = {key: str(value) for key, value in context.items()}
    return _PLACEHOLDER.sub(lambda match: values[match.group(1)], text)


def class_name_for(name: str) -> str:
    """Convert ``my-thing`` / ``my_thing`` to ``MyThing``."""
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))
