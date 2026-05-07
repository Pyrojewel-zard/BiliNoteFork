# BiliNote Deployment Handover (RFRLSERVER5)

Last updated: 2026-04-26 22:47 CST

## 1) Target and assumptions

- Server: `RFRL26@RFRLSERVER5`
- Project path on server: `/home/DataTransfer/Pyrojewel/vscode/BiliNoteFork`
- Deployment mode: source deploy (not Docker), with CUDA acceleration for ASR
- Python environment: cloned from `pacosyt` to `bilinote5090`

## 2) Configuration plan (actual applied values)

### Root `.env`

- `BACKEND_PORT=8483`
- `FRONTEND_PORT=3015`
- `VITE_FRONTEND_PORT=3015`
- `VITE_API_BASE_URL=http://127.0.0.1:8483/api`

### `backend/.env`

- `API_BASE_URL=http://127.0.0.1`
- `SCREENSHOT_BASE_URL=http://127.0.0.1:8483/static/screenshots`
- `TRANSCRIBER_TYPE=fast-whisper`
- `WHISPER_MODEL_SIZE=medium`

Notes:
- `API_BASE_URL` intentionally has no port, because backend code appends `:{BACKEND_PORT}` internally.

## 3) Environment status

- Conda env exists: `bilinote5090`
- GPU chain verified:
  - `torch 2.10.0+cu128`
  - `torch.cuda.is_available() == True`
  - `ctranslate2.get_cuda_device_count() == 2`
- Backend ASR dependencies installed in `bilinote5090`:
  - `faster-whisper==1.1.1`
  - `ctranslate2==4.5.0`
  - `modelscope==1.25.0`
  - `ffmpeg-python==0.2.0`
- Frontend dependencies installed with `pnpm`

## 4) Current progress

### Completed

1. Created/verified conda env `bilinote5090` from `pacosyt`.
2. Installed backend Python dependencies from `backend/requirements.txt`.
3. Fixed compatibility warning after install:
   - upgraded `sympy` to `1.14.0`
   - upgraded `filelock` to `3.29.0`
4. Generated and patched `.env` + `backend/.env`.
5. Started backend service.
6. Installed frontend deps and built frontend (`dist/` exists).
7. Started frontend preview service.
8. Verified backend and frontend local accessibility on server.

### Running services now

- Backend:
  - process: `python main.py` (pid observed: `234440`)
  - listen: `0.0.0.0:8483`
  - health sample: `GET http://127.0.0.1:8483/api/deploy_status` returns success with CUDA available
- Frontend:
  - process: `pnpm preview --host 0.0.0.0 --port 3015` (pid observed: `835389`, child node pid observed: `835449`)
  - listen: `0.0.0.0:3015`
  - health sample: `GET http://127.0.0.1:3015` returns `HTTP/1.1 200 OK`

## 5) Logs and operational commands

### Logs

- Backend log: `/tmp/bilinote-backend.log`
- Frontend log: `/tmp/bilinote-frontend.log`

### Quick checks

```bash
# backend status
curl -sS http://127.0.0.1:8483/api/deploy_status

# frontend status
curl -I http://127.0.0.1:3015
```

### Restart commands

```bash
# backend
ssh RFRL26@RFRLSERVER5 '
source /home/RFRL26/miniconda3/bin/activate bilinote5090 &&
cd /home/DataTransfer/Pyrojewel/vscode/BiliNoteFork/backend &&
pkill -f "python main.py" || true &&
nohup python main.py > /tmp/bilinote-backend.log 2>&1 &
'

# frontend
ssh RFRL26@RFRLSERVER5 '
source ~/.nvm/nvm.sh &&
cd /home/DataTransfer/Pyrojewel/vscode/BiliNoteFork/BillNote_frontend &&
pkill -f "pnpm preview --host 0.0.0.0 --port 3015" || true &&
nohup pnpm preview --host 0.0.0.0 --port 3015 > /tmp/bilinote-frontend.log 2>&1 &
'
```

## 6) Pending / next work for next AI

1. Add process supervisor (`systemd`/`pm2`) to avoid manual nohup lifecycle.
2. Validate full E2E note generation from UI:
   - upload local video
   - generate note
   - confirm ASR path uses GPU under real workload
3. Implement required local upload limits (size + duration) in backend and frontend:
   - backend hard validation in `backend/app/routers/note.py`
   - duration extraction in `backend/app/downloaders/local_downloader.py`
   - frontend pre-check in `BillNote_frontend/src/pages/HomePage/components/NoteForm.tsx`
4. Optional: pre-download target whisper model to reduce first-request latency.

