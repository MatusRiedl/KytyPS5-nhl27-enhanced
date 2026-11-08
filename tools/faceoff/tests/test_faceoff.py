import json
import os
import shutil

import pytest

from faceoff import config, game, launch

# The release ships tools/nhl27/cfgGlobal.json; set FACEOFF_RC_DIR to test against an unpacked release instead.
HERE = os.path.dirname(os.path.abspath(__file__))
RC_DIR = os.environ.get("FACEOFF_RC_DIR", os.path.join(HERE, "..", "..", "nhl27"))
GAME = r"C:\Games\NHL27\PPSA34063-app0"


@pytest.fixture
def build(tmp_path):
    src = os.path.join(RC_DIR, "cfgGlobal.json")
    if not os.path.exists(src):
        pytest.skip("cfgGlobal.json not found")
    shutil.copy(src, tmp_path / "cfgGlobal.json")
    return str(tmp_path)


def test_load_defaults_from_rc4(build):
    s = config.load_settings(build)
    assert s == {"resolution": "R2560X1440", "fullscreen": False, "scale": 0.6667, "trophies": True}


def test_save_keeps_every_other_byte(build):
    path = os.path.join(build, "cfgGlobal.json")
    before = open(path, encoding="utf-8").read()
    config.save_setting(build, "resolution", "R1920X1080")
    config.save_setting(build, "fullscreen", True)
    config.save_setting(build, "scale", 0.85)
    config.save_setting(build, "trophies", False)
    after = open(path, encoding="utf-8").read()
    assert config.load_settings(build) == {"resolution": "R1920X1080", "fullscreen": True, "scale": 0.85, "trophies": False}
    expected = (before.replace('"R2560X1440"', '"R1920X1080"')
                .replace('"fullscreen_enabled": false', '"fullscreen_enabled": true')
                .replace('"KYTY_NHL_RES_SCALE": "0.6667"', '"KYTY_NHL_RES_SCALE": "0.85"')
                .replace('"trophy_enabled": true', '"trophy_enabled": false'))
    assert after == expected
    assert json.loads(before)["emu"]["env"].keys() == json.loads(after)["emu"]["env"].keys()


def test_bad_values_refused(build):
    with pytest.raises(ValueError):
        config.save_setting(build, "scale", 2)
    with pytest.raises(ValueError):
        config.save_setting(build, "resolution", "R999")


def test_missing_key_added(tmp_path):
    (tmp_path / "cfgGlobal.json").write_text('{"version": 1, "emu": {}}')
    config.save_setting(str(tmp_path), "scale", 0.5)
    assert config.load_settings(str(tmp_path))["scale"] == 0.5


def test_command_line_matches_ps1(build):
    env, args = launch.plan(build, GAME)
    assert args == rf'--game "{GAME}" --screen-width 2560 --screen-height 1440 --redzone'
    assert env["KYTY_NHL_RES_SCALE"] == "0.6667"
    assert env["KYTY_FLAG_FILE"] == ""
    config.save_setting(build, "fullscreen", True)
    _, args = launch.plan(build, "G")
    assert args == '--game "G" --screen-width 2560 --screen-height 1440 --fullscreen --redzone'


def test_game_folder_checks(tmp_path):
    assert not game.inspect("")["ok"]
    assert game.inspect(str(tmp_path / "nope"))["status"] == "Game folder not found"
    assert game.inspect(str(tmp_path))["status"] == "No eboot.bin in this folder"
    (tmp_path / "eboot.bin").write_bytes(b"x")
    (tmp_path / "sce_sys").mkdir()
    (tmp_path / "sce_sys" / "param.json").write_text(json.dumps(
        {"contentVersion": "01.003.001", "titleId": "PPSA34063", "localizedParameters": {"en-US": {"titleName": "NHL\u00ae 27"}}}),
        encoding="utf-8")
    info = game.inspect(str(tmp_path / "eboot.bin"))
    assert info["ok"] and info["title"] == "NHL 27" and info["version"] == "01.003.001"
    assert info["path"] == str(tmp_path)
