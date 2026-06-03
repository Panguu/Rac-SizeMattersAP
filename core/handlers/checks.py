# Re-export shim — logic lives in core/states/handlers/checks.py
from ..states.handlers.checks import (  # noqa: F401
    _on_bolt_pickup,
    _on_cutscene,
    _on_planet_change,
    _on_skill_point,
)
