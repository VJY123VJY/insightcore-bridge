import asyncio
import random
import time
from bridge_sync import TelemetryBridge
import sqlite3
# Initialize the bridge
TELEMETRY_BRIDGE = TelemetryBridge()

# List of users and possible task states
USERS = ["Priya", "Vijay", "Raj"]
STATES = ["completed", "positive_feedback", "negative_feedback", "skipped"]

def create_event(task_id: int, user: str, state: str):
    """Creates a structured telemetry event packet."""
    
    # Calculate a simple reward/signal based on the state
    if state == "completed" or state == "positive_feedback":
        reward = random.uniform(0.5, 1.0)
    elif state == "negative_feedback":
        reward = random.uniform(-1.0, -0.5)
    else:
        reward = 0.0 # skipped

    event_packet = {
        "timestamp": time.time(),
        "source": "InsightCore",
        "task_id": f"Task {task_id}",
        "user_id": user,
        "event_type": "task_update",
        "state": state,
        "reward": round(reward, 3)
    }
    return event_packet

async def main_insightcore_loop(num_events: int):
    """
    Phase 2: Simulates the generation of concurrent telemetry events
    and buffers them via the TelemetryBridge.
    """
    
    tasks = []
    
    print(f"--- Starting simulation of {num_events} events ---")

    for i in range(1, num_events + 1):
        # Determine the sequence of processing and event generation
        user = random.choice(USERS)
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.01, 0.1))
        print(f"--- Processing Task {i} for {user} ---")
        
        # Simulate event generation after processing
        state = random.choice(STATES)
        event = create_event(i, user, state)
        
        # Phase 3: Hand off to the bridge for buffering
        tasks.append(asyncio.to_thread(TELEMETRY_BRIDGE.buffer_event, event))
        
        print(f"[{user}] Task {i} reached state: {state}. Triggering event...")
        print(f"[{user}] Core task completed and event handed off to Bridge buffer.")

    # Wait for all buffering to finish
    await asyncio.gather(*tasks)

    # Phase 4: Start the Synchronization Loop
    print("\n--- InsightCore tasks complete. Starting Bridge Sync to clear buffer... ---")
    
    # Loop continuously until the buffer is truly empty.
    while TELEMETRY_BRIDGE.get_queue_size() > 0:
        TELEMETRY_BRIDGE.sync_events()
        # Sleep briefly to yield control and prevent maxing out the CPU
        await asyncio.sleep(0.01)

    print("\n Bridge Sync complete. The buffer is now empty.")
    

if __name__ == '__main__':
    # Add a method to the bridge to check queue size (required by the loop)
    def get_queue_size(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM event_queue")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    TelemetryBridge.get_queue_size = get_queue_size
    
    # Run the main asynchronous loop
    asyncio.run(main_insightcore_loop(num_events=12))