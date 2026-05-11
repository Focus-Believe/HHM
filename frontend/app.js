let ws;
let target = null;
let myName = null;

// chat memory
let chats = {};

// =====================
// CONNECT WEBSOCKET
// =====================
function connect() {

  ws = new WebSocket(
    (location.protocol === "https:" ? "wss://" : "ws://") +
    location.host +
    "/ws"
  );

  ws.onmessage = (e) => {

    let d = JSON.parse(e.data);

    // =====================
    // LOGIN SUCCESS
    // =====================
    if (d.type === "login" && d.ok) {

      myName = document.getElementById("name").value;

      document.getElementById("login").style.display = "none";
      document.getElementById("app").style.display = "flex";
    }

    // =====================
    // USERS LIST
    // =====================
    if (d.type === "users") {
      renderUsers(d.data);
    }

    // =====================
    // MESSAGE RECEIVE
    // =====================
    if (d.type === "message") {
      handleIncomingMessage(d);
    }
  };
}

// =====================
// LOGIN
// =====================
function login() {

  connect();

  ws.onopen = () => {

    ws.send(JSON.stringify({
      type: "login",
      name: document.getElementById("name").value,
      password: document.getElementById("pass").value
    }));
  };
}

// =====================
// REGISTER
// =====================
function register() {

  connect();

  ws.onopen = () => {

    ws.send(JSON.stringify({
      type: "register",
      name: document.getElementById("name").value,
      password: document.getElementById("pass").value
    }));
  };
}

// =====================
// RENDER USERS
// =====================
function renderUsers(list) {

  const usersDiv = document.getElementById("users");
  const header = document.getElementById("header");

  usersDiv.innerHTML = "";

  list.forEach(u => {

    if (u === myName) return;

    let div = document.createElement("div");
    div.className = "user";
    div.innerText = u;

    div.onclick = async () => {

      target = u;
      header.innerText = "Chat with " + u;

      document.querySelectorAll(".user")
        .forEach(x => x.classList.remove("active"));

      div.classList.add("active");

      await loadHistory(u);
    };

    usersDiv.appendChild(div);
  });
}

// =====================
// LOAD CHAT HISTORY (NEW)
// =====================
async function loadHistory(user) {

  try {

    let res = await fetch(`/history/${myName}/${user}`);
    let data = await res.json();

    chats[user] = [];

    data.forEach(m => {

      storeMsg(
        user,
        m.sender,
        m.msg,
        m.time
      );
    });

    renderChat(user);

  } catch (err) {
    console.log(err);
  }
}

// =====================
// SEND MESSAGE
// =====================
function send() {

  if (!target) {
    alert("Select a user first");
    return;
  }

  const msgInput = document.getElementById("msg");
  const text = msgInput.value.trim();

  if (text === "") return;

  const time = getTime();

  // instant UI
  storeMsg(target, myName, text, time);
  renderChat(target);

  ws.send(JSON.stringify({
    type: "dm",
    to: target,
    msg: text
  }));

  msgInput.value = "";
}

// =====================
// STORE MESSAGE
// =====================
function storeMsg(user, sender, text, time) {

  if (!chats[user]) {
    chats[user] = [];
  }

  chats[user].push({
    sender,
    text,
    time
  });
}

// =====================
// HANDLE INCOMING MESSAGE
// =====================
function handleIncomingMessage(d) {

  let sender = d.sender;
  let text = d.text;
  let time = d.time;

  let key = (sender === myName) ? target : sender;

  if (!key) return;

  storeMsg(key, sender, text, time);

  if (key === target) {
    renderChat(target);
  }
}

// =====================
// RENDER CHAT
// =====================
function renderChat(user) {

  const box = document.getElementById("messages");
  box.innerHTML = "";

  if (!chats[user]) return;

  chats[user].forEach(m => {

    let div = document.createElement("div");

    div.className =
      "msg " +
      (m.sender === myName ? "me" : "other");

    div.innerHTML = `
      <div class="text">${m.text}</div>
      <div class="time">${m.sender} • ${m.time}</div>
    `;

    box.appendChild(div);
  });

  box.scrollTop = box.scrollHeight;
}

// =====================
// TIME
// =====================
function getTime() {

  let d = new Date();

  return d.getHours() + ":" +
    String(d.getMinutes()).padStart(2, "0");
  }
