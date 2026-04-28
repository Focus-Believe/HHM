let ws;
let target=null;
let myName=null;

function connect(){
  ws=new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws");

  ws.onmessage=e=>{
    let d=JSON.parse(e.data);

    if(d.type==="login" && d.ok){
      myName=name.value;
      login.style.display="none";
      app.style.display="flex";
    }

    if(d.type==="users"){
      renderUsers(d.data);
    }

    if(d.type==="msg"){
      addMsg(d.from, d.msg, d.time);
    }
  };
}

function login(){
  connect();
  ws.onopen=()=>{
    ws.send(JSON.stringify({
      type:"login",
      name:name.value,
      password:pass.value
    }));
  };
}

function register(){
  connect();
  ws.onopen=()=>{
    ws.send(JSON.stringify({
      type:"register",
      name:name.value,
      password:pass.value
    }));
  };
}

function renderUsers(list){
  users.innerHTML="";
  list.forEach(u=>{
    let div=document.createElement("div");
    div.className="user";
    div.innerText=u;

    div.onclick=()=>{
      target=u;
      header.innerText=u;

      document.querySelectorAll(".user").forEach(x=>x.classList.remove("active"));
      div.classList.add("active");
    };

    users.appendChild(div);
  });
}

function send(){
  if(!target) return alert("Select user first");

  let text=msg.value;
  let time=getTime();

  addMsg(myName,text,time);

  ws.send(JSON.stringify({
    type:"dm",
    to:target,
    msg:text
  }));

  msg.value="";
}

function addMsg(sender,text,time){
  let box=messages;

  let div=document.createElement("div");
  div.className="msg "+(sender===myName?"me":"other");

  div.innerHTML=`
    <div>${text}</div>
    <div class="time">${time}</div>
  `;

  box.appendChild(div);
  box.scrollTop=box.scrollHeight;
}

function getTime(){
  let d=new Date();
  return d.getHours()+":"+String(d.getMinutes()).padStart(2,"0");
             }
