from __future__ import annotations


def _reset_dotenv_state() -> None:
    """`_load_dotenv_once()` caches after the first call per-process; force
    it to re-run so each test gets an isolated `.env` lookup.
    """
    import fastframe.core.settings as settings_module

    settings_module._dotenv_loaded = False


def test_dotenv_file_is_loaded_into_environ(tmp_path, monkeypatch) -> None:
    _reset_dotenv_state()
    (tmp_path / ".env").write_text("FASTFRAME_TEST_DOTENV_VAR=from_dotenv\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FASTFRAME_TEST_DOTENV_VAR", raising=False)

    from fastframe.core.settings import _load_dotenv_once

    _load_dotenv_once()

    import os

    assert os.environ.get("FASTFRAME_TEST_DOTENV_VAR") == "from_dotenv"


def test_real_env_var_wins_over_dotenv(tmp_path, monkeypatch) -> None:
    _reset_dotenv_state()
    (tmp_path / ".env").write_text("FASTFRAME_TEST_DOTENV_VAR=from_dotenv\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FASTFRAME_TEST_DOTENV_VAR", "from_real_env")

    from fastframe.core.settings import _load_dotenv_once

    _load_dotenv_once()

    import os

    assert os.environ.get("FASTFRAME_TEST_DOTENV_VAR") == "from_real_env"


def test_dotenv_loading_is_cached_per_process(tmp_path, monkeypatch) -> None:
    """Regression test for the real bug hit while dogfooding: without
    `usecwd=True`, python-dotenv's `find_dotenv()` searches upward from the
    *caller's file location* (deep inside the installed `fastframe`
    package), never finding a project's `.env` at all. This also verifies
    the per-process caching flag flips correctly.
    """
    import fastframe.core.settings as settings_module

    _reset_dotenv_state()
    assert settings_module._dotenv_loaded is False

    settings_module._load_dotenv_once()

    assert settings_module._dotenv_loaded is True
