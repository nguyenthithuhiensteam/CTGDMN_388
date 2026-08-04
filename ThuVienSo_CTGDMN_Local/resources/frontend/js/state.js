// ─── STATE dùng chung toàn app (tách từ main.js, GĐ1) ───────────────────────
// Nạp sau js/api.js, trước main.js. Vẫn là biến/hàm global (không module).

var CURRENT_ACCOUNT = null;
var CHILDREN_LIST = [];
var APP_VERSION = '1.0.1';

function loadChildren(){
  return apiGet('/api/children').then(function(list){ CHILDREN_LIST=list||[]; return CHILDREN_LIST; }).catch(function(){ CHILDREN_LIST=[]; return CHILDREN_LIST; });
}

function childOptionsHtml(selectedId){
  if(!CHILDREN_LIST.length) return '<option value="">Chưa có trẻ nào – vào "Theo dõi trẻ" bấm Thêm trẻ trước</option>';
  return CHILDREN_LIST.map(function(c){
    return '<option value="'+c.id+'"'+(String(c.id)===String(selectedId)?' selected':'')+'>'+escHtml(c.full_name)+(c.class_name?' – '+escHtml(c.class_name):'')+'</option>';
  }).join('');
}
