"""Unit tests for LocData Code paths and configuration."""

from pathlib import Path
from locdata_code.paths import get_locdata_home, get_project_config_path, get_project_memory_path
from locdata_code.config import LocDataConfig
from locdata_code.approval_mode import ApprovalMode


def test_paths(tmp_path):
    home = get_locdata_home()
    assert home.exists()
    assert home.name == ".locdata"

    proj_cfg = get_project_config_path(tmp_path)
    assert proj_cfg == tmp_path / ".locdata" / "config.toml"


def test_config_defaults(tmp_path):
    cfg = LocDataConfig.load(project_root=tmp_path)
    assert cfg.approval_mode == ApprovalMode.PROMPT
    assert cfg.enable_web_search is True
    assert cfg.model.temperature == 0.2


def test_config_save_and_load(tmp_path):
    cfg = LocDataConfig.load(project_root=tmp_path)
    cfg.approval_mode = ApprovalMode.BYPASS
    cfg.model.model = "sensenova-6.8-flash"
    cfg.save_project(project_root=tmp_path)

    loaded = LocDataConfig.load(project_root=tmp_path)
    assert loaded.approval_mode == ApprovalMode.BYPASS
    assert loaded.model.model == "sensenova-6.8-flash"
