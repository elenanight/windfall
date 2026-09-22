"""Tests for the JSON-backed config store."""

from __future__ import annotations

from windfall import Config


class TestConfig:
    def test_missing_file_falls_back_to_defaults(self, tmp_path) -> None:
        config = Config.load(tmp_path / "app.json", defaults={"header": "hi"})
        assert config.get("header") == "hi"
        assert config.get("absent", "dflt") == "dflt"

    def test_save_and_load_round_trip(self, tmp_path) -> None:
        path = tmp_path / "nested" / "app.json"
        Config(path, defaults={"header": "hi"}).set("border", "red").save()
        loaded = Config.load(path, defaults={"header": "hi"})
        assert loaded.get("header") == "hi"
        assert loaded.get("border") == "red"

    def test_saved_values_override_defaults(self, tmp_path) -> None:
        path = tmp_path / "app.json"
        Config(path, defaults={"header": "hi"}).set("header", "yo").save()
        assert Config.load(path, defaults={"header": "hi"}).get("header") == "yo"

    def test_corrupt_file_falls_back_to_defaults(self, tmp_path) -> None:
        path = tmp_path / "app.json"
        path.write_text("{nope", encoding="utf-8")
        assert Config.load(path, defaults={"header": "hi"}).get("header") == "hi"