"""Credential providers for auth-dependent tools.

This module defines protocols and implementations for providing credentials
to tools that require authentication (e.g., Google OAuth tools).

Usage:
    from tool_master.providers import SimpleGoogleCredentials
    from tool_master.tools.google import create_calendar_tools

    # Option 1: Use environment variables
    creds = SimpleGoogleCredentials()

    # Option 2: Direct configuration
    creds = SimpleGoogleCredentials(
        client_id="your-client-id",
        client_secret="your-client-secret",
        refresh_token="your-refresh-token",
    )

    # Create tools wired to the credentials
    calendar_tools = create_calendar_tools(creds)
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class GoogleCredentialsProvider(Protocol):
    """Protocol for providing Google OAuth credentials.

    Implementations must provide:
    - get_access_token(): Returns a valid access token, refreshing if needed
    - client_id, client_secret, refresh_token properties

    The OAuth flow itself is out of scope - implementations receive a
    refresh_token from a separate OAuth setup and handle token refresh.
    """

    async def get_access_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        ...

    @property
    def client_id(self) -> str:
        """The OAuth client ID."""
        ...

    @property
    def client_secret(self) -> str:
        """The OAuth client secret."""
        ...

    @property
    def refresh_token(self) -> str:
        """The OAuth refresh token."""
        ...


# Import implementations for convenience
from tool_master.providers.google import SimpleGoogleCredentials

__all__ = [
    "GoogleCredentialsProvider",
    "SimpleGoogleCredentials",
]
