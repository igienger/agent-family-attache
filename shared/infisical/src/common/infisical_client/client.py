import functools
import logging

from common.client_utils import NamespaceWrapper
from infisical_sdk import InfisicalSDKClient
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .api_settings import ApiSettings

logger = logging.getLogger(__name__)


class ClientSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    @model_validator(mode="after")
    def validate_auth_method(self) -> "ClientSettings":
        """Ensures exactly one project identification is provided."""
        has_id = self.project_id is not None
        has_slug = self.project_slug is not None
        if has_id and has_slug:
            raise ValueError(
                "Ambiguous project identification: Provide *either* 'project_id' "
                "*or* 'project_slug', not both."
            )
        return self

    project_id: str | None = None
    project_slug: str | None = None
    environment_slug: str = "dev"
    secret_path: str = "/"


class InfisicalClient:
    """
    A pre-configured Infisical Client wrapper.

    This class initializes the official InfisicalSDKClient using settings
    loaded from environment variables via Pydantic.

    It transparently delegates all attribute and method calls
    (e.g., `get_secret`, `create_secret`) to the underlying
    InfisicalSDKClient instance. It fills in project_id / project_slug,
    environment_slug, and secret_path from ClientSettings automatically.
    """

    _client: InfisicalSDKClient
    api_settings: ApiSettings
    settings: ClientSettings

    def __init__(
        self,
        settings: ClientSettings | None = None,
        api_settings: ApiSettings | None = None,
    ):
        """
        Initializes the client.

        If 'api_settings' is not provided, it will be loaded automatically
        from environment variables by instantiating InfisicalSettings.

        Args:
            api_settings: An optional, pre-loaded InfisicalSettings instance.
                      Primarily used for testing.

        Raises:
            RuntimeError: If settings cannot be loaded or are invalid.
        """
        self.api_settings = api_settings if api_settings else ApiSettings()
        self.settings = settings if settings else ClientSettings()

        # Initialize the REAL Infisical client
        self._client = InfisicalSDKClient(host=str(self.api_settings.INFISICAL_HOST))

        self._client.auth.universal_auth.login(
            self.api_settings.INFISICAL_CLIENT_ID,
            self.api_settings.INFISICAL_CLIENT_SECRET.get_secret_value(),
        )

    # Whitelist of attributes to delegate to the underlying client
    _ALLOWED_NAMESPACES = {"secrets"}

    def __getattr__(self, name: str):
        """
        Delegates all unknown attribute/method access to the underlying
        InfisicalClient instance.

        This allows you to call `client.get_secret(...)` and it will
        automatically call `client._client.get_secret(...)`.
        """
        if name not in self._ALLOWED_NAMESPACES or not hasattr(self._client, name):
            raise AttributeError(f"'InfisicalClient' object has no attribute '{name}'")
        return self._get_ns_wrapper(name)

    @functools.cache
    def _get_ns_wrapper(self, name: str) -> NamespaceWrapper:
        return NamespaceWrapper(
            wrapped_namespace=getattr(self._client, name),
            kwargs_to_inject=frozenset(
                self.settings.model_dump(exclude_unset=True).items()
            ),
        )

    @property
    def raw_client(self) -> InfisicalSDKClient:
        """
        Provides direct access to the underlying InfisicalSDKClient
        instance if needed.
        """
        return self._client
