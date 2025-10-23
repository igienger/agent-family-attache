"""
Python library for a pre-configured Infisical SDK Client.
"""

# Import the main classes to make them available when
# someone imports the package
from .api_settings import ApiSettings
from .client import ClientSettings, InfisicalClient

# Controls what `from infisical_client import *` imports
__all__ = ["InfisicalClient", "ApiSettings", "ClientSettings"]
