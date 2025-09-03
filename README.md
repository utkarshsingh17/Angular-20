from autogen_agentchat.agents import AssistantAgent
from tools import validator_tools

def create_validator_agent():
    return AssistantAgent(
        name="ValidatorAgent",
        system_message=(
            "You are a validator agent. "
            "You check summaries, entity extractions, and Q&A answers. "
            "If something is invalid, recommend rollback or human review."
        ),
        description="Agent for validation.",
        tools=[
            validator_tools.validate_summary,
            validator_tools.validate_entities,
            validator_tools.validate_answer,
        ]
    )
