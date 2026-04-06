#!/usr/bin/env python3
import os
import sys
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from urllib.error import URLError, HTTPError

sys.path.insert(0, os.path.dirname(__file__))

from fetch_usage import (
    load_cookies, fetch_usage, format_time_remaining, time_bar, ascii_bar,
    main, get_timezone, load_config, get_local_timezone,
    CookiesNotFoundError, NetworkError, HTTPError as FetchHTTPError, InvalidResponseError
)

class TestLoadCookies:
    def test_load_cookies_from_env(self):
        try:
            os.environ["MINIMAX_COOKIES"] = "test_cookie_from_env"
            cookies = load_cookies()
            assert cookies == "test_cookie_from_env"
        finally:
            del os.environ["MINIMAX_COOKIES"]

    def test_load_cookies_from_config_yml(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            with open("config.yml", "w") as f:
                f.write("minimax_cookies: test_cookie_from_yaml\n")
            
            os.environ["MINIMAX_COOKIES"] = ""
            cookies = load_cookies()
            assert cookies == "test_cookie_from_yaml"
        finally:
            if "MINIMAX_COOKIES" in os.environ:
                del os.environ["MINIMAX_COOKIES"]
            os.chdir(original_cwd)

    def test_load_cookies_no_config(self):
        with patch('fetch_usage.load_config', return_value={}):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(CookiesNotFoundError) as exc_info:
                    load_cookies()
                assert "No cookies found" in str(exc_info.value)

    def test_load_cookies_config_file_not_found(self):
        with patch('fetch_usage.load_config', return_value={}):
            with pytest.raises(CookiesNotFoundError) as exc_info:
                load_cookies("/nonexistent/config.yml")
            assert "Config file not found" in str(exc_info.value)

    def test_load_cookies_config_missing_field(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            config_path = os.path.join(os.getcwd(), "my_config.yml")
            with open(config_path, "w") as f:
                f.write("timezone: UTC\n")
            
            with pytest.raises(CookiesNotFoundError) as exc_info:
                load_cookies(config_path)
            assert "does not contain 'minimax_cookies' field" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)

    def test_load_cookies_empty_value(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            with open("config.yml", "w") as f:
                f.write("minimax_cookies: \"\"\n")
            
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(CookiesNotFoundError) as exc_info:
                    load_cookies()
            assert "No cookies found" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)

    def test_load_cookies_from_home_config(self):
        original_cwd = os.getcwd()
        home_file = os.path.expanduser("~/.minimax_config.yml")
        try:
            os.chdir(tempfile.mkdtemp())
            with open(home_file, "w") as f:
                f.write("minimax_cookies: test_cookie_home\n")
            
            os.environ["MINIMAX_COOKIES"] = ""
            cookies = load_cookies()
            assert cookies == "test_cookie_home"
        finally:
            if "MINIMAX_COOKIES" in os.environ:
                del os.environ["MINIMAX_COOKIES"]
            os.chdir(original_cwd)
            if os.path.exists(home_file):
                os.unlink(home_file)

    def test_load_cookies_from_specific_config_path(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            custom_config = os.path.join(os.getcwd(), "my_config.yml")
            with open(custom_config, "w") as f:
                f.write("minimax_cookies: cookie_from_specific_path\n")
            
            os.environ["MINIMAX_COOKIES"] = ""
            cookies = load_cookies(custom_config)
            assert cookies == "cookie_from_specific_path"
        finally:
            if "MINIMAX_COOKIES" in os.environ:
                del os.environ["MINIMAX_COOKIES"]
            os.chdir(original_cwd)

    def test_c_config_overrides_env_var(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            custom_config = os.path.join(os.getcwd(), "my_config.yml")
            with open(custom_config, "w") as f:
                f.write("minimax_cookies: cookie_from_config\n")
            
            os.environ["MINIMAX_COOKIES"] = "cookie_from_env"
            cookies = load_cookies(custom_config)
            assert cookies == "cookie_from_config"
        finally:
            if "MINIMAX_COOKIES" in os.environ:
                del os.environ["MINIMAX_COOKIES"]
            os.chdir(original_cwd)

    def test_load_config_success(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            with open("config.yml", "w") as f:
                f.write("minimax_cookies: yaml_cookie\ntimezone: Asia/Shanghai\n")
            
            config = load_config()
            assert config["minimax_cookies"] == "yaml_cookie"
            assert config["timezone"] == "Asia/Shanghai"
        finally:
            os.chdir(original_cwd)

    def test_load_config_empty(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            
            config = load_config()
            assert config == {}
        finally:
            os.chdir(original_cwd)

    def test_load_config_from_specific_path(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            custom_config = os.path.join(os.getcwd(), "custom_config.yml")
            with open(custom_config, "w") as f:
                f.write("minimax_cookies: custom_cookie\ntimezone: Asia/Tokyo\n")
            
            config = load_config(custom_config)
            assert config["minimax_cookies"] == "custom_cookie"
            assert config["timezone"] == "Asia/Tokyo"
        finally:
            os.chdir(original_cwd)

    def test_load_config_specific_path_not_found(self):
        config = load_config("/nonexistent/path/config.yml")
        assert config == {}

    def test_load_config_specific_path_has_highest_priority(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            with open("config.yml", "w") as f:
                f.write("minimax_cookies: default_cookie\n")
            
            custom_config = os.path.join(os.getcwd(), "custom_config.yml")
            with open(custom_config, "w") as f:
                f.write("minimax_cookies: custom_cookie\n")
            
            config = load_config(custom_config)
            assert config["minimax_cookies"] == "custom_cookie"
        finally:
            os.chdir(original_cwd)


class TestFetchUsage:
    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_success(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"data": "test"}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = fetch_usage()
        
        assert result == {"data": "test"}
        mock_load_cookies.assert_called_once()

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_with_real_api_response(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "base_resp": {"status_code": 0},
            "model_remains": [
                {"model_name": "MiniMax-M*", "current_interval_total_count": 100, "current_interval_usage_count": 50}
            ]
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = fetch_usage()
        
        assert result["base_resp"]["status_code"] == 0
        assert len(result["model_remains"]) == 1

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_empty_response(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_response = MagicMock()
        mock_response.read.return_value = b""
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with pytest.raises(InvalidResponseError):
            fetch_usage()

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_invalid_json(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with pytest.raises(InvalidResponseError):
            fetch_usage()

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_network_error(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_urlopen.side_effect = URLError("Connection refused")
        
        with pytest.raises(NetworkError):
            fetch_usage()

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_http_error(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_urlopen.side_effect = HTTPError(url="", code=401, msg="Unauthorized", hdrs={}, fp=None)
        
        with pytest.raises(FetchHTTPError):
            fetch_usage()

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_with_config_path(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"data": "test"}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = fetch_usage("/custom/config/path.yml")
        
        assert result == {"data": "test"}
        mock_load_cookies.assert_called_once_with("/custom/config/path.yml", debug=False)


class TestFormatTimeRemaining:
    def test_hours_remaining(self):
        assert format_time_remaining(2, 30, 0) == "2h 30m"

    def test_minutes_remaining(self):
        assert format_time_remaining(0, 15, 45) == "15m 45s"

    def test_seconds_only(self):
        assert format_time_remaining(0, 0, 30) == "30s"


class TestTimeBar:
    def test_time_bar_full(self):
        result = time_bar(5, 5)
        assert "████" in result
        assert "100%" in result

    def test_time_bar_empty(self):
        result = time_bar(0, 5)
        assert "░░░░" in result
        assert "0%" in result

    def test_time_bar_partial(self):
        result = time_bar(2.5, 5)
        assert "░" in result
        assert "%" in result

    def test_time_bar_zero_total(self):
        result = time_bar(1, 0)
        assert "(N/A)" in result

    def test_time_bar_with_label(self):
        result = time_bar(2.5, 5, label="Time:")
        assert "50%" in result
        assert "Time: " in result
        assert result.endswith("⏱️")

    def test_time_bar_zero_total_with_label(self):
        result = time_bar(1, 0, label="Time:")
        assert "(N/A)" in result
        assert "Time:" in result


class TestAsciiBar:
    def test_ascii_bar_full(self):
        result = ascii_bar(100, 100)
        assert "100%" in result
        assert "(100/100)" in result

    def test_ascii_bar_empty(self):
        result = ascii_bar(0, 100)
        assert "0%" in result
        assert "(0/100)" in result

    def test_ascii_bar_partial(self):
        result = ascii_bar(25, 100)
        assert "░" in result
        assert "(25/100)" in result

    def test_ascii_bar_zero_total(self):
        result = ascii_bar(50, 0)
        assert "(N/A)" in result

    def test_ascii_bar_with_label(self):
        result = ascii_bar(50, 100, label="Quota:")
        assert "50%" in result
        assert "(50/100)" in result
        assert "Usage: " in result

    def test_ascii_bar_zero_total_with_label(self):
        result = ascii_bar(50, 0, label="Quota:")
        assert "(N/A)" in result
        assert "Quota:" in result


class TestMain:
    @patch('fetch_usage.fetch_usage')
    @patch('fetch_usage.load_cookies')
    def test_main_expired_cookies(self, mock_load_cookies, mock_fetch):
        mock_load_cookies.return_value = "test"
        mock_fetch.return_value = {
            "base_resp": {"status_code": 1004}
        }
        
        main()
        
        mock_fetch.assert_called_once_with(None, debug=False)

    @patch('fetch_usage.datetime')
    @patch('fetch_usage.get_current_interval')
    @patch('fetch_usage.get_next_reset_time')
    @patch('fetch_usage.get_time_until_reset')
    @patch('fetch_usage.fetch_usage')
    @patch('fetch_usage.load_cookies')
    def test_main_success(self, mock_load_cookies, mock_fetch, mock_get_time_until_reset, mock_get_next_reset, mock_get_current_interval, mock_datetime):
        mock_load_cookies.return_value = "test"
        
        now = datetime(2026, 3, 29, 18, 30)
        mock_datetime.now.return_value = now
        mock_get_current_interval.return_value = (datetime(2026, 3, 29, 15, 0), datetime(2026, 3, 29, 20, 0))
        mock_get_next_reset.return_value = datetime(2026, 3, 29, 20, 0)
        mock_get_time_until_reset.return_value = (1, 30, 0)
        
        mock_fetch.return_value = {
            "base_resp": {"status_code": 0},
            "model_remains": [
                {
                    "model_name": "MiniMax-M*",
                    "current_interval_total_count": 100,
                    "current_interval_usage_count": 75
                }
            ]
        }
        
        main()
        
        mock_fetch.assert_called_once_with(None, debug=False)

    @patch('fetch_usage.fetch_usage')
    @patch('fetch_usage.load_cookies')
    def test_main_skips_other_models(self, mock_load_cookies, mock_fetch):
        mock_load_cookies.return_value = "test"
        mock_fetch.return_value = {
            "base_resp": {"status_code": 0},
            "model_remains": [
                {
                    "model_name": "Other-Model",
                    "current_interval_total_count": 100,
                    "current_interval_usage_count": 50
                }
            ]
        }
        
        main()
        mock_fetch.assert_called_once_with(None, debug=False)


class TestCommandLineArgs:
    def test_main_accepts_config_arg(self):
        with patch('fetch_usage.fetch_usage') as mock_fetch:
            mock_fetch.return_value = {"base_resp": {"status_code": 1004}}
            custom_path = "/path/to/config.yml"
            main(custom_path)
            mock_fetch.assert_called_once_with(custom_path, debug=False)

    def test_main_accepts_config_arg_none_by_default(self):
        with patch('fetch_usage.fetch_usage') as mock_fetch:
            mock_fetch.return_value = {"base_resp": {"status_code": 1004}}
            main()
            mock_fetch.assert_called_once_with(None, debug=False)


class TestTimezone:
    def setup_method(self):
        get_timezone.cache_clear()

    def teardown_method(self):
        get_timezone.cache_clear()

    def test_get_timezone_from_env(self):
        with patch.dict(os.environ, {"MINIMAX_TIMEZONE": "America/New_York"}):
            tz = get_timezone()
            assert str(tz) == "America/New_York"

    def test_get_timezone_invalid_fallback(self):
        with patch.dict(os.environ, {"MINIMAX_TIMEZONE": "Invalid/Timezone"}):
            tz = get_timezone()
            assert tz == get_local_timezone()

    def test_get_timezone_explicit(self):
        tz = get_timezone("America/Los_Angeles")
        assert str(tz) == "America/Los_Angeles"

    def test_get_timezone_from_config_path(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            config_path = os.path.join(os.getcwd(), "test_config.yml")
            with open(config_path, "w") as f:
                f.write("timezone: America/Los_Angeles\n")
            
            config = load_config(config_path)
            tz_name = config.get("timezone")
            tz = get_timezone(tz_name)
            assert str(tz) == "America/Los_Angeles"
        finally:
            os.chdir(original_cwd)

    def test_get_timezone_env_var_used_when_no_c_config(self):
        with patch.dict(os.environ, {"MINIMAX_TIMEZONE": "Europe/London"}):
            tz = get_timezone()
            assert str(tz) == "Europe/London"

    def test_get_timezone_default_is_local(self):
        tz = get_timezone()
        local_tz = get_local_timezone()
        assert tz == local_tz

    def test_get_timezone_reads_from_c_config_when_env_not_set(self):
        """When config_path provided and MINIMAX_TIMEZONE env var absent, timezone should come from -c config"""
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            config_path = os.path.join(os.getcwd(), "test_config.yml")
            with open(config_path, "w") as f:
                f.write("timezone: Asia/Shanghai\n")
            
            with patch.dict(os.environ, {}, clear=True):
                tz = get_timezone(config_path=config_path)
                assert str(tz) == "Asia/Shanghai"
        finally:
            os.chdir(original_cwd)

    def test_get_timezone_c_config_overrides_env_var(self):
        """When config_path provided, env var should be ignored"""
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            config_path = os.path.join(os.getcwd(), "test_config.yml")
            with open(config_path, "w") as f:
                f.write("timezone: Asia/Shanghai\n")
            
            with patch.dict(os.environ, {"MINIMAX_TIMEZONE": "Europe/London"}):
                tz = get_timezone(config_path=config_path)
                assert str(tz) == "Asia/Shanghai"
        finally:
            os.chdir(original_cwd)

    def test_get_timezone_local_used_when_no_env_no_c_config(self):
        """When no config_path and no env var, local timezone should be used"""
        with patch.dict(os.environ, {}, clear=True):
            tz = get_timezone()
            local_tz = get_local_timezone()
            assert tz == local_tz


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
