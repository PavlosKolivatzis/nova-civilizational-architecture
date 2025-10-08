from tools.fuzzy_loader import find_file


def test_ignores_virtualenv(tmp_path):
    # real file we expect to find
    target = tmp_path / "foo.txt"
    target.write_text("data")

    # same name inside a virtualenv-like directory should be ignored
    venv_file = tmp_path / ".venv" / "foo.txt"
    venv_file.parent.mkdir()
    venv_file.write_text("should be ignored")

    found = find_file("foo", base=str(tmp_path))
    assert found == str(target)
