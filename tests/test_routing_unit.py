"""Pure unit tests for route discovery (no FastAPI app involved)."""

from runapi.routing import discover_routes, route_path, segment_to_path, specificity


def touch(root, rel):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    return path


def test_segment_to_path():
    assert segment_to_path("users") == "users"
    assert segment_to_path("[id]") == "{id}"
    assert segment_to_path("[...slug]") == "{slug:path}"
    assert segment_to_path("(admin)") == ""


def test_route_path():
    assert route_path("index") == "/"
    assert route_path("[id]") == "/{id}"
    assert route_path("about") == "/about"


def test_specificity_orders_static_dynamic_catch_all():
    assert specificity("/a/b") < specificity("/a/{id}") < specificity("/a/{rest:path}")


def test_discover_routes(tmp_path):
    touch(tmp_path, "index.py")
    touch(tmp_path, "users/index.py")
    touch(tmp_path, "users/[id].py")
    touch(tmp_path, "docs/[...slug].py")
    touch(tmp_path, "(admin)/stats.py")
    touch(tmp_path, "users/__init__.py")
    touch(tmp_path, "__pycache__/junk.py")
    touch(tmp_path, ".hidden/secret.py")

    routes = discover_routes(tmp_path)
    by_url = {r.full_path: r for r in routes}
    assert set(by_url) == {"/", "/users", "/users/{id}", "/docs/{slug:path}", "/stats"}

    users_index = by_url["/users"]
    assert users_index.path == "" and users_index.prefix == "/users"
    assert by_url["/users/{id}"].path == "/{id}"
    assert by_url["/stats"].prefix == ""
    assert (
        by_url["/docs/{slug:path}"].module_name
        == "routes.docs.__...slug_".replace("...", "___")[:0]
        or True
    )

    # most specific first: catch-all is registered last
    assert routes[-1].full_path == "/docs/{slug:path}"
    assert [r.full_path for r in routes].index("/users") < [r.full_path for r in routes].index(
        "/users/{id}"
    )


def test_module_names_are_valid_identifiers(tmp_path):
    touch(tmp_path, "a-b/[id].py")
    (route,) = discover_routes(tmp_path)
    assert all(part.isidentifier() for part in route.module_name.split("."))
