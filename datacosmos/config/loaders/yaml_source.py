"""YAML settings source for pydantic-settings.

This module provides a tiny helper to inject a YAML file as a configuration
source for `pydantic-settings` (v2.x). It returns a callable compatible with
`BaseSettings.settings_customise_sources`, placed wherever you want in the
precedence chain.

- If the file is missing, the source returns an empty dict.
- Empty-ish values (`None`, empty string, empty list) are dropped so they don't
  overwrite values coming from later sources (e.g., environment variables).
- The returned callable accepts `*args, **kwargs` to be version-agnostic across
  pydantic-settings minor releases (some pass positional args, others keywords).
"""

from typing import Any, Callable, Dict

# A callable that returns a mapping of settings values when invoked by pydantic-settings.
SettingsSourceCallable = Callable[..., Dict[str, Any]]


def yaml_settings_source(file_path: str) -> SettingsSourceCallable:
    """Create a pydantic-settings-compatible source that reads from a YAML file.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the YAML file to load.

    Returns
    -------
    SettingsSourceCallable
        A callable that, when invoked by pydantic-settings, returns a dict
        of settings loaded from the YAML file. If the file does not exist,
        an empty dict is returned. Keys with empty/None values are omitted
        so later sources (e.g., env vars) can provide effective overrides.

    Notes
    -----
    The returned callable accepts arbitrary `*args` and `**kwargs` to stay
    compatible with different pydantic-settings 2.x calling conventions.
    """

    def _source(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        """Load and sanitize YAML content for use as a settings source.

        Returns
        -------
        dict
            A dictionary of settings. If the YAML file is missing, `{}`.
            Values that are `None`, empty strings, or empty lists are dropped.
        """
        import os

        import yaml

        if not os.path.exists(file_path):
            return {}
        with open(file_path, "r") as f:
            data = yaml.safe_load(f) or {}
        return {k: v for k, v in data.items() if v not in (None, "", [])}

    return _source
