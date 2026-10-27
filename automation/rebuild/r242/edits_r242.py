# -*- coding: utf-8 -*-
# r242 (사용자 요청 2026-10-20): 일정(메모장) 페이지 1회성 공지 팝업
#  - 유튜브 쇼츠(https://www.youtube.com/shorts/mx2bnXbRZq0)를 팝업 안에서 바로 재생(임베드) + [유튜브에서 열기] 링크
#  - 전 직원 대상, 계정별 1회: [확인(다시 보지 않기)] 를 누르면 Firebase `<_FB_PATH>/sched_notice_seen/<공지id>/<계정id>` 에 시각 기록
#    (상태 전체 PATCH 에 안 들어가는 별도 키라 다른 PC 저장에 덮이지 않음). 로컬 캐시(localStorage) 로 재조회 생략.
#  - 바탕(X)·닫기만 하면 다음에 다시 뜸. 공지 목록은 `_NOTICES` 에 추가하면 됨(id 가 다르면 새로 1회).
import io, sys, json

JS = r"""
  // ─── r242 1회성 공지 팝업 (일정 페이지) ─────────────────────────────
  var _NOTICES = [
    { id:'nt20261020', title:'공지 영상', yt:'mx2bnXbRZq0', url:'https://www.youtube.com/shorts/mx2bnXbRZq0', note:'아래 영상을 확인해 주세요. [확인] 을 누르면 다시 표시되지 않습니다.' }
  ];
  var _ntShown = {};   // 이번 세션에서 띄운/확인한 공지 id
  function _ntLsKey(nid, uid){ return 'sched_notice_seen_'+nid+'_'+uid; }
  function _ntUid(){ return (_authUser && _authUser.id) ? String(_authUser.id) : ''; }
  async function _ntSeen(nid, uid){
    try{ if(localStorage.getItem(_ntLsKey(nid, uid))) return true; }catch(_e){}
    if(!_fbDbUrl) return true;   // 동기화 전이면 띄우지 않는다(다음 기회에)
    try{
      var r = await _fbFetch(_fbDbUrl+'/'+_FB_PATH+'/sched_notice_seen/'+encodeURIComponent(nid)+'/'+encodeURIComponent(uid)+'.json');
      if(!r || !r.ok) return true;
      var v = await r.json();
      if(v){ try{ localStorage.setItem(_ntLsKey(nid, uid), String(v)); }catch(_e){} return true; }
      return false;
    }catch(_e){ return true; }
  }
  async function _ntCheck(){
    var uid=_ntUid(); if(!uid) return;
    if(document.getElementById('ntOverlay')) return;
    for(var i=0;i<_NOTICES.length;i++){
      var n=_NOTICES[i]; if(_ntShown[n.id]) continue;
      if(await _ntSeen(n.id, uid)) continue;
      _ntShown[n.id]=true; _ntOpen(n); return;
    }
  }
  function _ntOpen(n){
    var ov=document.createElement('div'); ov.id='ntOverlay';
    ov.style.cssText='position:fixed;inset:0;z-index:2000100;background:rgba(15,23,42,.55);display:flex;align-items:center;justify-content:center;padding:16px';
    var emb = n.yt ? '<div style="display:flex;justify-content:center;background:#000"><iframe id="ntFrame" src="https://www.youtube.com/embed/'+n.yt+'?rel=0&playsinline=1" title="공지 영상" referrerpolicy="strict-origin-when-cross-origin" style="width:315px;height:560px;max-height:70vh;border:0;display:block" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>' : '';
    ov.innerHTML = '<div style="width:100%;max-width:420px;background:#fff;border:1px solid #c8d2de;overflow:hidden">'
      + '<div style="padding:9px 14px;border-bottom:1px solid #c8d2de;background:#f4f6f9;display:flex;align-items:center;gap:8px"><span style="width:3px;height:15px;background:#1a1a1a"></span><span style="font-size:13.5px;font-weight:700;color:#1a1a1a;flex:1">'+esc(n.title||'공지')+'</span><button type="button" id="ntClose" style="border:0;background:none;font-size:18px;line-height:1;cursor:pointer;color:#64748b" title="닫기(다음에 다시 표시)">×</button></div>'
      + (n.note ? '<div style="padding:10px 14px;font-size:12.5px;color:#334155;line-height:1.5">'+esc(n.note)+'</div>' : '')
      + emb
      + '<div style="padding:10px 14px;display:flex;align-items:center;gap:8px;border-top:1px solid #e2e8f0">'
      + (n.url ? '<a href="'+esc(n.url)+'" target="_blank" rel="noopener" style="font-size:12px;color:#2563eb">유튜브에서 열기 ↗</a>' : '')
      + '<span style="flex:1"></span>'
      + '<button type="button" id="ntOk" class="btn-primary" style="padding:7px 14px;font-size:12.5px;cursor:pointer">확인 (다시 보지 않기)</button>'
      + '</div></div>';
    document.body.appendChild(ov);
    document.getElementById('ntClose').onclick=function(){ ov.remove(); };
    document.getElementById('ntOk').onclick=function(){ _ntConfirm(n.id); ov.remove(); };
  }
  async function _ntConfirm(nid){
    var uid=_ntUid(); if(!uid) return;
    var ts=Date.now();
    try{ localStorage.setItem(_ntLsKey(nid, uid), String(ts)); }catch(_e){}
    if(!_fbDbUrl) return;
    try{ await _fbPutOk(_fbDbUrl+'/'+_FB_PATH+'/sched_notice_seen/'+encodeURIComponent(nid)+'/'+encodeURIComponent(uid)+'.json', ts, '공지 확인 기록'); }
    catch(e){ try{ localStorage.removeItem(_ntLsKey(nid, uid)); }catch(_e){} }
  }
  window._ntCheck=_ntCheck; window._ntConfirm=_ntConfirm;
"""

OPS = [
  ["  window.smcSkip = function(id){",
   JS + "  window.smcSkip = function(id){", 1, "NT_JS"],
  ["renderMemoPage(true); setTimeout(function(){ try{ var _mi=document.getElementById('mmInput');",
   "renderMemoPage(true); try{ setTimeout(function(){ _ntCheck(); }, 300); }catch(_e){}   /* r242 공지 팝업 */ setTimeout(function(){ try{ var _mi=document.getElementById('mmInput');", 1, "NT_MEMO"],
  ["    _linkMyProfile();\n    // 로그인 확정 후 권한 의존 UI(연차 관리 등) 갱신",
   "    _linkMyProfile();\n    try{ setTimeout(function(){ try{ if(document.getElementById('pageMemo') && document.getElementById('pageMemo').classList.contains('active')) _ntCheck(); }catch(_e){} }, 1200); }catch(_e){}   // r242: 로그인 직후 일정 페이지면 공지 확인\n    // 로그인 확정 후 권한 의존 UI(연차 관리 등) 갱신", 1, "NT_AUTH"],
  ["<!-- test build r241 2026-10-19 -->", "<!-- test build r242 2026-10-20 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R242 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r242(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r242 브라우저 적용기 — edits_r242.py 의 OPS. r241 적용본 위에 적용.",
             "function r242Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R242 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r242Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r242(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r242 applied:', path)
