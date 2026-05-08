"""Tests for bitbrowser.exceptions."""

from __future__ import annotations

import pytest

from bitbrowser.exceptions import ApiError, BitBrowserError, TransportError


class TestBitBrowserError:
    def test_is_exception(self):
        err = BitBrowserError("base error")
        assert isinstance(err, Exception)
        assert str(err) == "base error"

    def test_subclass_hierarchy(self):
        assert issubclass(ApiError, BitBrowserError)
        assert issubclass(TransportError, BitBrowserError)


class TestApiError:
    def test_stores_msg(self):
        err = ApiError("quota exceeded")
        assert err.msg == "quota exceeded"

    def test_str_equals_msg(self):
        err = ApiError("not found")
        assert str(err) == "not found"

    def test_is_bit_browser_error(self):
        assert isinstance(ApiError("x"), BitBrowserError)

    def test_is_exception(self):
        assert isinstance(ApiError("x"), Exception)

    def test_raise_and_catch_as_base(self):
        with pytest.raises(BitBrowserError):
            raise ApiError("oops")

    def test_empty_msg(self):
        err = ApiError("")
        assert err.msg == ""
        assert str(err) == ""


class TestTransportError:
    def test_is_bit_browser_error(self):
        assert isinstance(TransportError("connection refused"), BitBrowserError)

    def test_str(self):
        err = TransportError("timeout")
        assert str(err) == "timeout"

    def test_raise_and_catch_as_base(self):
        with pytest.raises(BitBrowserError):
            raise TransportError("network error")

    def test_raise_and_catch_specifically(self):
        with pytest.raises(TransportError):
            raise TransportError("err")
