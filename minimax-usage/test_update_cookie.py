#!/usr/bin/env python3
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from update_cookie import extract_cookie_from_curl_file, update_cookie_in_config


class TestExtractCookie:
    def test_single_quotes(self, tmp_path):
        curl_file = tmp_path / "curl.txt"
        curl_file.write_text("curl -b 'session=abc123' https://example.com")
        result = extract_cookie_from_curl_file(str(curl_file))
        assert result == "session=abc123"

    def test_double_quotes(self, tmp_path):
        curl_file = tmp_path / "curl.txt"
        curl_file.write_text('curl -b "session=xyz789" https://example.com')
        result = extract_cookie_from_curl_file(str(curl_file))
        assert result == "session=xyz789"

    def test_cookie_with_special_chars(self, tmp_path):
        curl_file = tmp_path / "curl.txt"
        curl_file.write_text("-b 'token=abc123; refresh=def456'")
        result = extract_cookie_from_curl_file(str(curl_file))
        assert result == "token=abc123; refresh=def456"

    def test_cookie_not_found(self, tmp_path):
        curl_file = tmp_path / "curl.txt"
        curl_file.write_text("curl https://example.com")
        with pytest.raises(ValueError, match="No cookie found"):
            extract_cookie_from_curl_file(str(curl_file))

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            extract_cookie_from_curl_file("/nonexistent/file.txt")

    def test_empty_file(self, tmp_path):
        curl_file = tmp_path / "empty.txt"
        curl_file.write_text("")
        with pytest.raises(ValueError, match="No cookie found"):
            extract_cookie_from_curl_file(str(curl_file))

    def test_multiline_curl_command(self, tmp_path):
        curl_file = tmp_path / "curl.txt"
        curl_file.write_text("curl \\\n  -b 'cookie123' \\\n  https://example.com")
        result = extract_cookie_from_curl_file(str(curl_file))
        assert result == "cookie123"

    def test_cookie_with_equals_sign(self, tmp_path):
        curl_file = tmp_path / "curl.txt"
        curl_file.write_text("-b 'session_id=abc123; user=john'")
        result = extract_cookie_from_curl_file(str(curl_file))
        assert result == "session_id=abc123; user=john"


class TestUpdateCookieInConfig:
    def test_update_existing_cookie(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("minimax_cookies: old_cookie\n")

        update_cookie_in_config(str(config_file), "new_cookie")

        content = config_file.read_text()
        assert "new_cookie" in content
        assert "old_cookie" not in content

    def test_preserves_other_values(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("minimax_cookies: old\ntimezone: Asia/Shanghai\n")

        update_cookie_in_config(str(config_file), "new")

        content = config_file.read_text()
        assert "minimax_cookies: \"new\"" in content
        assert "timezone: Asia/Shanghai" in content

    def test_adds_cookie_if_missing(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("timezone: UTC\n")

        update_cookie_in_config(str(config_file), "my_cookie")

        content = config_file.read_text()
        assert "minimax_cookies: \"my_cookie\"" in content
        assert "timezone: UTC" in content

    def test_creates_new_config(self, tmp_path):
        config_file = tmp_path / "new_config.yml"

        update_cookie_in_config(str(config_file), "my_cookie")

        content = config_file.read_text()
        assert "minimax_cookies: \"my_cookie\"" in content

    def test_cookie_with_double_quotes_escaped(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("minimax_cookies: old\n")

        update_cookie_in_config(str(config_file), 'cookie"with"quotes')

        content = config_file.read_text()
        assert 'cookie\\"with\\"quotes' in content

    def test_cookie_with_backslash_escaped(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("minimax_cookies: old\n")

        update_cookie_in_config(str(config_file), "cookie\\with\\slashes")

        content = config_file.read_text()
        assert "cookie\\\\with\\\\slashes" in content

    def test_empty_cookie_value(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("minimax_cookies: old\n")

        update_cookie_in_config(str(config_file), "")

        content = config_file.read_text()
        assert 'minimax_cookies: ""' in content

    def test_preserves_multiple_other_values(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("minimax_cookies: old\ntimezone: Asia/Shanghai\nother: value\n")

        update_cookie_in_config(str(config_file), "new")

        content = config_file.read_text()
        assert "minimax_cookies: \"new\"" in content
        assert "timezone: Asia/Shanghai" in content
        assert "other: value" in content

    def test_whitespace_handling(self, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("  minimax_cookies: old  \n")

        update_cookie_in_config(str(config_file), "new")

        content = config_file.read_text()
        assert "minimax_cookies: \"new\"" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
