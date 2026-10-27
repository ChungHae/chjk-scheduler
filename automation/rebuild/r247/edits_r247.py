# -*- coding: utf-8 -*-
# r247 (사용자 요청 2026-10-22): 일정 옆 최상위 메뉴 "내규" — 사내 내규 페이지. 관리자가 항목별로 직접 작성(제목+본문), 직원은 열람.
#  - 자료: Firebase <_AUTH_BASE>/sched_rules.json = { secs:[{id,title,body,upd,by}], upd } (상태 전체 PATCH 와 분리된 별도 키 — 다른 저장에 덮이지 않음)
#  - 본문 표기: 빈 줄 = 문단, '## ' = 소제목, '- ' 또는 '· ' = 글머리. 수정일·수정자 표시.
#  - 처음 비어 있으면 관리자에게 기본 항목(근무·휴가 / 법인카드 / 견적·영업 자료 / 회의·2주 목표) 한 번에 만들기 제안 — 문구는 격려·안내 톤(PRINCIPLES.md).
import io, sys, json

HTML = r"""
  <div id="pageRules" class="page-section">
    <div class="q-toolbar inv-toolbar">
      <span class="inv-flat-label">사내 내규</span>
      <span id="rlMeta" style="font-size:11.5px;color:#9ca3af"></span>
      <span style="flex:1"></span>
      <button class="btn" id="rlAddBtn" onclick="rlAdd()" style="display:none;padding:4px 12px;font-size:12.5px">항목 추가</button>
    </div>
    <div class="rl-wrap" id="rlBody"><div style="padding:30px;text-align:center;color:#bbb">불러오는 중…</div></div>
  </div>
"""

CSS = r"""
    .rl-wrap { padding:14px 18px 40px; max-width:960px; }
    .rl-toc { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px; }
    .rl-toc a { font-size:12px; color:#1B3A6B; background:#eaf1fb; padding:3px 10px; border-radius:12px; cursor:pointer; text-decoration:none; }
    .rl-sec { border:1px solid #e5e7eb; background:#fff; padding:14px 18px; margin-bottom:12px; }
    .rl-sec h2 { margin:0 0 8px; font-size:15px; color:#1B3A6B; display:flex; align-items:center; gap:8px; }
    .rl-sec h2 .rl-tools { margin-left:auto; display:flex; gap:4px; }
    .rl-sec h2 .rl-tools button { font-size:11.5px; padding:2px 8px; }
    .rl-sec h3 { margin:10px 0 4px; font-size:13px; color:#334155; }
    .rl-sec p { margin:0 0 8px; font-size:13px; line-height:1.7; color:#1f2937; white-space:pre-wrap; }
    .rl-sec ul { margin:0 0 8px 18px; padding:0; font-size:13px; line-height:1.7; color:#1f2937; }
    .rl-sec .rl-foot { font-size:11px; color:#9ca3af; margin-top:6px; }
    .rl-sec input.rl-title { width:100%; box-sizing:border-box; font-size:14px; font-weight:700; padding:6px 8px; border:1px solid #c8d2de; font-family:inherit; margin-bottom:6px; }
    .rl-sec textarea.rl-body { width:100%; box-sizing:border-box; min-height:160px; font-size:13px; line-height:1.6; padding:8px; border:1px solid #c8d2de; font-family:inherit; resize:vertical; }
    .rl-empty { padding:40px 20px; text-align:center; color:#6b7280; font-size:13px; line-height:1.8; }
    .rl-hint { font-size:11.5px; color:#9ca3af; margin:4px 0 8px; }
"""

