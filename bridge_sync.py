import json
import time
import requests
import sqlite3
from typing import Dict, Any
from datetime import datetime

# Configuration
INSIGHTFLOW_ENDPOINT = "http://127.0.0.1:8000/receive_telemetry" # Mock endpoint
MAX_RETRIES = 5
RETRY_DELAY_SEC = 5

class TelemetryBridge:
    def __init__(self, db_path="telemetry/bridge_buffer.db"):
        self.db_path = db_path
        self._setup_db()
        print(f"Bridge Sync Initialized. Buffer: {db_path}")

    def _setup_db(self):
        """Phase 3: Setup SQLite buffer for offline events."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_json TEXT NOT NULL,
                retries INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def buffer_event(self, event_packet: Dict[str, Any]):
        """Phase 3: Adds an event to the SQLite buffer/queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        event_json = json.dumps(event_packet)
        cursor.execute(
            "INSERT INTO event_queue (event_json) VALUES (?)", (event_json,)
        )
        conn.commit()
        conn.close()

    def _log_transmission(self, event_id: int, status: str):
        """Phase 3: Logs transmission success/failure."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": event_id,
            "status": status,
        }
        try:
            with open("telemetry/integration_log.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except FileNotFoundError:
            print("Warning: /telemetry folder not found. Skipping integration log.")


    def sync_events(self):
        """
        Reads from the queue, attempts transmission, and handles retry/delete.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Select the oldest event (FIFO queue behavior)
        cursor.execute("SELECT id, event_json, retries FROM event_queue ORDER BY id ASC LIMIT 1")
        row = cursor.fetchone()
        
        if not row:
            # print("Buffer is empty. Waiting for new events...")
            conn.close()
            return
            
        event_id, event_json, retries = row
        event_packet = json.loads(event_json)
        
        print(f"Attempting to sync event ID {event_id} (Retries: {retries})...")

        try:
            # Pushes events to InsightFlow receiver
            response = requests.post(
                INSIGHTFLOW_ENDPOINT, 
                json=event_packet, 
                timeout=5
            )

            if response.status_code == 200:
                # Success: delete from buffer and log
                cursor.execute("DELETE FROM event_queue WHERE id = ?", (event_id,))
                self._log_transmission(event_id, "SUCCESS")
                print(f" Event ID {event_id} synced successfully.")
            else:
                # Failure: retry logic
                raise requests.exceptions.HTTPError(f"HTTP Status: {response.status_code}")

        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            # Phase 3: Simple queue/retry logic
            retries += 1
            if retries <= MAX_RETRIES:
                cursor.execute(
                    "UPDATE event_queue SET retries = ? WHERE id = ?", 
                    (retries, event_id)
                )
                self._log_transmission(event_id, f"RETRY_{retries}")
                print(f" Sync failed (attempt {retries}): {e}. Retrying later.")
                time.sleep(RETRY_DELAY_SEC) # Wait before next attempt (optional: only if running in a loop)
            else:
                # Max retries reached: delete and log as final failure
                cursor.execute("DELETE FROM event_queue WHERE id = ?", (event_id,))
                self._log_transmission(event_id, "FAILED_MAX_RETRIES")
                print(f" Event ID {event_id} failed after {MAX_RETRIES} attempts. Dropped.")
        
        conn.commit()
        conn.close()

# Main loop to run the bridge service (optional: can be run as a service)
# if __name__ == "__main__":
#     bridge = TelemetryBridge()
#     while True:
#         bridge.sync_events()
#         time.sleep(1) # Check buffer every second