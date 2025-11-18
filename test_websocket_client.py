#!/usr/bin/env python3
"""
Manual WebSocket client for testing real-time metrics streaming.

Usage:
    python3 test_websocket_client.py

This script connects to the WebSocket endpoint and prints metrics updates
in real-time to verify the 5-second broadcast interval and data structure.
"""

import asyncio
import json
import websockets
from datetime import datetime


async def test_websocket_connection():
    """Test WebSocket connection and metrics streaming"""
    uri = "ws://localhost:8000/ws/metrics"

    print(f"[{datetime.now().isoformat()}] Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{datetime.now().isoformat()}] Connected successfully!")
            print("-" * 80)

            # Receive and display 6 updates (30 seconds total)
            for i in range(6):
                start_time = datetime.now()

                message = await websocket.recv()
                data = json.loads(message)

                receive_time = datetime.now()
                latency_ms = (receive_time - start_time).total_seconds() * 1000

                print(f"\nUpdate #{i + 1} - Received at {receive_time.isoformat()}")
                print(f"Latency: {latency_ms:.2f}ms")
                print(f"Data: {json.dumps(data, indent=2)}")
                print("-" * 80)

            print(f"\n[{datetime.now().isoformat()}] Test complete - closing connection")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"[{datetime.now().isoformat()}] Connection closed: {e}")
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error: {e}")
        raise


async def test_multiple_concurrent_connections():
    """Test multiple concurrent WebSocket connections"""
    uri = "ws://localhost:8000/ws/metrics"

    print(f"\n[{datetime.now().isoformat()}] Testing multiple concurrent connections...")

    async def client_connection(client_id: int):
        """Single client connection"""
        try:
            async with websockets.connect(uri) as websocket:
                print(f"[Client {client_id}] Connected")

                # Receive 3 updates
                for i in range(3):
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"[Client {client_id}] Update {i + 1}: timestamp={data.get('timestamp')}")

                print(f"[Client {client_id}] Disconnecting")

        except Exception as e:
            print(f"[Client {client_id}] Error: {e}")

    # Run 3 concurrent clients
    await asyncio.gather(
        client_connection(1),
        client_connection(2),
        client_connection(3)
    )

    print(f"[{datetime.now().isoformat()}] All clients disconnected")


if __name__ == "__main__":
    print("=" * 80)
    print("WebSocket Metrics Streaming Test")
    print("=" * 80)

    # Test 1: Single connection with multiple updates
    print("\n--- Test 1: Single Connection with 5-Second Updates ---")
    asyncio.run(test_websocket_connection())

    # Test 2: Multiple concurrent connections
    print("\n--- Test 2: Multiple Concurrent Connections ---")
    asyncio.run(test_multiple_concurrent_connections())

    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
