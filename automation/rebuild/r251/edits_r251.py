# -*- coding: utf-8 -*-
# r251 (사용자 요청 2026-10-27): 견적 메일 받는 사람 — 업체별 주소록에서 골라 보내기
#  - [메일 보내기] 창 받는 사람 아래에 이 업체 주소록 칩(이름·직급·메일). 누르면 받는 사람에 넣기/빼기, ✕ 는 주소록에서 지우기.
#  - 처음 열 때 받는 사람 = 견적 담당자의 메일(있으면) → 없으면 주소록 첫 번째 1개 (r245 는 전부 넣었음).
#  - 새 주소 저장: 받는 사람 칸에 직접 쓰고 [+ 주소록에 저장] (이름 선택 입력) 또는 보낼 때 "보낸 주소를 주소록에 저장" 체크(기본 ✓, r245 동작).
#  - 저장 위치는 업체 상세(clientInfo) 담당자 연락처 — 업체 관리 화면과 같은 자료.
import io, sys, json

JS = r"""
  // ─── r250: 업체별 메일 주소록 ───
  var _ML_RE=/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/;
  function _mlSplit(s){ return String(s||'').split(/[,;\s]+/).map(function(a){ return a.trim(); }).filter(Boolean); }
  function _mailAddrBook(vname){
    var ci=_mailClientInfo(vname); var out=[], seen={};
    var add=function(email, name, tag){ var e=String(email||'').trim(); if(!_ML_RE.test(e)) return; var k=e.toLowerCase(); if(seen[k]) return; seen[k]=1; out.push({ email:e, name:String(name||'').trim(), tag:tag||'' }); };
    (Array.isArray(ci.contacts)?ci.contacts:[]).forEach(function(c){ if(c) add(c.email, c.name, c.rank||c.dept||''); });
    add(ci.email, '', '대표 메일'); add(ci.taxEmail, '', '계산서');
    return out;
  }
  function _mlBookHtml(vname){
    var book=_mailAddrBook(vname); var cur=_mlSplit((document.getElementById('mlTo')||{}).value).map(function(a){ return a.toLowerCase(); });
    var h='<div class="ml-book-h">이 업체 주소록 <span>— 눌러서 받는 사람에 넣기/빼기</span></div><div class="ml-book">';
    if(!book.length) h+='<span class="ml-book-empty">아직 저장된 주소가 없습니다. 받는 사람에 적고 [+ 주소록에 저장] 을 누르면 다음부터 골라 쓸 수 있습니다.</span>';
    book.forEach(function(b, i){ var on=cur.indexOf(b.email.toLowerCase())>=0;
      h+='<span class="ml-chip'+(on?' on':'')+'" onclick="mlBookToggle('+i+')" title="'+esc(b.email)+'">'+(on?'✓ ':'')+(b.name?('<b>'+esc(b.name)+'</b> '):'')+(b.tag?('<i>'+esc(b.tag)+'</i> '):'')+esc(b.email)+'<a onclick="event.stopPropagation(); mlBookDel('+i+')" title="주소록에서 지우기">✕</a></span>'; });
    h+='</div><div class="ml-book-add"><button type="button" class="btn" onclick="mlBookSave()">+ 받는 사람 주소를 주소록에 저장</button><label><input type="checkbox" id="mlRemember" checked> 보낼 때 새 주소 자동 저장</label></div>';
    return h;
  }
  function _mlBookRender(){ var el=document.getElementById('mlBook'); var d=window._mlDraft; if(el&&d) el.innerHTML=_mlBookHtml(d.vname); var rm=window.__mlRemember; var cb=document.getElementById('mlRemember'); if(cb&&rm===false) cb.checked=false; }
  window.mlBookToggle = function(i){
    var d=window._mlDraft; if(!d) return; var b=_mailAddrBook(d.vname)[i]; if(!b) return;
    var inp=document.getElementById('mlTo'); var list=_mlSplit(inp.value); var k=b.email.toLowerCase();
    var idx=list.findIndex(function(a){ return a.toLowerCase()===k; });
    if(idx>=0) list.splice(idx,1); else list.push(b.email);
    inp.value=list.join(', '); _mlKeepRemember(); _mlBookRender();
  };
  function _mlKeepRemember(){ var cb=document.getElementById('mlRemember'); if(cb) window.__mlRemember=cb.checked; }
  window.mlBookSave = function(){
    var d=window._mlDraft; if(!d) return;
    var list=_mlSplit((document.getElementById('mlTo')||{}).value).filter(function(a){ return _ML_RE.test(a); });
    var known=_mailAddrBook(d.vname).map(function(b){ return b.email.toLowerCase(); });
    var fresh=list.filter(function(a){ return known.indexOf(a.toLowerCase())<0; });
    if(!fresh.length){ try{ _mtToast(list.length?'이미 주소록에 있는 주소입니다':'받는 사람에 메일 주소를 먼저 적어 주세요'); }catch(_e){} return; }
    showPromptModal('주소록에 저장', fresh.join(', ')+'\n담당자 이름(선택) — 비워 두면 메일 주소만 저장합니다', d.mgr||'', function(nm){
      var n=_mailRemember(d.vname, String(nm||'').trim(), fresh.join(', '));
      _mlKeepRemember(); _mlBookRender(); try{ _mtToast(n?('주소 '+n+'건 저장 — 다음부터 골라 쓰면 됩니다'):'저장할 새 주소가 없습니다'); }catch(_e){}
    }, '저장');
  };
  window.mlBookDel = function(i){
    var d=window._mlDraft; if(!d) return; var b=_mailAddrBook(d.vname)[i]; if(!b) return;
    if(typeof _isViewer==='function' && _isViewer()) return;
    showConfirmModal('주소록에서 지우기', esc((b.name?b.name+' ':'')+b.email)+' 주소를 이 업체 주소록에서 지울까요?', function(){
      var key=_clxInfoKey(d.vname); var info=clientInfo[key]||clientInfo[d.vname]; if(!info) return; var k=b.email.toLowerCase();
      if(String(info.email||'').toLowerCase()===k) info.email='';
      if(String(info.taxEmail||'').toLowerCase()===k) info.taxEmail='';
      info.contacts=(info.contacts||[]).filter(function(c){
        if(!c || String(c.email||'').toLowerCase()!==k) return true;
        if(c.name||c.phone||c.phone2){ c.email=''; return true; }   // 연락처 정보는 남기고 메일만 지움
        return false; });
      clientInfo[key]=info; _clxPersist();
      var inp=document.getElementById('mlTo'); if(inp) inp.value=_mlSplit(inp.value).filter(function(a){ return a.toLowerCase()!==k; }).join(', ');
      _mlKeepRemember(); _mlBookRender();
    }, '지우기', '#dc2626');
  };
  (function(){ var st=document.createElement('style'); st.textContent='.ml-book-h{font-size:11.5px;font-weight:700;color:#14305c;margin:8px 0 4px} .ml-book-h span{font-weight:400;color:#9ca3af} .ml-book{display:flex;flex-wrap:wrap;gap:6px} .ml-chip{display:inline-flex;align-items:center;gap:4px;font-size:12px;padding:4px 8px;border:1px solid #d6e0ec;border-radius:14px;background:#fff;color:#334155;cursor:pointer;user-select:none} .ml-chip:hover{border-color:#1B3A6B} .ml-chip.on{background:#eaf1fb;border-color:#1B3A6B;color:#1B3A6B} .ml-chip i{font-style:normal;font-size:10.5px;color:#64748b} .ml-chip a{color:#cbd5e1;font-size:11px;margin-left:2px} .ml-chip a:hover{color:#dc2626} .ml-book-empty{font-size:11.5px;color:#9ca3af} .ml-book-add{display:flex;align-items:center;gap:12px;margin-top:6px;font-size:11.5px;color:#6b7280} .ml-book-add .btn{font-size:11.5px;padding:3px 9px} .ml-book-add label{display:flex;align-items:center;gap:4px;cursor:pointer}'; document.head.appendChild(st); })();
"""

