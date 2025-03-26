"""Package for storing mission specific information."""

from datacosmos.utils.constants import PROD_MISSION_NAMES, TEST_MISSION_NAMES


def get_mission_name(mission: int, env: str) -> str:
    """Get the mission name from the mission number."""
    if env == "test" or env == "local":
        return TEST_MISSION_NAMES[mission]
    elif env == "prod":
        return PROD_MISSION_NAMES[mission]
    else:
        raise ValueError(f"Unsupported environment: {env}")


def get_mission_id(mission_name: str, env: str) -> int:
    """Get the mission number from the mission name."""
    if env == "test" or env == "local":
        return {v.upper(): k for k, v in TEST_MISSION_NAMES.items()}[
            mission_name.upper()
        ]
    elif env == "prod":
        return {v.upper(): k for k, v in PROD_MISSION_NAMES.items()}[
            mission_name.upper()
        ]
    else:
        raise ValueError(f"Unsupported environment: {env}")
