from typing import Any, Dict, Callable

SettingsSourceCallable = Callable[..., Dict[str, Any]]

def yaml_settings_source(file_path: str) -> SettingsSourceCallable:
    def _source(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        import os, yaml
        if not os.path.exists(file_path):
            return {}
        with open(file_path, "r") as f:
            data = yaml.safe_load(f) or {}
        return {k: v for k, v in data.items() if v not in (None, "", [])}
    return _source
