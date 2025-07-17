"""OpenHands量化插件包"""

__version__ = "0.1.0"
__author__ = "OpenHands Quant Team"

from openhands_plugins.agents import FactorDevelopmentAgent
from openhands_plugins.memory import MarketWisdomExtension
from openhands_plugins.tools import QuantToolsRegistry

__all__ = [
    'FactorDevelopmentAgent',
    'MarketWisdomExtension', 
    'QuantToolsRegistry'
]
