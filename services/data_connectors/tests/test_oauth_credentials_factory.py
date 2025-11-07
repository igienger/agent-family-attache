import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from gmail.oauth_credentials_factory import Credentials, OAuthCredentialsFactory

TEST_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@pytest.fixture
def mock_creds_from_file():
    """Fixture to patch 'Credentials.from_authorized_user_file'."""
    with patch(
        "gmail.oauth_credentials_factory.Credentials.from_authorized_user_file"
    ) as mock:
        yield mock


@pytest.fixture
def mock_installed_app_flow():
    """Fixture to patch 'InstalledAppFlow'."""
    with patch("gmail.oauth_credentials_factory.InstalledAppFlow") as mock:
        yield mock


# --- Tests ---


def test_get_creds_with_existing_valid_token(
    tmp_path,
    mock_creds_from_file,
    mock_installed_app_flow,
):
    """
    Scenario 1: Tests get_credentials when a valid token.json exists.
    """
    fake_valid_creds = Credentials(token="fake-valid-token")
    token_path = tmp_path / "token.json"
    creds_path = tmp_path / "credentials.json"
    token_path.write_text("pre-existing token data")
    mock_creds_from_file.return_value = fake_valid_creds

    fake_valid_creds.refresh = MagicMock()  # Should not be called

    creds = OAuthCredentialsFactory(
        credentials_path=str(creds_path), token_path=str(token_path), scopes=TEST_SCOPES
    ).get_credentials()

    assert creds == fake_valid_creds

    token = get_token_file_as_dict(token_path)
    assert token["token"] == "fake-valid-token"

    creds.refresh.assert_not_called()
    mock_installed_app_flow.from_client_secrets_file.assert_not_called()


def test_get_creds_with_expired_refreshable_token(
    tmp_path,
    mock_creds_from_file,
    mock_installed_app_flow,
):
    """
    Scenario 2: Tests get_credentials with an expired but refreshable token.
    """
    expired_refreshable_creds = build_expired_refreshable_creds()
    token_path = tmp_path / "token.json"
    creds_path = tmp_path / "credentials.json"
    token_path.write_text("expired token data")
    mock_creds_from_file.return_value = expired_refreshable_creds

    # --- Act ---
    factory = OAuthCredentialsFactory(
        credentials_path=str(creds_path), token_path=str(token_path), scopes=TEST_SCOPES
    )
    creds = factory.get_credentials()

    assert creds == expired_refreshable_creds

    token = get_token_file_as_dict(token_path)
    assert token["token"] == "refreshed-token"

    creds.refresh.assert_called_once()
    mock_installed_app_flow.from_client_secrets_file.assert_not_called()


def build_expired_refreshable_creds():
    """
    Returns a *real* Credentials object that is expired but refreshable. We mock
    'refresh' to simulate the refresh process.
    """
    creds = Credentials(
        token=None,  # No valid token
        refresh_token="fake-refresh-token",
        token_uri="https://fake.token.uri",
        client_id="fake-client-id",
        client_secret="fake-client-secret",
        # Set expiry to the past
        expiry=datetime.now() - timedelta(days=1),
    )

    assert not creds.valid
    assert creds.expired
    assert creds.refresh_token is not None

    # Mock methods we expect to be called
    creds.refresh = MagicMock()

    def refresh_side_effect(_):
        creds.expiry = datetime.now() + timedelta(days=1)
        creds.token = "refreshed-token"
        return None

    creds.refresh.side_effect = refresh_side_effect
    return creds


def test_get_creds_with_no_token_triggers_oauth_flow(
    tmp_path,
    mock_creds_from_file,
    mock_installed_app_flow,
):
    """
    Scenario 3: Tests get_credentials when no token.json exists.
    """
    fake_valid_creds = Credentials(token="fake-valid-token")
    token_path = tmp_path / "token.json"
    creds_path = tmp_path / "credentials.json"
    assert not token_path.exists()

    # Configure the OAuth flow mock to return our fake valid creds
    mock_flow_instance = MagicMock()
    mock_flow_instance.run_local_server.return_value = fake_valid_creds
    mock_installed_app_flow.from_client_secrets_file.return_value = mock_flow_instance

    creds = OAuthCredentialsFactory(
        credentials_path=str(creds_path), token_path=str(token_path), scopes=TEST_SCOPES
    ).get_credentials()

    assert creds == fake_valid_creds
    token = get_token_file_as_dict(token_path)
    assert token["token"] == "fake-valid-token"

    mock_creds_from_file.assert_not_called()
    mock_installed_app_flow.from_client_secrets_file.assert_called_once_with(
        str(creds_path), TEST_SCOPES
    )
    mock_flow_instance.run_local_server.assert_called_once()


def test_get_creds_with_invalid_token_triggers_oauth_flow(
    tmp_path,
    mock_creds_from_file,
    mock_installed_app_flow,
):
    """
    Scenario 4: Tests fallback to OAuth flow when token is invalid/unrefreshable.
    """
    fake_valid_creds = Credentials(token="fake-valid-token")
    fake_expired_unrefreshable_creds = build_expired_unrefreshable_creds()
    token_path = tmp_path / "token.json"
    creds_path = tmp_path / "credentials.json"
    token_path.write_text("expired, unrefreshable token data")

    mock_creds_from_file.return_value = fake_expired_unrefreshable_creds

    mock_flow_instance = MagicMock()
    mock_flow_instance.run_local_server.return_value = fake_valid_creds
    mock_installed_app_flow.from_client_secrets_file.return_value = mock_flow_instance

    creds = OAuthCredentialsFactory(
        credentials_path=str(creds_path), token_path=str(token_path), scopes=TEST_SCOPES
    ).get_credentials()

    assert creds == fake_valid_creds
    token = get_token_file_as_dict(token_path)
    assert token["token"] == "fake-valid-token"

    mock_installed_app_flow.from_client_secrets_file.assert_called_once_with(
        str(creds_path), TEST_SCOPES
    )
    mock_flow_instance.run_local_server.assert_called_once()


def build_expired_unrefreshable_creds():
    """
    Returns a *real* Credentials object that is expired and *not* refreshable.
    """
    creds = Credentials(
        token=None,
        refresh_token=None,  # The key: no refresh token
        expiry=datetime.now() - timedelta(days=1),
    )

    # Assertions in the code will check these properties
    assert not creds.valid
    assert creds.expired
    assert creds.refresh_token is None

    return creds


# --- Helpers ---


from pathlib import Path


def get_token_file_as_dict(token_path: str | Path) -> dict:
    """Helper to read the token file as a dict."""
    with open(str(token_path)) as f:
        return json.load(f)
