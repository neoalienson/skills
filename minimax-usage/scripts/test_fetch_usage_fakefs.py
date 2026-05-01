#!/usr/bin/env python3
"""
Tests using pyfakefs for filesystem mocking via pytest fixture.
These tests replace the tempfile.mkdtemp() + os.chdir() pattern with in-memory filesystem.

Note: TestTimezoneWithFakeFs tests that involve zoneinfo.ZoneInfo() are skipped
because pyfakefs doesn't provide timezone data. Those tests use real filesystem
or mock zoneinfo directly instead.
"""
import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))

from run import (
    load_cookies, load_config, get_timezone,
    CookiesNotFoundError
)


@pytest.fixture
def fake_fs(fs):
    """Pyfakefs fixture - 'fs' is automatically provided by pyfakefs pytest plugin"""
    get_timezone.cache_clear()
    yield fs
    get_timezone.cache_clear()


class TestLoadCookiesWithFakeFs:
    def test_load_cookies_from_config_yml(self, fake_fs):
        fake_fs.create_file("config.yml", contents="minimax_cookies: test_cookie_from_yaml\n")
        with patch.dict(os.environ, {"MINIMAX_COOKIES": ""}):
            cookies = load_cookies()
            assert cookies == "test_cookie_from_yaml"

    def test_load_cookies_config_missing_field(self, fake_fs):
        fake_fs.create_file("my_config.yml", contents="timezone: UTC\n")
        with pytest.raises(CookiesNotFoundError) as exc_info:
            load_cookies("/my_config.yml")
        assert "does not contain 'minimax_cookies' field" in str(exc_info.value)

    def test_load_cookies_empty_value(self, fake_fs):
        fake_fs.create_file("config.yml", contents='minimax_cookies: ""\n')
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(CookiesNotFoundError) as exc_info:
                load_cookies()
            assert "No cookies found" in str(exc_info.value)

    def test_load_cookies_from_home_config(self, fake_fs):
        home_file = os.path.expanduser("~/.minimax_config.yml")
        fake_fs.create_file(home_file, contents="minimax_cookies: test_cookie_home\n")
        with patch.dict(os.environ, {"MINIMAX_COOKIES": ""}):
            cookies = load_cookies()
            assert cookies == "test_cookie_home"

    def test_load_cookies_from_specific_config_path(self, fake_fs):
        fake_fs.create_file("my_config.yml", contents="minimax_cookies: cookie_from_specific_path\n")
        with patch.dict(os.environ, {"MINIMAX_COOKIES": ""}):
            cookies = load_cookies("/my_config.yml")
            assert cookies == "cookie_from_specific_path"

    def test_c_config_overrides_env_var(self, fake_fs):
        fake_fs.create_file("my_config.yml", contents="minimax_cookies: cookie_from_config\n")
        with patch.dict(os.environ, {"MINIMAX_COOKIES": "cookie_from_env"}):
            cookies = load_cookies("/my_config.yml")
            assert cookies == "cookie_from_config"

    def test_load_config_success(self, fake_fs):
        fake_fs.create_file("config.yml", contents="minimax_cookies: yaml_cookie\ntimezone: Asia/Shanghai\n")
        config = load_config()
        assert config["minimax_cookies"] == "yaml_cookie"
        assert config["timezone"] == "Asia/Shanghai"

    def test_load_config_from_specific_path(self, fake_fs):
        fake_fs.create_file("custom_config.yml", contents="minimax_cookies: custom_cookie\ntimezone: Asia/Tokyo\n")
        config = load_config("/custom_config.yml")
        assert config["minimax_cookies"] == "custom_cookie"
        assert config["timezone"] == "Asia/Tokyo"

    def test_load_config_specific_path_has_highest_priority(self, fake_fs):
        fake_fs.create_file("config.yml", contents="minimax_cookies: default_cookie\n")
        fake_fs.create_file("custom_config.yml", contents="minimax_cookies: custom_cookie\n")
        config = load_config("/custom_config.yml")
        assert config["minimax_cookies"] == "custom_cookie"


# Note: TestTimezoneWithFakeFs tests are in test_fetch_usage.py because they need
# access to the real system's zoneinfo data for timezone resolution.
# pyfakefs does not mock zoneinfo, so tests that call zoneinfo.ZoneInfo() directly
# cannot use the fake filesystem.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
