import asyncio
import json
import socket
from aiortc import RTCPeerConnection, RTCSessionDescription

async def check_media_server():
    try:
        # 1. Ping the root
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/") as resp:
                print(f"Root status: {resp.status}")
                print(f"Root text: {await resp.text()}")
            
            # 2. Try to see if it accepts wrong offer
            async with session.post("http://localhost:8080/offer", json={"sdp": "invalid", "type": "offer", "session_id": "test"}) as resp:
                print(f"Offer status (expected error): {resp.status}")
                print(f"Offer text: {await resp.text()}")
    except Exception as e:
        print(f"Error checking media server: {e}")

if __name__ == "__main__":
    asyncio.run(check_media_server())
