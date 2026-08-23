# EasyChatBot AI Governance Center — V2 READY

This is an OVERLAY package for the existing EasyChatBot-Hackathon frontend.

It fixes the frontend -> FastAPI connection by adding a Vite proxy and provides the
Governance Center presentation requested:

- AI Governance Center hero
- YETI Governance Guardian
- YETI Governance Brief
- Governance Status
- Provider Controls
- Cybersecurity Governance
- Governance Events
- Audit Evidence
- responsive desktop + iPhone 11 layout
- faded governance mountains background
- YETI appears once in the hero; explanatory YETI text is reused without repeating
  the large character artwork

IMPORTANT:
This package does not replace the backend. Your existing backend governance routes
remain the authority.

Backend routes expected:
GET  /operations/governance/status
GET  /operations/governance/timeline
GET  /controls/providers/status
POST /controls/providers/pause
POST /controls/providers/resume

INSTALL / OVERLAY
-----------------
Copy the files from this ZIP into:

C:\AI Folder\EasyChatBot-Hackathon\frontend

Allow replacement of the matching files.

Then from PowerShell:

cd "C:\AI Folder\EasyChatBot-Hackathon\frontend"
npm install
npm run build
npm run dev

Open:
http://127.0.0.1:5173/operations-center/governance

Run the backend separately on:
http://127.0.0.1:8000

The Vite proxy forwards:
 /operations/* -> http://127.0.0.1:8000
 /controls/*   -> http://127.0.0.1:8000
 /governance/* -> http://127.0.0.1:8000
 /api/*        -> http://127.0.0.1:8000

IMAGE ASSETS
------------
The UI expects:
frontend/assets/governance-mountains.png
frontend/assets/character-front-cards/yeti.png

Use the governance-mountains.png supplied in the previous design work and the
approved YETI artwork already stored in the frontend asset location.

If the full YETI artwork is stored elsewhere, copy it to:
frontend/assets/character-front-cards/yeti.png

The frontend does not embed a Windows C:\Users\... path, so it remains portable.

IMPORTANT ARCHITECTURE
----------------------
YETI is presentation/decision-support only.
YETI cannot approve, pause, resume, remediate, or execute operational controls.

Human authority remains required for control changes.
