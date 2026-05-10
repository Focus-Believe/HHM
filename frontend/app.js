let ws;
let target = null;
let myName = null;

// 👉 per-user chat store
let chats = {};

// =====================
// CONNECT WEBSOCKET
// =====================
function connect(){
  ws = new WebSocket(
    (location.protocol === "https:" ? "wss://" : "ws://") +
    location.host +
    "/ws"
  );

  ws.onmessage = (e) => {
    let d = JSON.parse(e.data);

    // LOGIN SUCCESS
    if(d.type === "login" && d.ok){
      myName = document.getElementById("name").value;

      document.getElementById("login").style.display = "none";
      document.getElementById("app").style.display = "flex";
    }

    // USERS LIST
    if(d.type === "users"){
      renderUsers(d.data);
    }

    // MESSAGE RECEIVE
    if(d.type === "message"){
      addMsg(d.sender, d.text, d.time);
    }
  };
}

// =====================
// LOGIN
// =====================
function login(){
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
function register(){
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
function renderUsers(list){
  const usersDiv = document.getElementById("users");
  const header = document.getElementById("header");

  usersDiv.innerHTML = "";

  list.forEach(u => {

    // ❌ নিজের নাম hide
    if(u === myName) return;

    let div = document.createElement("div");
    div.className = "user";
    div.innerText = u;

    div.onclick = () => {
      target = u;
      header.innerText = "Chat with " + u;

      document.querySelectorAll(".user")
        .forEach(x => x.classList.remove("active"));

      div.classList.add("active");

      // 👉 load chat history
      renderChat(u);
    };

    usersDiv.appendChild(div);
  });
}

// =====================
// SEND MESSAGE
// =====================
function send(){
  if(!target){
    alert("Select a user first");
    return;
  }

  const msgInput = document.getElementById("msg");
  const text = msgInput.value.trim();

  if(text === "") return;

  const time = getTime();

  // save locally first
  storeMsg(target, myName, text, time);

  // show instantly
  renderChat(target);

  ws.send(JSON.stringify({
    type: "dm",
    to: target,
    msg: text
  }));

  msgInput.value = "";
}

// =====================
// STORE MESSAGE (CORE FIX)
// =====================
function storeMsg(user, sender, text, time){

  if(!chats[user]){
    chats[user] = [];
  }

  chats[user].push({sender, text, time});
}

// =====================
// ADD MESSAGE (from server)
// =====================
function addMsg(sender, text, time){

  let key = (sender === myName) ? target : sender;

  if(!key) return;

  storeMsg(key, sender, text, time);

  if(key === target){
    renderChat(target);
  }
}

// =====================
// RENDER CHAT (IMPORTANT)
// =====================
function renderChat(user){

  const box = document.getElementById("messages");
  box.innerHTML = "";

  if(!chats[user]) return;

  chats[user].forEach(m => {

    let div = document.createElement("div");

    div.className = "msg " + (m.sender === myName ? "me" : "other");

    div.innerHTML = `
      <div class="text">${m.text}</div>
      <div class="time">${m.sender} • ${m.time}</div>
    `;

    box.appendChild(div);
  });

  box.scrollTop = box.scrollHeight;
}

// =====================
// TIME FORMAT
// =====================
function getTime(){
  let d = new Date();
  return d.getHours() + ":" + String(d.getMinutes()).padStart(2, "0");
                                         }  const text = msgInput.value.trim();

  if(text === "") return;

  const time = getTime();

  // show own message instantly
  addMsg(myName, text, time);

  ws.send(JSON.stringify({
    type: "dm",
    to: target,
    msg: text
  }));

  msgInput.value = "";
}

// =====================
// ADD MESSAGE UI
// =====================
function addMsg(sender, text, time){
  const box = document.getElementById("messages");

  let div = document.createElement("div");

  div.className = "msg " + (sender === myName ? "me" : "other");

  div.innerHTML = `
    <div class="text">${text}</div>
    <div class="time">${sender} • ${time}</div>
  `;

  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

// =====================
// TIME FORMAT
// =====================
function getTime(){
  let d = new Date();
  return d.getHours() + ":" + String(d.getMinutes()).padStart(2, "0");
    }
