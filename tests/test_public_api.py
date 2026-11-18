import runapi


def test_all_exports_resolve():
    missing = [name for name in runapi.__all__ if not hasattr(runapi, name)]
    assert not missing, f"listed in __all__ but not importable: {missing}"


def test_all_has_no_duplicates():
    assert len(runapi.__all__) == len(set(runapi.__all__))


def test_version_is_a_string():
    assert isinstance(runapi.__version__, str) and runapi.__version__
