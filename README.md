## ✅ **README.md — Plivo Real-Time Voice Bot (Non-AI, Rule-Based, Bidirectional Stream)**

```markdown
# Plivo Real-Time Voice Bot (Python + FastAPI + Vosk + TTS)

This project implements a **real-time, non-AI voice assistant** using:

- ✅ Plivo inbound voice calls  
- ✅ Bidirectional audio streaming (WebSocket `<Stream>` XML)  
- ✅ Offline speech-to-text using **Vosk** (no LLM required)  
- ✅ Rule-based response logic (no ML/AI)  
- ✅ Text-to-speech using macOS `say` (or eSpeak fallback)  
- ✅ Live agent escalation + call transfer  
- ✅ Automatic stream cleanup  
- ✅ Fully stateless, no database required

---

## 📂 Project Structure

```

Plivo_support_demo/
│
├── backend/
│   ├── app.py              # FastAPI server + WebSocket handler
│   ├── plivo_client.py     # Transfer + delete stream API wrappers
│   ├── logic.py            # Rule-based bot responses
│   ├── stt.py              # Vosk STT engine
│   ├── tts_stream.py       # TTS → PCM conversion
│   ├── utils.py            # Normalization helpers
│
├── models/                 # Vosk model folder (NOT included in repo)
│
├── requirements.txt
├── README.md
└── .gitignore

```

---

## ✅ Prerequisites

### **System requirements**
- macOS (tested)
- Python **3.10 – 3.12**
- Homebrew installed

### **Plivo setup**
1. Create a Plivo **Voice Application**
2. Assign your Plivo number
3. Set URLs:

```

Answer URL:
https://<your-ngrok-url>/answer

App type: XML

````

---

## 🔧 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/<your-username>/plivo-voice-bot.git
cd plivo-voice-bot
````

### 2️⃣ Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🎤 Download Vosk STT Model (Required)

We do **NOT** commit models to GitHub.

### Download model manually:

```bash
mkdir -p models
cd models
curl -O https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
mv vosk-model-en-us-0.22 .
```

Verify:

```
models/vosk-model-en-us-0.22/
```

---

## 🔈 Enable macOS Text-to-Speech

Already installed — confirm voices:

```bash
say -v '?'
```

Recommended voice:

```bash
say -v Samantha "Voice check successful."
```

Linux users will auto-fallback to **eSpeak**.

---

## 🚀 Run the Server

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

You should see:

```
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

---

## 🌐 Expose with Ngrok

```bash
ngrok http 8000
```

Copy your public URL and update Plivo **Answer URL**:

```
https://<ngrok-url>/answer
```

---

## 📞 How It Works — Call Flow

1. Caller dials your Plivo number
2. Plivo fetches `/answer`
3. XML responds with:

```xml

<Response>
    <Stream bidirectional="true" contentType="audio/x-l16;rate=8000" keepCallAlive="true">wss://<ngrok>/audiostream</Stream>
</Response>
```

4. WebSocket begins:

   * Plivo sends caller audio
   * Bot processes speech using Vosk
   * Logic engine generates a reply
   * Bot streams TTS audio back

5. If caller says *“human agent”*:

   * Bot replies
   * Plivo call is transferred via API
   * Streaming session is closed cleanly

---

## 🤖 Supported Speech Commands (Rule-Based)

| User Says Contains                 | Bot Response                                    |
| ---------------------------------- | ----------------------------------------------- |
| `hello`, `hi`                      | "Hello! How can I assist you today?"            |
| `help`, `issue`, `problem`         | "Sure, please tell me what you need help with." |
| `agent`, `representative`, `human` | Triggers live agent transfer                    |
| Anything else                      | "I'm here to assist you. Please tell me more."  |

Customize in:

```
backend/logic.py
```

---

## ✅ Live Agent Transfer

Triggered only when logic detects intent.

Plivo uses:

```
transfer_call(call_uuid, callerId, aleg_url)
```

Call forwarding XML at:

```
/forward-agent
```

Example response:

```xml
<Response>
  <Dial callerId="+91xxxxxxxxx">
    <Number>+91xxxxxxxxxx</Number>
  </Dial>
</Response>
```

---




Just say the word 🚀
```
