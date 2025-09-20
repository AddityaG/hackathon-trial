# agent_credentials.py
# A simple mock database for agent credentials.

# Agent Credentials for Authentication
AGENT_CREDENTIALS = {
    # Consumer Agent
    "consumer_agent_1": {
        "client_secret": "consumer_secret_1",
        "scopes": ["consumer:write", "consumer:read"]
    },
    # Bank Agents
    "bank_agent_a": {
        "client_secret": "bank_secret_a",
        "scopes": ["bank:write", "bank:read"]
    },
    "bank_agent_b": {
        "client_secret": "bank_secret_b",
        "scopes": ["bank:write", "bank:read"]
    }
}

# Map of agent IDs to their allowed scopes
SCOPES_MAP = {
    "consumer_agent_1": ["consumer:write", "consumer:read"],
    "bank_agent_a": ["bank:write", "bank:read"],
    "bank_agent_b": ["bank:write", "bank:read"]
}
