"""Google OAuth credentials provider implementation."""

import os
from datetime import datetime, timedelta
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


class SimpleGoogleCredentials:
    """Simple credentials provider using env vars or direct config.

    This implementation handles token refresh using Google's OAuth2 endpoint.
    The initial OAuth flow (obtaining the refresh_token) is out of scope -
    projects must provide their own refresh_token.

    Environment variables (used if parameters not provided):
        GOOGLE_CLIENT_ID: OAuth client ID
        GOOGLE_CLIENT_SECRET: OAuth client secret
        GOOGLE_REFRESH_TOKEN: OAuth refresh token

    Usage:
        # Option 1: Environment variables
        creds = SimpleGoogleCredentials()

        # Option 2: Direct config
        creds = SimpleGoogleCredentials(
            client_id="...",
            client_secret="...",
            refresh_token="...",
        )

        # Get access token (auto-refreshes if needed)
        token = await creds.get_access_token()
    """

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_refresh_buffer: int = 300,  # Refresh 5 minutes before expiry
    ):
        """Initialize credentials provider.

        Args:
            client_id: OAuth client ID (or set GOOGLE_CLIENT_ID env var)
            client_secret: OAuth client secret (or set GOOGLE_CLIENT_SECRET env var)
            refresh_token: OAuth refresh token (or set GOOGLE_REFRESH_TOKEN env var)
            token_refresh_buffer: Seconds before expiry to trigger refresh
        """
        self._client_id = client_id or os.getenv("GOOGLE_CLIENT_ID")
        self._client_secret = client_secret or os.getenv("GOOGLE_CLIENT_SECRET")
        self._refresh_token = refresh_token or os.getenv("GOOGLE_REFRESH_TOKEN")
        self._token_refresh_buffer = token_refresh_buffer

        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    @property
    def client_id(self) -> str:
        """The OAuth client ID."""
        if not self._client_id:
            raise ValueError(
                "client_id not set. Provide it directly or set GOOGLE_CLIENT_ID env var."
            )
        return self._client_id

    @property
    def client_secret(self) -> str:
        """The OAuth client secret."""
        if not self._client_secret:
            raise ValueError(
                "client_secret not set. Provide it directly or set GOOGLE_CLIENT_SECRET env var."
            )
        return self._client_secret

    @property
    def refresh_token(self) -> str:
        """The OAuth refresh token."""
        if not self._refresh_token:
            raise ValueError(
                "refresh_token not set. Provide it directly or set GOOGLE_REFRESH_TOKEN env var."
            )
        return self._refresh_token

    def _needs_refresh(self) -> bool:
        """Check if the access token needs to be refreshed."""
        if self._access_token is None or self._token_expiry is None:
            return True

        # Refresh if within buffer period of expiry
        buffer = timedelta(seconds=self._token_refresh_buffer)
        return datetime.now() >= (self._token_expiry - buffer)

    async def _refresh(self) -> None:
        """Refresh the access token using the refresh token."""
        if httpx is None:
            raise ImportError(
                "httpx is required for token refresh. "
                "Install with: pip install tool-master[google]"
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Token refresh failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            self._access_token = data["access_token"]

            # Calculate expiry time
            expires_in = data.get("expires_in", 3600)  # Default 1 hour
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)

    async def get_access_token(self) -> str:
        """Get a valid access token, refreshing if needed.

        Returns:
            A valid access token string.

        Raises:
            ValueError: If credentials are not configured.
            RuntimeError: If token refresh fails.
            ImportError: If httpx is not installed.
        """
        if self._needs_refresh():
            await self._refresh()

        assert self._access_token is not None
        return self._access_token

    def is_configured(self) -> bool:
        """Check if all required credentials are configured.

        Returns:
            True if client_id, client_secret, and refresh_token are all set.
        """
        return all([
            self._client_id,
            self._client_secret,
            self._refresh_token,
        ])
