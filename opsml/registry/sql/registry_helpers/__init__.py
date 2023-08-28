from opsml.registry.sql.settings import settings
from opsml.registry.sql.registry_helpers.client import _ClientRegistryHelper
from opsml.registry.sql.registry_helpers.server import _ServerRegistryHelper


def get_registry_helper():
    """Retrieves client or server registry helper based on settings request client status"""
    if settings.request_client is not None:
        return _ClientRegistryHelper()
    return _ServerRegistryHelper()


registry_helper = get_registry_helper()
