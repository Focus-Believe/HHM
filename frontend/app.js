let ws;
let myName = null;
let target = null;

// =====================
// CHAT MEMORY
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
    // REGISTER SUCCESS
    // =====================
    if (d.type === "register") {

      if (d.ok) {
        alert("Register success");
      } else {
        alert("Username already exists");
      }
    }

    // =====================
    // USERS LIST
    // =====================
    if (d.type === "users") {
      renderUsers(d.data);
    }

    // =====================
    // MESSAGE
    // =====================
    if (d.type === "message") {
      handleIncomingMessage(d);
    }

    // =====================
    // TYPING
    // =====================
    if (d.type === "typing") {

      const typingBox = document.getElementById("typing");

      typingBox.innerText = d.from + " is typing...";

      clearTimeout(window.typingTimer);

      window.typingTimer = setTimeout(() => {
        typingBox.innerText = "";
      }, 1000);
    }

    // =====================
    // PONG
    // =====================
    if (d.type === "pong") {
      console.log("pong:", d.time);
    }
  };

  // =====================
  // AUTO RECONNECT
  // =====================
  ws.onclose = () => {

    console.log("Disconnected");

    setTimeout(() => {

      console.log("Reconnecting...");
      connect();

    }, 2000);
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

  const usersBox = document.getElementById("users");

  usersBox.innerHTML = "";

  list.forEach(user => {

    // hide self
    if (user === myName) return;

    const div = document.createElement("div");

    div.className = "user";

    div.innerHTML = `
      <span>${user}</span>
      <small id="status-${user}"></small>
    `;

    // =====================
    // OPEN CHAT
    // =====================
    div.onclick = () => {

      target = user;

      document.getElementById("header").innerText =
        "Chat with " + user;

      // active style
      document.querySelectorAll(".user")
        .forEach(x => x.classList.remove("active"));

      div.classList.add("active");

      // clear unread
      const unread = document.getElementById("status-" + user);

      if (unread) {
        unread.innerText = "";
      }

      // seen
      markSeen(user);

      // render messages
      renderChat(user);
    };

    usersBox.appendChild(div);
  });
}

// =====================
// SEND MESSAGE
// FIXED (NO DUPLICATE)
// =====================
function send() {

  if (!target) {
    alert("Select a user first");
    return;
  }

  const input = document.getElementById("msg");

  const text = input.value.trim();

  if (text === "") return;

  // SEND ONLY
  // server will return once
  ws.send(JSON.stringify({
    type: "dm",
    to: target,
    msg: text
  }));

  input.value = "";
}

// =====================
// HANDLE MESSAGE
// =====================
function handleIncomingMessage(d) {

  const sender = d.sender;

  // if own msg
  let chatUser;

  if (sender === myName) {
    chatUser = target;
  } else {
    chatUser = sender;
  }

  if (!chatUser) return;

  // create memory
  if (!chats[chatUser]) {
    chats[chatUser] = [];
  }

  // store once only
  chats[chatUser].push({
    sender: sender,
    text: d.text,
    time: d.time,
    delivered: d.delivered || false,
    seen: false
  });

  // active chat
  if (chatUser === target) {

    renderChat(chatUser);

    // auto seen
    if (sender !== myName) {
      markSeen(chatUser);
    }

  } else {

    // unread count
    increaseUnread(chatUser);
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

    // own message
    if (m.sender === myName) {

      if (m.seen) {
        tick = " ✓✓";
      } else if (m.delivered) {
        tick = " ✓";
      }
    }

    const div = document.createElement("div");

    div.className =
      "msg " +
      (m.sender === myName ? "me" : "other");

    div.innerHTML = `
      <div class="text">
        ${m.text}${tick}
      </div>

      <div class="time">
        ${m.time}
      </div>
    `;

    box.appendChild(div);
  });

  // auto scroll
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
// TYPING
// =====================
function typing() {

  if (!target) return;

  ws.send(JSON.stringify({
    type: "typing",
    to: target
  }));
}

// =====================
// UNREAD
// =====================
function increaseUnread(user) {

  const el =
    document.getElementById("status-" + user);

  if (!el) return;

  let count =
    parseInt(el.innerText || "0");

  count++;

  el.innerText = count + " new";
}

// =====================
// HEARTBEAT
// =====================
setInterval(() => {

  if (ws && ws.readyState === 1) {

    ws.send(JSON.stringify({
      type: "ping"
    }));
  }

}, 30000);
