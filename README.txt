ANCIENT VIBE TICKET GENERATOR — DEPLOY TO RENDER

1. Create a GitHub repository named ancient-vibe-ticket-generator.
2. Upload app.py, requirements.txt, and render.yaml from this folder.
3. In Render, choose New + > Web Service and connect the repository.
4. Use build command: pip install -r requirements.txt
5. Use start command: gunicorn app:app
6. Deploy and open the Render URL.

IMPORTANT LIMITS:
- Starter demo stores generated batches in server memory; restarting the service clears them.
- QR codes encode ticket IDs, but this starter does NOT validate tickets against a permanent database and does not stop duplicate scans.
- Before selling tickets, add persistent database storage and a protected check-in/scan endpoint with one-time redemption.
