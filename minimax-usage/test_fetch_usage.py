#!/usr/bin/env python3
import os
import sys
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone, timedelta
from urllib.error import URLError, HTTPError

sys.path.insert(0, os.path.dirname(__file__))

from fetch_usage import load_cookies, fetch_usage, format_time_remaining, time_bar, ascii_bar, main, get_timezone, load_config

class TestLoadCookies:
    def test_load_cookies_from_env(self):
        os.environ["MINIMAX_COOKIES"] = "test_cookie_from_env"
        cookies = load_cookies()
        assert cookies == "test_cookie_from_env"
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
            
            del os.environ["MINIMAX_COOKIES"]
        finally:
            os.chdir(original_cwd)

    def test_load_cookies_no_config(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            
            if "MINIMAX_COOKIES" in os.environ:
                del os.environ["MINIMAX_COOKIES"]
            
            with pytest.raises(SystemExit) as exc_info:
                load_cookies()
            assert exc_info.value.code == 1
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
            
            del os.environ["MINIMAX_COOKIES"]
        finally:
            os.chdir(original_cwd)
            if os.path.exists(home_file):
                os.unlink(home_file)

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
        
        with pytest.raises(SystemExit) as exc_info:
            fetch_usage()
        assert exc_info.value.code == 1

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_invalid_json(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with pytest.raises(SystemExit) as exc_info:
            fetch_usage()
        assert exc_info.value.code == 1

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_network_error(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_urlopen.side_effect = URLError("Connection refused")
        
        with pytest.raises(SystemExit) as exc_info:
            fetch_usage()
        assert exc_info.value.code == 1

    @patch('fetch_usage.urllib.request.urlopen')
    @patch('fetch_usage.load_cookies')
    def test_fetch_usage_http_error(self, mock_load_cookies, mock_urlopen):
        mock_load_cookies.return_value = "test_cookies"
        mock_urlopen.side_effect = HTTPError(url="", code=401, msg="Unauthorized", hdrs={}, fp=None)
        
        with pytest.raises(SystemExit) as exc_info:
            fetch_usage()
        assert exc_info.value.code == 1


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


class TestMain:
    @patch('fetch_usage.fetch_usage')
    @patch('fetch_usage.load_cookies')
    def test_main_expired_cookies(self, mock_load_cookies, mock_fetch):
        mock_load_cookies.return_value = "test"
        mock_fetch.return_value = {
            "base_resp": {"status_code": 1004}
        }
        
        main()
        
        mock_fetch.assert_called_once()

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
        
        mock_fetch.assert_called_once()

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


class TestTimezone:
    def test_get_timezone_default(self):
        tz = get_timezone()
        assert str(tz) == "Asia/Shanghai" or tz == timezone(timedelta(hours=8))

    def test_get_timezone_from_env(self):
        with patch.dict(os.environ, {"MINIMAX_TIMEZONE": "America/New_York"}):
            import importlib
            import fetch_usage
            importlib.reload(fetch_usage)
            tz = fetch_usage.get_timezone()
            assert str(tz) == "America/New_York"
            importlib.reload(fetch_usage)

    def test_get_timezone_invalid_fallback(self):
        with patch.dict(os.environ, {"MINIMAX_TIMEZONE": "Invalid/Timezone"}):
            import importlib
            import fetch_usage
            importlib.reload(fetch_usage)
            tz = fetch_usage.get_timezone()
            assert tz == timezone(timedelta(hours=8))
            importlib.reload(fetch_usage)

    def test_get_timezone_explicit(self):
        import importlib
        import fetch_usage
        importlib.reload(fetch_usage)
        tz = fetch_usage.get_timezone("America/Los_Angeles")
        assert str(tz) == "America/Los_Angeles"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
