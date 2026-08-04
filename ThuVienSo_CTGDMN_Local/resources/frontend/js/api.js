// ─── API BASE + helper gọi backend (tách từ main.js, GĐ1) ──────────────────
// File này PHẢI nạp trước main.js (xem index.html) — không dùng ES module,
// các hàm/biến ở đây vẫn là global giống trước khi tách, chỉ đổi vị trí file.

// Desktop/Electron app và local dev nạp backend trên 127.0.0.1:8000.
// Bản web đã deploy thì frontend + backend chung 1 origin nên dùng đường dẫn
// tương đối (không cần cấu hình CORS phức tạp).
var API_BASE = (location.hostname==='127.0.0.1' || location.hostname==='localhost' || location.protocol==='file:') ? 'http://127.0.0.1:8000' : '';

function getAuthToken(){
  try { return localStorage.getItem('gdmn_auth_token') || ''; } catch(e){ return ''; }
}
function setAuthToken(token){
  try { localStorage.setItem('gdmn_auth_token', token); } catch(e){}
}
function clearAuthToken(){
  try { localStorage.removeItem('gdmn_auth_token'); } catch(e){}
}
function authHeaders(){
  var token = getAuthToken();
  return token ? {'Authorization':'Bearer '+token} : {};
}

function apiGet(path){
  return fetch(API_BASE+path,{headers:authHeaders()}).then(function(r){
    return r.json().catch(function(){return {};}).then(function(d){
      if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
      return d;
    });
  });
}
function apiPost(path,body){
  return fetch(API_BASE+path,{method:'POST',headers:Object.assign({'Content-Type':'application/json'},authHeaders()),body:JSON.stringify(body)}).then(function(r){
    return r.json().catch(function(){return {};}).then(function(d){
      if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
      return d;
    });
  });
}
function apiDelete(path){
  return fetch(API_BASE+path,{method:'DELETE',headers:authHeaders()}).then(function(r){
    return r.json().catch(function(){return {};}).then(function(d){
      if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
      return d;
    });
  });
}
