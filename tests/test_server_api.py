import json
import os
import sys
import threading
import time
import urllib.request
import pytest

from server import app, session
import uvicorn

@pytest.fixture(scope="module")
def live_server():
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=8991, log_level="error"),
        daemon=True,
    )
    server_thread.start()
    time.sleep(1.5)
    yield "http://127.0.0.1:8991"

def test_frontend_served(live_server):
    req = urllib.request.Request(f"{live_server}/")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        content = res.read().decode("utf-8")
        assert '<div id="root">' in content
        assert "SPCIS" in content

def test_api_status(live_server):
    req = urllib.request.Request(f"{live_server}/api/status")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode("utf-8"))
        assert data["status"] == "online"
        assert "model_loaded" in data

def test_api_topology(live_server):
    req = urllib.request.Request(f"{live_server}/api/topology")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode("utf-8"))
        assert "nodes" in data
        assert len(data["nodes"]) > 0

def test_simulation_step(live_server):
    req = urllib.request.Request(
        f"{live_server}/api/simulation/step",
        data=b"{}",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode("utf-8"))
        assert "kpis" in data
        assert "events" in data
        assert data["kpis"]["step"] >= 1
