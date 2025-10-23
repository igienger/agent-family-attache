from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from common.infisical_client import ApiSettings, ClientSettings, InfisicalClient
from pydantic import SecretStr, ValidationError

# We patch 'infisical_sdk.InfisicalSDKClient'
# This is the path to the class *as it is imported* in your module.
SDK_CLIENT_PATH = "common.infisical_client.client.InfisicalSDKClient"

VALID_API_SETTINGS = ApiSettings(
    INFISICAL_HOST="http://mock-host.com",
    INFISICAL_CLIENT_ID="id",
    INFISICAL_CLIENT_SECRET=SecretStr("secret"),
)


# --- Tests for ClientSettings ---


def test_client_settings_validator_fails_with_both_id_and_slug():
    """
    Tests that ClientSettings raises a ValidationError if both
    project_id and project_slug are provided.
    """
    with pytest.raises(ValidationError, match="Ambiguous project identification"):
        ClientSettings(
            # Using a string that can be parsed as a UUID5
            project_id="154101e0-b6f7-5767-8526-b81d76b3f7a5",
            project_slug="my-project",
        )


def test_client_settings_validator_passes_with_id_only():
    """Tests that ClientSettings validates successfully with only project_id."""
    project_id_str = "154101e0-b6f7-5767-8526-b81d76b3f7a5"
    settings = ClientSettings(project_id=project_id_str)

    # Pydantic v2 parses UUIDs into UUID objects
    assert isinstance(settings.project_id, str)
    assert str(settings.project_id) == project_id_str
    assert settings.project_slug is None


def test_client_settings_validator_passes_with_slug_only():
    """Tests that ClientSettings validates successfully with only project_slug."""
    settings = ClientSettings(project_slug="my-project")
    assert settings.project_slug == "my-project"
    assert settings.project_id is None


# --- Tests for InfisicalClient ---


@patch(SDK_CLIENT_PATH)
def test_infisical_client_init_with_universal_auth(MockInfisicalSdkClient):
    """
    Tests that the client initializes correctly using Token authentication.
    """
    ### Arrange ###
    mock_client = MagicMock()
    MockInfisicalSdkClient.return_value = mock_client

    api_settings = ApiSettings(
        INFISICAL_HOST="http://mock-host.com",
        INFISICAL_CLIENT_ID="id",
        INFISICAL_CLIENT_SECRET=SecretStr("secret"),
    )

    ### Act ###
    client = InfisicalClient(settings=ClientSettings(), api_settings=api_settings)

    ### Assert ###

    # Check the real SDK constructor was used & login called correctly
    MockInfisicalSdkClient.assert_called_once_with(host="http://mock-host.com/")
    mock_client.auth.universal_auth.login.assert_called_once_with("id", "secret")

    # Check that the internal properties are set
    assert client.raw_client == mock_client


@patch(SDK_CLIENT_PATH)
def test_getattr_delegates_whitelisted_method_calls(MockInfisicalSdkClient: MagicMock):
    """
    Tests that __getattr__ correctly delegates method calls
    to the underlying _client instance.
    """

    ### Arrange ###
    # Setup client.secrets.get_secret_by_name mock
    def get_secret_by_name(name: str, project_id: str, secret_path: str):
        pass

    mock_get_secret = mock.create_autospec(get_secret_by_name)
    mock_secrets = MagicMock()
    mock_client = MagicMock()

    MockInfisicalSdkClient.return_value = mock_client
    mock_client.secrets = mock_secrets
    mock_secrets.get_secret_by_name = mock_get_secret

    mock_get_secret.return_value = "secret-payload"

    client = InfisicalClient(
        api_settings=VALID_API_SETTINGS,
        settings=ClientSettings(
            project_id="123",
            # NOTE: env_slug is an extra arg that won't get used
            environment_slug="prod",
            secret_path="/",
        ),
    )

    ### Act ###
    # Call a method that *should* be delegated
    result = client.secrets.get_secret_by_name(name="DB_PASS")

    ### Assert ###
    # Check that the method was called with correct args
    mock_secrets.get_secret_by_name.assert_called_once_with(
        name="DB_PASS", project_id="123", secret_path="/"
    )
    assert result == "secret-payload"


@patch(SDK_CLIENT_PATH)
def test_getattr_ignores_other_calls(MockInfisicalSdkClient: MagicMock):
    """
    Tests that __getattr__ does not delegate non-whitelisted calls.
    """

    # Setup client.other.get_secret_by_name mock
    def get_secret_by_name():
        pass

    mock_get_secret = mock.create_autospec(get_secret_by_name)
    mock_other = MagicMock()
    mock_client = MagicMock()

    MockInfisicalSdkClient.return_value = mock_client
    mock_client.other = mock_other
    mock_other.get_secret_by_name = mock_get_secret

    mock_get_secret.return_value = "secret-payload"

    client = InfisicalClient(
        api_settings=VALID_API_SETTINGS,
        settings=ClientSettings(
            project_id="123", environment_slug="prod", secret_path="/"
        ),
    )

    ### Act ###
    # Call a method that *should not* be delegated
    with pytest.raises(AttributeError):
        client.other.get_secret_by_name(name="DB_PASS")

    ### Assert ###
    mock_other.get_secret_by_name.assert_not_called()
