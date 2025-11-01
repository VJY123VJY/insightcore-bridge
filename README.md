
# InsightCore Bridge (mock telemetry pipeline)

Small telemetry simulation and bridge utilities used to generate, structure,
buffer and transmit telemetry events to a mock InsightFlow receiver.

## Project purpose

This repository simulates an application pipeline that:
- generates structured telemetry events,
- buffers events locally in a SQLite queue,
- retries and syncs events to an HTTP receiver (mocked via Flask).

It's intended for local testing of telemetry ingestion and for developing
robust bridge logic with retries and offline buffering.

## Project structure

Top-level files
- `insights_generator.py` — simulates event generation and drives the bridge sync loop.
- `event_structurer.py` — formats raw insight data into the project's event schema and writes to `telemetry/event_stream.json`.
- `bridge_sync.py` — implements `TelemetryBridge`: SQLite buffer, buffer_event, sync_events, and logging to `telemetry/integration_log.json`.
- `mock_insightflow_receiver.py` — Flask mock HTTP receiver with endpoints `/` and `/receive_telemetry`.
- `README.md` — this file.

Telemetry folder
- `telemetry/event_stream.json` — append-only structured event stream (one JSON per line).
- `telemetry/integration_log.json` — append-only records of bridge transmissions (one JSON per line).
- `telemetry/bridge_buffer.db` — SQLite DB created at runtime by `TelemetryBridge`.

## Dependencies

The project uses the following Python packages:
- `requests` — HTTP client used by `bridge_sync.py`.
- `Flask` — mock receiver in `mock_insightflow_receiver.py`.

Create a virtual environment and install dependencies (recommended):

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows (Bash): .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install Flask requests
```

Optionally create a `requirements.txt` with:

```
Flask>=2.0
requests>=2.0
```

## How to run (local development)

1) Start the mock receiver (listens on port 8000):

```bash
python c:/Users/Admin/Desktop/insightcore-bridge/mock_insightflow_receiver.py
```

2) In another terminal, run the telemetry generator which buffers events and
	 triggers the sync loop:

```bash
python c:/Users/Admin/Desktop/insightcore-bridge/insights_generator.py
```

3) Manual test (send a single event):

```bash
curl -i -X POST http://127.0.0.1:8000/receive_telemetry \
	-H "Content-Type: application/json" \
	-d '{"source":"te","event_type":"positive_feedback","state":"ok","reward":0.953,"timestamp":"2025-11-01T22:02:20"}'
```

Expected behavior:
- The mock receiver prints the received event to its console and returns HTTP 200.
- `TelemetryBridge` will remove successfully-sent events from `telemetry/bridge_buffer.db` and append a success entry to `telemetry/integration_log.json`.

## Files of interest (short descriptions)
- `insights_generator.py`: Simulates concurrent tasks, creates event packets and calls `TelemetryBridge.buffer_event`.
- `event_structurer.py`: Converts raw data to the final event schema used by the system.
- `bridge_sync.py`: Local SQLite queue + sync logic. Important constants: `INSIGHTFLOW_ENDPOINT`, `MAX_RETRIES`, `RETRY_DELAY_SEC`.
- `mock_insightflow_receiver.py`: Flask app to mimic the remote ingestion endpoint.

## Development notes & suggestions

- Add a permanent `get_queue_size(self)` method to `TelemetryBridge` (currently patched by `insights_generator.py`) for clarity and reuse.
- Consider adding a `requirements.txt` to lock dependencies.
- Replace prints with Python `logging` for better control and levels.
- For production-like testing, add authentication/TLS to the receiver and avoid accepting unauthenticated POSTs.
- Consider batching multiple queued events per sync for throughput and add exponential backoff for retries.

## Troubleshooting

- If you see `NameError: name 'requests' is not defined` when running a selection in VS Code, that means the temp runner executed a single line referencing `requests` without the import. Run the full script (or include `import requests`) instead:

```bash
python c:/Users/Admin/Desktop/insightcore-bridge/insights_generator.py
```

- If Flask or requests isn't installed, install them into the same environment used by your interpreter (`python -m pip install Flask requests`).

## Next steps (optional edits I can make)

- Add `requirements.txt`.
- Add a permanent `get_queue_size` method to `bridge_sync.py`.
- Add a short run script or Makefile to standardize commands.

If you want any of those changes applied now, tell me which ones and I will implement them.

---

Last updated: 2025-11-01
