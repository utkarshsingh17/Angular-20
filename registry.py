"""
registry.py
-----------------
A simple plugin/registry system for managing AutoGen agents.

- Allows registration of agent factories
- Supports dynamic lookup by name
- Makes it easy to plug in new agents
"""

from typing import Callable, Dict
from autogen_agentchat.agents import AssistantAgent

class AgentRegistry:
    def __init__(self):
        # Map: agent name -> factory function
        self._registry: Dict[str, Callable[[], AssistantAgent]] = {}

    def register(self, name: str, factory: Callable[[], AssistantAgent]):
        """
        Register an agent factory function under a name.
        """
        if name in self._registry:
            raise ValueError(f"Agent '{name}' already registered.")
        self._registry[name] = factory

    def get(self, name: str) -> AssistantAgent:
        """
        Create and return an agent instance by name.
        """
        if name not in self._registry:
            raise ValueError(f"Agent '{name}' not found in registry.")
        return self._registry[name]()

    def list_agents(self) -> list[str]:
        """
        List all registered agent names.
        """
        return list(self._registry.keys())


# ---- Global Singleton Registry ----
agent_registry = AgentRegistry()