JS = r"""
  // ─── r247: 사내 내규 ───
  var _rlDoc=null, _rlEdit=null, _rlLoading=null;
  var _RL_SEED=[
    { title:'1. 근무·휴가', body:'## 근무\n- 근무 시간과 휴게 시간, 외근·출장 보고 방법을 적어 주세요.\n\n## 휴가\n- 연차는 일정 › 개인 일정에서 신청합니다. 미리 적어 두면 팀이 일정을 맞추기 쉽습니다.' },
    { title:'2. 법인카드', body:'- 점심 식사는 그대로 사용하시면 됩니다(용도 "식대").\n- 그 밖의 사용(접대·물품·출장 등)은 **미리 한 줄 신청**해 두면 정산이 빨라집니다 — 일정 › 내 카드 사용 › 사용 신청.\n- 사용 뒤에는 카드사용 화면에서 용도만 골라 주세요. 모르는 가맹점은 한 번 고르면 다음부터 자동입니다.' },
    { title:'3. 견적·영업 자료', body:'- 견적은 사내전산 견적 화면에서 작성·저장하고, PDF·메일 보내기를 쓰면 자동 저장됩니다.\n- 가격표에 없는 SMC 품번은 "SMC 확인" 대기열에 올라가고, 확인되면 가격표에 반영됩니다.\n- 제안서는 일정 › [영업 자료]에서 내 이름·전화로 바로 받아 쓰세요.' },
    { title:'4. 회의·2주 목표', body:'- 업무회의는 2주마다. 회의에서 각자 다음 2주의 미팅 수·제안서 수를 정합니다.\n- 일정에 미팅을 적고 완료하면, 제안서를 보내면 그대로 결과가 됩니다 — 따로 숫자를 올릴 필요가 없습니다.\n- 목표는 짧게, 결과는 다음 회의에서 같이 봅니다. 잘 된 건 같이 축하합니다.' }
  ];
  function _rlUrl(){ return _fbDbUrl+'/'+_AUTH_BASE+'/sched_rules.json'; }
  async function _rlLoad(force){
    if(_rlDoc && !force) return _rlDoc;
    if(_rlLoading && !force) return _rlLoading;
    _rlLoading=(async function(){
      var d=null;
      try{ if(_fbDbUrl){ var r=await _fbFetch(_rlUrl()); if(r&&r.ok) d=await r.json(); } }catch(_e){}
      _rlDoc=(d&&typeof d==='object')?d:{ secs:[], upd:0 };
      if(!Array.isArray(_rlDoc.secs)) _rlDoc.secs=Object.keys(_rlDoc.secs||{}).map(function(k){ return _rlDoc.secs[k]; });
      _rlLoading=null; return _rlDoc;
    })();
    return _rlLoading;
  }
  async function _rlSave(){
    if(!_isAdmin()) throw new Error('관리자만 수정할 수 있습니다.');
    if(!_fbDbUrl) throw new Error('팀 동기화 연결이 필요합니다.');
    _rlDoc.upd=Date.now();
    await _fbPutOk(_rlUrl(), _rlDoc, '내규 저장');
  }
  function _rlFmtDate(ts){ if(!ts) return ''; var d=new Date(ts); return d.getFullYear()+'.'+String(d.getMonth()+1).padStart(2,'0')+'.'+String(d.getDate()).padStart(2,'0'); }
  function _rlBodyHtml(body){   // 빈 줄=문단 · '## '=소제목 · '- '/'· '=글머리 · **굵게**
    var inl=function(t){ return esc(t).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>'); };
    var out='', para=[], list=[];
    var flushP=function(){ if(para.length){ out+='<p>'+para.map(inl).join('\n')+'</p>'; para=[]; } };
    var flushL=function(){ if(list.length){ out+='<ul>'+list.map(function(x){ return '<li>'+inl(x)+'</li>'; }).join('')+'</ul>'; list=[]; } };
    String(body||'').split('\n').forEach(function(ln){
      var t=ln.replace(/\s+$/,'');
      if(!t.trim()){ flushP(); flushL(); return; }
      if(/^##\s+/.test(t)){ flushP(); flushL(); out+='<h3>'+inl(t.replace(/^##\s+/,''))+'</h3>'; return; }
      if(/^(-|·|•)\s+/.test(t)){ flushP(); list.push(t.replace(/^(-|·|•)\s+/,'')); return; }
      flushL(); para.push(t);
    });
    flushP(); flushL();
    return out;
  }
  window.renderRulesPage = async function(){
    var host=document.getElementById('rlBody'); if(!host) return;
    var adm=_isAdmin();
    var ab=document.getElementById('rlAddBtn'); if(ab) ab.style.display=adm?'':'none';
    await _rlLoad();
    var secs=_rlDoc.secs||[];
    var meta=document.getElementById('rlMeta'); if(meta) meta.textContent=secs.length?('항목 '+secs.length+' · 최근 수정 '+_rlFmtDate(_rlDoc.upd)):'';
    if(!secs.length && !_rlEdit){
      host.innerHTML='<div class="rl-empty">아직 적힌 내규가 없습니다.'+(adm?'<br><br><button class="btn btn-primary" onclick="rlSeed()" style="padding:7px 16px">기본 항목 4개로 시작하기</button> &nbsp; <button class="btn" onclick="rlAdd()" style="padding:7px 16px">빈 항목 추가</button><div class="rl-hint" style="margin-top:10px">근무·휴가 / 법인카드 / 견적·영업 자료 / 회의·2주 목표 — 만든 뒤 자유롭게 고치세요.</div>':'<br>관리자가 작성하면 여기에 보입니다.')+'</div>';
      return;
    }
    var h='';
    if(secs.length>1) h+='<div class="rl-toc">'+secs.map(function(s){ return '<a onclick="document.getElementById(\'rl_'+s.id+'\').scrollIntoView({behavior:\'smooth\',block:\'start\'})">'+esc(s.title||'(제목 없음)')+'</a>'; }).join('')+'</div>';
    secs.forEach(function(s, i){
      var editing=(_rlEdit===s.id);
      h+='<div class="rl-sec" id="rl_'+s.id+'">';
      if(editing){
        h+='<input class="rl-title" id="rlT_'+s.id+'" value="'+esc(s.title||'')+'" placeholder="항목 제목">'
          +'<div class="rl-hint">빈 줄 = 문단 · "## 소제목" · "- 글머리" · **굵게**</div>'
          +'<textarea class="rl-body" id="rlB_'+s.id+'" placeholder="내용">'+esc(s.body||'')+'</textarea>'
          +'<div style="display:flex;gap:6px;justify-content:flex-end;margin-top:8px"><button class="btn" onclick="rlCancel()">취소</button><button class="btn btn-primary" onclick="rlSaveSec(\''+s.id+'\')">저장</button></div>';
      } else {
        h+='<h2>'+esc(s.title||'(제목 없음)')+(adm?'<span class="rl-tools"><button class="btn" onclick="rlMove(\''+s.id+'\',-1)" title="위로"'+(i===0?' disabled':'')+'>↑</button><button class="btn" onclick="rlMove(\''+s.id+'\',1)" title="아래로"'+(i===secs.length-1?' disabled':'')+'>↓</button><button class="btn" onclick="rlEditSec(\''+s.id+'\')">수정</button><button class="btn" onclick="rlDel(\''+s.id+'\')" style="color:#dc2626">삭제</button></span>':'')+'</h2>'
          +_rlBodyHtml(s.body)
          +'<div class="rl-foot">'+(s.upd?('수정 '+_rlFmtDate(s.upd)+(s.by?' · '+esc(s.by):'')):'')+'</div>';
      }
      h+='</div>';
    });
    host.innerHTML=h;
    if(_rlEdit){ var ta=document.getElementById('rlB_'+_rlEdit); if(ta) ta.focus(); }
  };
  function _rlId(){ return 'rs'+Date.now().toString(36)+Math.random().toString(36).slice(2,5); }
  window.rlAdd = async function(){ if(!_isAdmin()) return; await _rlLoad(); var s={ id:_rlId(), title:'', body:'', upd:0, by:'' }; _rlDoc.secs.push(s); _rlEdit=s.id; renderRulesPage(); };
  window.rlSeed = async function(){ if(!_isAdmin()) return; await _rlLoad(); var who=(_authUser&&_authUser.name)||'';
    _RL_SEED.forEach(function(t){ _rlDoc.secs.push({ id:_rlId(), title:t.title, body:t.body, upd:Date.now(), by:who }); });
    try{ await _rlSave(); }catch(e){ showInfoModal('내규', e.message||String(e)); } renderRulesPage(); };
  window.rlEditSec = function(id){ if(!_isAdmin()) return; _rlEdit=id; renderRulesPage(); };
  window.rlCancel = function(){ var s=(_rlDoc&&_rlDoc.secs||[]).find(function(x){ return x.id===_rlEdit; }); if(s && !s.title && !s.body && !s.upd) _rlDoc.secs=_rlDoc.secs.filter(function(x){ return x.id!==_rlEdit; }); _rlEdit=null; renderRulesPage(); };
  window.rlSaveSec = async function(id){
    if(!_isAdmin()) return; var s=(_rlDoc.secs||[]).find(function(x){ return x.id===id; }); if(!s) return;
    var t=document.getElementById('rlT_'+id), b=document.getElementById('rlB_'+id);
    s.title=(t&&t.value||'').trim(); s.body=(b&&b.value||'').replace(/\r\n/g,'\n'); s.upd=Date.now(); s.by=(_authUser&&_authUser.name)||'';
    if(!s.title && !s.body.trim()){ showInfoModal('내규','제목이나 내용을 적어 주세요.'); return; }
    try{ await _rlSave(); _rlEdit=null; renderRulesPage(); }catch(e){ showInfoModal('내규 저장 실패', e.message||String(e)); }
  };
  window.rlDel = function(id){
    if(!_isAdmin()) return; var s=(_rlDoc.secs||[]).find(function(x){ return x.id===id; }); if(!s) return;
    showConfirmModal('내규 항목 삭제', '"'+esc(s.title||'(제목 없음)')+'" 항목을 지울까요?', async function(){
      _rlDoc.secs=_rlDoc.secs.filter(function(x){ return x.id!==id; });
      try{ await _rlSave(); }catch(e){ showInfoModal('내규 저장 실패', e.message||String(e)); } renderRulesPage();
    }, '삭제', '#dc2626');
  };
  window.rlMove = async function(id, dir){
    if(!_isAdmin()) return; var a=_rlDoc.secs||[]; var i=a.findIndex(function(x){ return x.id===id; }); var j=i+dir; if(i<0||j<0||j>=a.length) return;
    var t=a[i]; a[i]=a[j]; a[j]=t;
    try{ await _rlSave(); }catch(e){ showInfoModal('내규 저장 실패', e.message||String(e)); } renderRulesPage();
  };
"""