OPS = [
  # 받는 사람 칸 + 주소록 자리 (처음 값: 담당자 메일 우선, 없으면 첫 주소 1개)
  ["+'<div><div style=\"'+_MLL+'\">받는 사람 <span style=\"font-weight:400;color:#9ca3af\">— 여러 명은 쉼표</span></div><input id=\"mlTo\" value=\"'+esc(d.to.join(', '))+'\" placeholder=\"고객 메일 주소\" style=\"'+_MLI+'\">'+(d.to.length?'':'<div style=\"font-size:11px;color:#b45309;margin-top:3px\">업체 상세에 담당자 메일이 없어 비워 두었습니다. 직접 입력해 주세요 (업체 관리에 등록해 두면 다음부터 자동).</div>')+'</div>'",
   "+'<div><div style=\"'+_MLL+'\">받는 사람 <span style=\"font-weight:400;color:#9ca3af\">— 여러 명은 쉼표 · 아래 주소록에서 골라도 됩니다</span></div><input id=\"mlTo\" value=\"'+esc(d.to.slice(0,1).join(', '))+'\" placeholder=\"고객 메일 주소\" style=\"'+_MLI+'\"><div id=\"mlBook\"></div></div>'   // r250: 주소록", 1, "TO_UI"],
  ["    window._mlDraft=d;\n    window._mlDraftBody=d.body;",
   "    window._mlDraft=d;\n    window._mlDraftBody=d.body;\n    window.__mlRemember=true; try{ _mlBookRender(); }catch(_e){}   // r250", 1, "OPEN_RENDER"],
  ["var _mgEl=document.getElementById('qManager'); var mgr=(_mgEl&&!_mgEl.disabled&&_mgEl.value)?String(_mgEl.value).trim():'';",
   "var _mgEl=document.getElementById('qManager'); var mgr=(_mgEl&&!_mgEl.disabled&&_mgEl.value)?String(_mgEl.value).trim():((typeof _qMgr!=='undefined'&&_qMgr)?String(_qMgr):'');   // r250: 저장된 견적 담당자도", 1, "DRAFT_MGR"],
  # 보낼 때 자동 저장은 체크박스가 켜져 있을 때만
  ["var _remembered=0; try{ _remembered=_mailRemember(d.vname, d.mgr, to); }catch(_e){}   // r245",
   "var _remembered=0; try{ var _rmcb=document.getElementById('mlRemember'); if(!_rmcb || _rmcb.checked) _remembered=_mailRemember(d.vname, d.mgr, to); }catch(_e){}   // r245 · r250: 체크 시만", 1, "SEND_REMEMBER"],
  ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238",
   JS + "  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
  ["<!-- test build r249 2026-10-27 -->", "<!-- test build r250 2026-10-27 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R250 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r250(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER':
            if not is_test: continue
            if old not in s:   # r249 를 건너뛴 바탕(r247)에도 적용 가능
                old = "<!-- test build r247 2026-10-22 -->"
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r250 브라우저 적용기 — edits_r250.py 의 OPS. r245 이후 바탕(r247/r249) 위에 적용.",
             "function r250Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R250 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; var old=o[0]; if(o[3]==='MARKER'){ if(!isTest) continue; if(s.indexOf(old)<0) old='<!-- test build r247 2026-10-22 -->'; } s = rep(s, old, o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r250Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r250(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r250 applied:', path)
