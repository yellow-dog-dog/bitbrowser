"""BitBrowser SDK exceptions."""

from __future__ import annotations


class BitBrowserError(Exception):
    """Base exception for all BitBrowser SDK errors."""


class ApiError(BitBrowserError):
    """Raised when the API returns success=false.

    Attributes:
        msg: The error message returned by the API.
    """

    def __init__(self, msg: str) -> None:
        self.msg = msg
        super().__init__(msg)


class TransportError(BitBrowserError):
    """Raised on HTTP-level or network errors."""
