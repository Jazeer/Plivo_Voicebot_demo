import os
import json
import base64
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv, find_dotenv

# Load environment
env_path = find_dotenv()
load_dotenv(env_path, override=True)

print("DEBUG_AUTH_ID:", os.getenv("PLIVO_AUTH_ID"))

from backend.stt import StreamingVosk
from backend.logic import ConversationManager
from backend.plivo_client import PlivoClient
from backend.utils import logger
from backend.tts_stream import synthesize_to_pcm16_8k, pcm16_to_playAudio_payload


# -----------------------------------------------------------------------------
# FastAPI
# -----------------------------------------------------------------------------
app = FastAPI()

CALLUUID_BY_FROM = {}
LAST_CALLUUID = None
CALLUUID_WAIT_SECONDS = 3.0

VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH")
vosk = StreamingVosk(VOSK_MODEL_PATH)

plivo = PlivoClient(os.getenv("PLIVO_AUTH_ID"), os.getenv("PLIVO_AUTH_TOKEN"))
conv_mgr = ConversationManager()

CHUNK = 1600
PLAY_SLEEP = 0.02


# -----------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# -----------------------------------------------------------------------------
# /answer
# -----------------------------------------------------------------------------
@app.post("/answer")
async def answer_post(request: Request):
    global LAST_CALLUUID

    form = await request.form()
    call_uuid = form.get("CallUUID")
    caller = form.get("From")

    if call_uuid:
        LAST_CALLUUID = call_uuid
        CALLUUID_BY_FROM[caller] = call_uuid
        logger.info(f"ANSWER POST captured CallUUID={call_uuid} from={caller}")

    hostname = os.getenv("HOSTNAME")
    ws_url = f"wss://{hostname}/audiostream"

    xml = f"""
<Response>
    <Stream bidirectional="true" contentType="audio/x-l16;rate=8000" keepCallAlive="true">{ws_url}</Stream>
</Response>
"""

    return PlainTextResponse(xml, media_type="application/xml")


# -----------------------------------------------------------------------------
# Transfer XML — FIXED WITH callerId
# -----------------------------------------------------------------------------
@app.get("/forward-agent")
async def forward_agent():
    agent = os.getenv("AGENT_NUMBER")
    caller_id = "+918035737582"  # your Plivo number

    return PlainTextResponse(f"""
<Response>
    <Dial callerId="{caller_id}">
        <Number>{agent}</Number>
    </Dial>
</Response>""", media_type="application/xml")


@app.get("/forward-agent-warm")
async def forward_agent_warm():
    agent = os.getenv("AGENT_NUMBER")
    caller_id = "+918035737582"
    intro = "Connecting you to a live agent now."

    return PlainTextResponse(f"""
<Response>
    <Speak>{intro}</Speak>
    <Dial callerId="{caller_id}">
        <Number>{agent}</Number>
    </Dial>
</Response>""", media_type="application/xml")


# -----------------------------------------------------------------------------
# TTS helper
# -----------------------------------------------------------------------------

async def send_tts(ws: WebSocket, text: str):
    # Generate full PCM buffer in a thread
    pcm = await asyncio.to_thread(synthesize_to_pcm16_8k, text)
    logger.info(f"[TTS] playAudio total bytes={len(pcm)}")

    off = 0
    while off < len(pcm):
        chunk = pcm[off:off + CHUNK]
        payload = pcm16_to_playAudio_payload(chunk, sample_rate=8000)
        # IMPORTANT: send as text JSON
        await ws.send_text(json.dumps(payload))
        await asyncio.sleep(PLAY_SLEEP)
        off += CHUNK


# -----------------------------------------------------------------------------
# WebSocket Streaming
# -----------------------------------------------------------------------------
@app.websocket("/audiostream")
async def audiostream_ws(ws: WebSocket):
    await ws.accept()
    session = None

    try:
        async for raw in ws.iter_text():

            msg = json.loads(raw)
            event = msg.get("event")

            # START
            if event == "start":
                start = msg["start"]
                stream_id = start["streamId"]
                caller = start.get("from")

                session = conv_mgr.create_session(stream_id, stream_id)

                real_uuid = CALLUUID_BY_FROM.get(caller)

                waited = 0
                while not real_uuid and not LAST_CALLUUID and waited < CALLUUID_WAIT_SECONDS:
                    await asyncio.sleep(0.1)
                    waited += 0.1

                if not real_uuid:
                    real_uuid = LAST_CALLUUID

                session.context["real_call_uuid"] = real_uuid
                session.context["caller"] = caller

                sample_rate = int(start.get("sampleRate", 8000))
                vosk.new_recognizer(session.session_id, sample_rate)

                logger.info(
                    f"Stream started: session={session.session_id}, caller={caller}, mapped_uuid={real_uuid}"
                )
                continue

            # MEDIA
            if event == "media":
                if not session:
                    continue

                audio = base64.b64decode(msg["media"]["payload"])
                result = vosk.accept_audio_chunk(session.session_id, audio)

                if not result.get("text"):
                    continue

                text = result["text"].strip()
                logger.info(f"Transcript: {text}")

                reply, escalate = conv_mgr.handle_user_utterance(session, text)

                if reply:
                    logger.info(f"[Bot] replying: {reply}")
                    await send_tts(ws, reply)

                if escalate:
                    logger.info("[Escalation] user requested agent. Initiating transfer flow.")

                    real_uuid = session.context["real_call_uuid"]
                    host = os.getenv("HOSTNAME")
                    aleg = f"https://{host}/forward-agent"

                    logger.info(f"[Escalation] transferring call {real_uuid} → aleg={aleg}")

                    # ✅ Transfer FIRST
                    try:
                        await plivo.transfer_call(real_uuid, os.getenv("AGENT_NUMBER"), aleg)
                    except Exception as e:
                        logger.error(f"[Escalation] transfer_call failed: {e}")

                    # ✅ Stop stream AFTER
                    try:
                        await plivo.delete_streams(real_uuid)
                    except Exception as e:
                        logger.error(f"[Escalation] delete_streams (best-effort) failed: {e}")

                    conv_mgr.end_session(session.session_id)
                    break

                continue

            # STOP
            if event == "stop":
                conv_mgr.end_session(session.session_id)
                break

    except WebSocketDisconnect:
        logger.info("WS disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
    finally:
        if session:
            conv_mgr.end_session(session.session_id)
