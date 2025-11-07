import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class OAuthCredentialsFactory:
    """A factory to create and manage OAuth 2.0 credentials for Google API access."""

    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
        scopes: list[str] | None = None,
    ):
        """
        Initializes the CredentialsFactory with OAuth 2.0 credentials.

        Args:
            credentials_path: Path to the OAuth 2.0 client secrets file.
            token_path: Path where the current access token is stored.
            scopes: List of OAuth 2.0 scopes for API access.
        """
        self.scopes = scopes if scopes is not None else []
        self.credentials_path = credentials_path
        self.token_path = token_path

    def get_credentials(self) -> Credentials:
        """
        Retrieves valid OAuth 2.0 credentials, refreshing or obtaining new ones if
        necessary.

        Returns:
            The authenticated credentials object.
        """
        creds = self._authenticate(self.credentials_path, self.token_path, self.scopes)
        # Save the credentials for the next run
        self._write_creds_to_token_file(creds, self.token_path)
        return creds

    def _authenticate(
        self, credentials_path: str, token_path: str, scopes: list[str]
    ) -> Credentials:
        """
        Handles the OAuth 2.0 authentication flow.

        Args:
            credentials_path: Path to the credentials file.
            token_path: Path to the token file.
            scopes: List of OAuth 2.0 scopes to request.

        Returns:
            The authenticated credentials object.
        """
        if not os.path.exists(token_path):
            # First time requires OAuth login.
            creds = self._oauth_flow(credentials_path, scopes)
        else:
            creds = Credentials.from_authorized_user_file(token_path, scopes)

        if creds and creds.valid:
            return creds

        if creds and creds.expired and creds.refresh_token:
            return self._refresh_credentials(creds)

        # As a fallback, use OAuth flow if credentials are non-existent or invalid or
        # unable to refresh.
        return self._oauth_flow(credentials_path, scopes)

    def _refresh_credentials(self, creds: Credentials) -> Credentials:
        creds.refresh(Request())
        return creds

    def _oauth_flow(self, credentials_path: str, scopes: list[str]) -> Credentials:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
        creds = flow.run_local_server(port=0)
        assert isinstance(creds, Credentials)
        return creds

    def _write_creds_to_token_file(self, creds: Credentials, token_path: str) -> None:
        with open(token_path, "w") as token:
            token.write(creds.to_json())
