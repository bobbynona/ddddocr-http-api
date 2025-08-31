#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to handle shutdown signals
handle_signal() {
  echo "[Entrypoint] Received signal. Forwarding to server PID: $SERVER_PID"
  # Pass the signal to the child process
  if [ -n "$SERVER_PID" ]; then
    kill -s TERM "$SERVER_PID"
    # Wait for the child process to terminate
    wait "$SERVER_PID"
  fi
  echo "[Entrypoint] Server process stopped. Exiting."
  exit 0
}

# Trap SIGTERM (used by `docker stop`) and SIGINT (used by Ctrl+C)
trap 'handle_signal' TERM INT

echo "[Entrypoint] Starting API server in the background..."
# Start the main application in the background
uv run python main.py api &

# Capture the process ID of the background server
SERVER_PID=$!

echo "[Entrypoint] Waiting for server to become available..."
sleep 10

echo "[Entrypoint] Sending initialization request..."
curl -sS -f -X POST -H "Content-Type: application/json" -d '{"ocr": true, "det": true}' http://localhost:8000/initialize || echo "[Entrypoint] Initialization request failed or server not ready yet."

echo "[Entrypoint] Initialization process finished. Server is running."

# Wait for the server process to exit. This is the crucial part.
wait $SERVER_PID