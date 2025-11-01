import json
from datetime import datetime
from typing import Dict, Any

# --- Phase 1: Define the core schema structure and reward map ---

# Reward map for Phase 4
REWARD_MAP = {
    "completed": +1,
    "skipped": -1,
    "positive_feedback": +2,
    "negative_feedback": -2,
}

def generate_telemetry_event(
    raw_insight_data: Dict[str, Any],
    event_type: str,
    context: str = "user_behavior"
) -> Dict[str, Any]:
    """
    Input: Raw log data from InsightCore.
    Output: Formatted JSON object matching the required schema.
    """
    state = raw_insight_data.get("state", "unknown")
    
    # Phase 4: Calculate reward based on state/feedback
    reward = REWARD_MAP.get(state, 0)

    # The formatted event packet (Phase 1 schema)
    event_packet = {
        "source": "InsightCore",
        "event_type": event_type,
        "context": context,
        "state": state,
        "reward": reward,
        "timestamp": datetime.utcnow().isoformat() + "Z", # ISO8601
        "data": raw_insight_data # Include full raw data for context
    }
    
    # Phase 2: Save to a local stream file for immediate inspection
    _save_to_event_stream(event_packet)
    
    return event_packet

def _save_to_event_stream(event_packet: Dict[str, Any]):
    """Saves the structured event to the telemetry stream file."""
    try:
        # Appends the new event JSON line to the file
        with open("telemetry/event_stream.json", "a") as f:
            f.write(json.dumps(event_packet) + "\n")
    except FileNotFoundError:
        print("Warning: /telemetry folder not found. Skipping local save.")


# Example usage (not run in main script, just for testing modularity)
if __name__ == "__main__":
    example_raw_data = {"user_id": "vj_dhn", "task_id": 42, "state": "completed"}
    event = generate_telemetry_event(example_raw_data, "task_update")
    print(json.dumps(event, indent=2))