OPS = [
  ['  <button class="page-tab active" id="tabSchedule">일정</button>',
   '  <button class="page-tab active" id="tabSchedule">일정</button>\n  <button class="page-tab" data-page="rules">내규</button><!-- r247 -->', 1, "TAB"],
  ['  <div id="pageLinks" class="page-section">', HTML + '  <div id="pageLinks" class="page-section">', 1, "SECTION"],
  ["links:'pageLinks', cardsales:'pageCardSales' };", "links:'pageLinks', cardsales:'pageCardSales', rules:'pageRules' };   // r247", 1, "PAGEMAP"],
  ["    if (page === 'done') { renderDonePage(); }   // r184",
   "    if (page === 'done') { renderDonePage(); }   // r184\n    if (page === 'rules') { try{ renderRulesPage(); }catch(_e){} }   // r247", 1, "SWITCH"],
  ["    .btn-primary { background: #334155; color: white; border-color: #334155; }",
   "    .btn-primary { background: #334155; color: white; border-color: #334155; }" + CSS, 1, "CSS"],
  ["  // ─── r242 1회성 공지 팝업 (일정 페이지) ─────────────────────────────",
   JS + "  // ─── r242 1회성 공지 팝업 (일정 페이지) ─────────────────────────────", 1, "JS"],
  ["<!-- test build r246 2026-10-22 -->", "<!-- test build r247 2026-10-22 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R247 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r247(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r247 브라우저 적용기 — edits_r247.py 의 OPS. r246 적용본 위에 적용.",
             "function r247Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R247 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r247Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r247(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r247 applied:', path)
