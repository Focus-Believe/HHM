let ws;
let myName = null;
let target = null;

// =====================
// CHAT MEMORY (PER USER)
// =====================
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

    const d = JSON.parse(e.data);

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

    // =====================
    // TYPING
    // =====================
    if (d.type === "typing") {

      const box = document.getElementById("typing");

      box.innerText = d.from + " is typing...";

      clearTimeout(window.__typingTimer);

      window.__typingTimer = setTimeout(() => {
        box.innerText = "";
      }, 1000);
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

  const box = document.getElementById("users");
  box.innerHTML = "";

  list.forEach(user => {

    if (user === myName) return;

    const div = document.createElement("div");
    div.className = "user";

    div.innerHTML = `
      <span>${user}</span>
      <small id="status-${user}"></small>
    `;

    div.onclick = () => {

      target = user;

      document.getElementById("header").innerText = "Chat with " + user;

      markSeen(user);

      renderChat(user);
    };

    box.appendChild(div);
  });
}

// =====================
// SEND MESSAGE (FIXED)
// =====================
function send() {

  if (!target) {
    alert("Select a user first");
    return;
  }

  const input = document.getElementById("msg");
  const text = input.value.trim();

  if (text === "") return;

  const time = getTime();

  storeMessage(target, myName, text, time);

  renderChat(target);

  ws.send(JSON.stringify({
    type: "dm",
    to: target,
    msg: text
  }));

  input.value = "";
}

// =====================
// STORE MESSAGE (LOCAL CACHE)
// =====================
function storeMessage(user, sender, text, time) {

  if (!chats[user]) {
    chats[user] = [];
  }

  chats[user].push({
    sender,
    text,
    time,
    seen: false
  });
}

// =====================
// HANDLE INCOMING MESSAGE (NO DUPLICATE BUG)
// =====================
function handleIncomingMessage(d) {

  const sender = d.sender;

  const chatKey = (sender === myName) ? target : sender;

  if (!chatKey) return;

  storeMessage(chatKey, sender, d.text, d.time);

  if (chatKey === target) {
    renderChat(target);
  } else {
    increaseUnread(chatKey);
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

    let tick = "";

    if (m.sender === myName) {
      tick = m.seen ? " ✓✓" : " ✓";
    }

    const div = document.createElement("div");

    div.className = "msg " + (m.sender === myName ? "me" : "other");

    div.innerHTML = `
      <div class="text">${m.text} ${tick}</div>
      <div class="time">${m.time}</div>
    `;

    box.appendChild(div);
  });

  box.scrollTop = box.scrollHeight;
}

// =====================
// MARK SEEN
// =====================
function markSeen(user) {

  ws.send(JSON.stringify({
    type: "seen",
    user: user
  }));
}

// =====================
// TYPING EVENT
// =====================
function typing() {

  if (!target) return;

  ws.send(JSON.stringify({
    type: "typing",
    to: target
  }));
}

// =====================
// UNREAD SYSTEM
// =====================
function increaseUnread(user) {

  const el = document.getElementById("status-" + user);

  if (!el) return;

  let count = parseInt(el.innerText || "0");

  el.innerText = (count + 1) + " new";
}

// =====================
// TIME FORMAT
// =====================
function getTime() {

  const d = new Date();

  return d.getHours() + ":" + String(d.getMinutes()).padStart(2, "0");
    }
