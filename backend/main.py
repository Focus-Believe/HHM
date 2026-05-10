import json
import os
import asyncio

from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend import db
from backend.manager import Manager

app = FastAPI()
mgr = Manager()

# =========================
# SAVE QUEUE
# =========================
save_queue = asyncio.Queue()


# =========================
# DB SAVE WORKER
# =========================
async def save_worker():

    while True:

        # queue থেকে next message নাও
        sender, receiver, msg, time = await save_queue.get()

        # database save
        db.save(sender, receiver, msg, time)

        print(f"Saved: {msg}")


# =========================
# START WORKER
# =========================
@app.on_event("startup")
async def startup():

    # background worker start
    asyncio.create_task(save_worker())


# =========================
# PATH SETUP (Render safe)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")


# =========================
# STATIC FILES
# =========================
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# =========================
# HOME PAGE
# =========================
@app.get("/")
async def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# =========================
# USERS BROADCAST
# =========================
async def send_users():

    users = mgr.users()

    for ws in list(mgr.name_to_ws.values()):

        try:
            await ws.send_text(json.dumps({
                "type": "users",
                "data": users
            }))

        except:
            mgr.disconnect(ws)


# =========================
# WEBSOCKET
# =========================
@app.websocket("/ws")
async def ws(websocket: WebSocket):

    await websocket.accept()

    try:

        while True:

            data = json.loads(await websocket.receive_text())

            t = data.get("type")

            # -----------------
            # REGISTER
            # -----------------
            if t == "register":

                ok = db.register(
                    data["name"],
                    data["password"]
                )

                await websocket.send_text(json.dumps({
                    "type": "register",
                    "ok": ok
                }))

            # -----------------
            # LOGIN
            # -----------------
            elif t == "login":

                ok = db.login(
                    data["name"],
                    data["password"]
                )

                if ok:
                    await mgr.connect(
                        data["name"],
                        websocket
                    )

                    await send_users()

                await websocket.send_text(json.dumps({
                    "type": "login",
                    "ok": ok
                }))

            # -----------------
            # DIRECT MESSAGE
            # -----------------
            elif t == "dm":

                sender = mgr.get_name(websocket)

                target_ws = mgr.get_ws(data["to"])

                time = datetime.now().strftime("%H:%M")

                # =====================
                # SAVE TO QUEUE
                # =====================
                await save_queue.put((
                    sender,
                    data["to"],
                    data["msg"],
                    time
                ))

                # =====================
                # SEND MESSAGE
                # =====================
                if target_ws:

                    await target_ws.send_text(json.dumps({
                        "type": "message",
                        "sender": sender,
                        "text": data["msg"],
                        "time": time
                    }))

    except WebSocketDisconnect:

        mgr.disconnect(websocket)

        await send_users()
