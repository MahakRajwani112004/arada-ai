"""Channel integrations for MagoneAI.

This module provides integrations for external messaging platforms
like Microsoft Teams, Slack, etc.
"""

from .teams.handler import TeamsHandler
from .teams.client import TeamsClient

__all__ = ["TeamsHandler", "TeamsClient"]
