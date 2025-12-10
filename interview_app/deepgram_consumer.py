import os
import json
import asyncio
from urllib.parse import urlencode

from channels.generic.websocket import AsyncWebsocketConsumer


class DeepgramProxyConsumer(AsyncWebsocketConsumer):
    """Bidirectional proxy between browser and Deepgram realtime WS.

    Browser connects to /dg_ws. We open a connection to Deepgram and forward
    binary audio frames upstream and transcription messages downstream.
    """

    async def connect(self):
        print(f"🔌 DeepgramProxyConsumer.connect() called!")
        self.dg_ws = None
        self.dg_task = None
        self.closed = False

        # Get Deepgram API key from Django settings (preferred) or environment variable
        try:
            from django.conf import settings as django_settings
            api_key = getattr(django_settings, 'DEEPGRAM_API_KEY', None)
            if not api_key:
                api_key = os.getenv("DEEPGRAM_API_KEY", "")
        except Exception:
            # Fallback if Django settings not available
            api_key = os.getenv("DEEPGRAM_API_KEY", "")
        print(f"🔌 Deepgram WebSocket consumer connecting... API key present: {bool(api_key)}")
        
        if not api_key:
            print(f"❌ No Deepgram API key!")
            await self.close()
            return

        print(f"✅ Accepting WebSocket connection...")
        await self.accept()
        print(f"✅ WebSocket connection accepted!")
        self.api_key = api_key
        print(f"✅ WebSocket connection accepted")

    async def receive(self, text_data=None, bytes_data=None):
        # First text message is expected to be config {sample_rate, model}
        if self.dg_ws is None and text_data:
            print(f"📡 Received config from browser: {text_data[:200]}")
            try:
                cfg = json.loads(text_data or "{}")
            except Exception as e:
                print(f"❌ Config parse error: {e}")
                cfg = {}
            sample_rate = int(cfg.get("sample_rate") or 16000)
            # Use base model instead of nova (requires paid tier)
            model = cfg.get("model") or "general"
            print(f"🔧 Opening Deepgram connection: model={model}, sample_rate={sample_rate}")
            await self._open_deepgram(sample_rate, model)
            # Notify connected
            try:
                await self.send(json.dumps({"type": "Connected"}))
                print(f"✅ Sent Connected message to browser")
            except Exception as e:
                print(f"❌ Failed to send Connected: {e}")
            return
        elif bytes_data:
            print(f"🎵 Received binary audio data: {len(bytes_data)} bytes")

        # Forward audio to Deepgram
        if bytes_data is not None and self.dg_ws is not None:
            try:
                print(f"🎵 Forwarding audio to Deepgram: {len(bytes_data)} bytes")
                await self.dg_ws.send(bytes_data)
            except Exception as e:
                print(f"❌ Failed to forward audio: {e}")
        elif bytes_data is not None:
            print(f"⚠️ Received audio data but Deepgram WebSocket is None: {len(bytes_data)} bytes")

    async def disconnect(self, code):
        self.closed = True
        try:
            if self.dg_ws is not None:
                await self.dg_ws.close()
        except Exception:
            pass

    async def _open_deepgram(self, sample_rate: int, model: str):
        # Connect to Deepgram DIRECTLY - MATCH ORIGINAL index.html
        qs = urlencode({
            "model": "nova-3",
            "language": "en-IN",
            "encoding": "linear16",
            "sample_rate": str(sample_rate),
            "channels": "1",
            "interim_results": "true",
            "punctuate": "false",
            "smart_format": "false",
        })
        url = f"wss://api.deepgram.com/v1/listen?{qs}"

        async def reader():
            import websockets
            ws = None
            try:
                print(f"🔗 Connecting to Deepgram at: {url}")
                ws = await websockets.connect(
                    url,
                    extra_headers=[("Authorization", f"Token {self.api_key}")],
                    max_queue=32,
                    ping_interval=20,
                    ping_timeout=10,
                )
                self.dg_ws = ws
                print(f"✅ Connected to Deepgram!")

                message_count = 0
                while not self.closed:
                    try:
                        msg = await ws.recv()
                        message_count += 1
                        if message_count % 10 == 1:  # Log every 10th message
                            print(f"📨 Received message #{message_count} from Deepgram")
                    except Exception as e:
                        print(f"❌ Error receiving from Deepgram: {e}")
                        break
                    try:
                        await self.send(msg)
                    except Exception as e:
                        print(f"❌ Error sending to browser: {e}")
                        break
                print(f"🔌 Deepgram reader loop ended")
            except Exception as e:
                print(f"❌ Deepgram connection error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                if ws:
                    try:
                        await ws.close()
                        print(f"🔌 Deepgram WebSocket closed")
                    except Exception:
                        pass

        # Launch background reader
        self.dg_task = asyncio.create_task(reader())


# ASGI entry point wrapper for URLRouter
deepgram_ws_app = DeepgramProxyConsumer.as_asgi()


