"""Tests for ghcr_badge.main module."""

from __future__ import annotations

from argparse import ArgumentTypeError, Namespace
from http.client import CannotSendRequest
from unittest.mock import MagicMock, Mock, patch

import pytest

from ghcr_badge.main import (
    HttpConnectionNotFountError,
    check_connectivity,
    main,
    parse_args,
)


class TestCheckConnectivity:
    """Test check_connectivity function."""

    @patch("ghcr_badge.main.HTTPConnection")
    def test_connectivity_success(self, mock_http_connection: MagicMock) -> None:
        """Test check_connectivity with successful connection."""
        mock_conn = Mock()
        mock_http_connection.return_value = mock_conn
        mock_conn.request.return_value = None
        mock_conn.close.return_value = None

        result = check_connectivity()
        assert result is True
        mock_conn.request.assert_called_once_with("HEAD", "/")
        mock_conn.close.assert_called_once()

    @patch("ghcr_badge.main.HTTPConnection")
    def test_connectivity_failure(self, mock_http_connection: MagicMock) -> None:
        """Test check_connectivity with failed connection."""
        mock_conn = Mock()
        mock_http_connection.return_value = mock_conn
        mock_conn.request.side_effect = CannotSendRequest

        with pytest.raises(ArgumentTypeError, match="No connection"):
            check_connectivity()

    @patch("ghcr_badge.main.HTTPConnection")
    def test_connectivity_custom_url(self, mock_http_connection: MagicMock) -> None:
        """Test check_connectivity with custom URL."""
        mock_conn = Mock()
        mock_http_connection.return_value = mock_conn
        mock_conn.request.return_value = None
        mock_conn.close.return_value = None

        result = check_connectivity("example.com", timeout=5)
        assert result is True
        mock_http_connection.assert_called_once_with("example.com", timeout=5)


class TestParseArgs:
    """Test parse_args function."""

    def test_parse_args_minimal(self) -> None:
        """Test parse_args with minimal required arguments."""
        args = parse_args(["-u", "testuser", "-n", "testrepo"])
        assert args.user == "testuser"
        assert args.name == "testrepo"
        assert args.color == "lime"
        assert args.out is None

    def test_parse_args_all_options(self) -> None:
        """Test parse_args with all options."""
        args = parse_args(["-u", "testuser", "-n", "testrepo", "-c", "red", "-o", "output.svg"])
        assert args.user == "testuser"
        assert args.name == "testrepo"
        assert args.color == "red"
        assert args.out == "output.svg"

    def test_parse_args_missing_user(self) -> None:
        """Test parse_args with missing user."""
        with pytest.raises(SystemExit):
            parse_args(["-n", "testrepo"])

    def test_parse_args_missing_name(self) -> None:
        """Test parse_args with missing name."""
        with pytest.raises(SystemExit):
            parse_args(["-u", "testuser"])

    def test_parse_args_long_options(self) -> None:
        """Test parse_args with long option names."""
        args = parse_args(["--user", "testuser", "--name", "testrepo", "--color", "blue", "--out", "badge.svg"])
        assert args.user == "testuser"
        assert args.name == "testrepo"
        assert args.color == "blue"
        assert args.out == "badge.svg"

    def test_parse_args_version(self) -> None:
        """Test parse_args with version flag."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["-V"])
        assert exc_info.value.code == 0


class TestMain:
    """Test main function."""

    @patch("ghcr_badge.main.check_connectivity")
    @patch("ghcr_badge.main.parse_args")
    @patch("ghcr_badge.main.GHCRBadgeGenerator")
    @patch("builtins.print")
    def test_main_success_no_output_file(
        self,
        mock_print: MagicMock,
        mock_generator_class: MagicMock,
        mock_parse_args: MagicMock,
        mock_check_connectivity: MagicMock,
    ) -> None:
        """Test main with successful execution and no output file."""
        mock_check_connectivity.return_value = True
        mock_args = Namespace(user="testuser", name="testrepo", color="lime", out=None)
        mock_parse_args.return_value = mock_args
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg>badge</svg>"
        mock_generator_class.return_value = mock_generator

        main()

        mock_check_connectivity.assert_called_once()
        mock_generator_class.assert_called_once_with(color="lime")
        mock_generator.generate_tags.assert_called_once_with("testuser", "testrepo")
        # When out is None, prints to stdout
        assert mock_print.call_count >= 1

    @patch("ghcr_badge.main.check_connectivity")
    @patch("ghcr_badge.main.parse_args")
    @patch("ghcr_badge.main.GHCRBadgeGenerator")
    @patch("builtins.print")
    @patch("pathlib.Path.open")
    def test_main_success_with_output_file(
        self,
        mock_open: MagicMock,
        mock_print: MagicMock,
        mock_generator_class: MagicMock,
        mock_parse_args: MagicMock,
        mock_check_connectivity: MagicMock,
    ) -> None:
        """Test main with successful execution and output file."""
        mock_check_connectivity.return_value = True
        mock_args = Namespace(user="testuser", name="testrepo", color="red", out="output.svg")
        mock_parse_args.return_value = mock_args
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg>badge</svg>"
        mock_generator_class.return_value = mock_generator
        mock_file = Mock()
        mock_open.return_value = mock_file

        main()

        mock_check_connectivity.assert_called_once()
        mock_generator_class.assert_called_once_with(color="red")
        mock_generator.generate_tags.assert_called_once_with("testuser", "testrepo")
        mock_open.assert_called_once_with("w")
        mock_print.assert_called_once_with("<svg>badge</svg>", file=mock_file)

    @patch("ghcr_badge.main.check_connectivity")
    @patch("ghcr_badge.main.parse_args")
    def test_main_no_connectivity(self, mock_parse_args: MagicMock, mock_check_connectivity: MagicMock) -> None:
        """Test main with no connectivity."""
        mock_check_connectivity.return_value = False
        mock_args = Namespace(user="testuser", name="testrepo", color="lime", out=None)
        mock_parse_args.return_value = mock_args

        with pytest.raises(HttpConnectionNotFountError):
            main()
