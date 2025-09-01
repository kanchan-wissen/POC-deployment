import os
import json
from pathlib import Path
from browser_use.agent.service import Agent

# Local storage directory for agent states
AGENT_STATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'agent_states')

def ensure_agent_states_dir():
    """Ensure the agent states directory exists"""
    os.makedirs(AGENT_STATES_DIR, exist_ok=True)

def save_agent_history_to_local(agent: Agent, session_id: str):
    """Save agent history to local file storage"""
    ensure_agent_states_dir()
    
    file_path = os.path.join(AGENT_STATES_DIR, f"{session_id}.json")
    
    try:
        # Try to load existing data
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = []  # Start fresh if file doesn't exist
    except Exception:
        existing_data = []  # Start fresh if file is corrupted

    # Save entire agent state as a dict (deeply serializes everything inside)
    new_data = agent.state.model_dump()

    # Append the new snapshot
    existing_data.append(new_data)

    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Agent state saved to local file: {file_path}")

def load_agent_history_from_local(session_id: str) -> list[dict]:
    """Load agent history from local file storage"""
    ensure_agent_states_dir()
    
    file_path = os.path.join(AGENT_STATES_DIR, f"{session_id}.json")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return json.loads(content)
    except Exception:
        print(f"⚠️ No previous history found for session {session_id}")
        return []
