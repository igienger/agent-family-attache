import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


@functools.cache
def _get_valid_params(target_callable: Callable) -> set[str]:
    """
    Inspects a callable and returns a set of its parameter names.

    Results are cached indefinitely so `inspect.signature` is only
    called once per method.
    """
    try:
        sig = inspect.signature(target_callable)
        return set(sig.parameters.keys())
    except (ValueError, TypeError):
        # ValueError: e.g., C-compiled functions
        # TypeError: e.g., some built-ins like print()
        # We can't inspect it, so we can't inject anything.
        return set()


class NamespaceWrapper:
    """
    Wraps an object and intercepts attribute access.

    When a callable attribute (a method) is accessed, this class
    returns a new function. This new function will automatically
    inject a set of default keyword arguments *before* calling
    the original method.

    - User-provided arguments at call time always take precedence.
    - Arguments are only injected if the original method's
      signature actually accepts them.
    - Non-callable attributes (properties) are returned directly.
    """

    def __init__(
        self, wrapped_namespace: object, kwargs_to_inject: frozenset[str, Any]
    ):
        """
        Initializes the wrapper.

        Args:
            wrapped_namespace: The underlying object to delegate calls to
                               (e.g., client.secrets).
            kwargs_to_inject: The default keyword arguments to inject
                                into any method calls (e.g., secret_path="...").
        """
        self._wrapped_namespace = wrapped_namespace
        self._injected_kwargs = kwargs_to_inject

    def __getattr__(self, name: str) -> Any:
        """
        Called when an attribute is accessed (e.g., .read_secret).

        This is the core of the delegation and injection logic.
        """
        # Get the real attribute (method or property)
        try:
            target_attr = getattr(self._wrapped_namespace, name)
        except AttributeError:
            # Raise a clear error if the method doesn't exist
            raise AttributeError(
                f"'{type(self._wrapped_namespace).__name__}' object "
                f"has no attribute '{name}'"
            )

        if not callable(target_attr):
            return target_attr  # Directly return non-callable attributes

        # Figure out which kwargs can be injected
        valid_params = _get_valid_params(target_attr)
        kwargs_to_inject: dict[str, Any] = {
            key: value for key, value in self._injected_kwargs if key in valid_params
        }

        # Return the wrapper function
        @functools.wraps(target_attr)
        def method_wrapper(*args, **call_kwargs):
            """
            This function is returned to the caller.
            It wraps the real method and merges default kwargs
            with call-time kwargs.
            """

            # This is the key logic:
            # 1. Start with the pre-calculated, valid defaults.
            # 2. Unpack the user's call_kwargs on top.
            # This cleanly and efficiently overrides any defaults
            # with the user-provided arguments.
            final_kwargs = {**kwargs_to_inject, **call_kwargs}

            # Call the original method with the final, merged args
            return target_attr(*args, **final_kwargs)

        return method_wrapper
