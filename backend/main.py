import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

import db
from manager import Manager

app = FastAPI()
mgr = Manager()

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")


async def send_users():
    users = mgr.users()
    for ws in list(mgr.name_to_ws.values()):
        try:
            await ws.send_text(json.dumps({"type":"users","data":users}))
        except:
            mgr.disconnect(ws)


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = json.loads(await websocket.receive_text())
            t = data["type"]

            if t == "register":
                ok = db.register(data["name"],data["password"])
                await websocket.send_text(json.dumps({"type":"register","ok":ok}))

            elif t == "login":
                ok = db.login(data["name"],data["password"])
                if ok:
                    await mgr.connect(data["name"],websocket)
                    await send_users()

                await websocket.send_text(json.dumps({"type":"login","ok":ok}))

            elif t == "dm":
                sender = mgr.get_name(websocket)
                target = mgr.get_ws(data["to"])
                time = datetime.now().strftime("%H:%M")

                db.save(sender,data["to"],data["msg"],time)

                if target:
                    await target.send_text(json.dumps({
                        "type":"msg",
                        "from":sender,
                        "msg":data["msg"],
                        "time":time
                    }))

    except WebSocketDisconnect:
        mgr.disconnect(websocket)
        await send_users()
