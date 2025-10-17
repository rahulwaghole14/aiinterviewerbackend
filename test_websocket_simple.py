#!/usr/bin/env python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/dg_ws"
    print(f"Testing WebSocket connection to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send test config
            config = {
                "sample_rate": 16000,
                "model": "nova-2-meeting"
            }
            await websocket.send(json.dumps(config))
            print("✅ Sent config message")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"✅ Received response: {response}")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ WebSocket connection refused - server not running or endpoint not available")
    except websockets.exceptions.InvalidURI:
        print("❌ Invalid WebSocket URI")
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timeout")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
