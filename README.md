Quick start (local development):


1. Open.env file and fill in your Plivo credentials and AGENT_NUMBER.
2. Download a Vosk model and set VOSK_MODEL_PATH in .env.
3. Install requirements: pip install -r requirements.txt
4. Run the backend: uvicorn app:app --host 0.0.0.0 --port 8000
5. Expose via ngrok or deploy to a public HTTPS host.
6. Point Plivo number's Answer URL to the hosted infra/plivo_answer_url.xml endpoint.