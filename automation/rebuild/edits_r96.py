# -*- coding: utf-8 -*-
# r96: 업체명 입력 후 엔터 → 내용 칸으로 이동. (재작성본 v2)

R96_EDITS = [
("""_pmVendors=[], _pmVendEditFor=null, _pmDraftId=null;""",
 """_pmVendors=[], _pmVendEditFor=null, _pmDraftId=null, _pmKeepDraft=false;"""),

("""    if(_pmDraftId && _pmVendEditFor!==_pmDraftId){""",
 """    if(_pmDraftId && !_pmKeepDraft && _pmVendEditFor!==_pmDraftId){"""),

("""  window.pmVendInlineKey = function(ev, inp){
    if(ev.key==='Enter'){
      ev.preventDefault();
      var s=_pmVendSugFirstFor(inp); if(s) inp.value=s;
      inp.blur();
    } else if(ev.key==='Escape'){ inp.dataset.esc='1'; inp.blur(); }
  };
  window.pmVendInlineBlur = function(inp){
    setTimeout(_pmVendSugHide,140);
    if(inp.dataset.esc==='1'){ delete inp.dataset.esc; _pmRender(true); return; }
    var m=projMemos.find(function(x){ return x.id===inp.dataset.mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    var vi=Number(inp.dataset.vi);
    var v=String(inp.value||'').trim();
    if(!Array.isArray(m.vendors)) m.vendors=[];
    if(v===''){ m.vendors.splice(vi,1); }
    else if(m.vendors[vi]!==v){
      if(m.vendors.indexOf(v)>=0){ _pmRender(true); return; }   // 중복이면 원복
      m.vendors[vi]=v;
    } else { return; }   // 변경 없음
    _pmSave(); _pmRender(true);
  };""",
 """  window.pmVendInlineKey = function(ev, inp){
    if(ev.key==='Enter'){
      ev.preventDefault();
      var s=_pmVendSugFirstFor(inp); if(s) inp.value=s;
      inp.dataset.goc='1';   // 엔터 → 내용 칸으로 이동
      inp.blur();
    } else if(ev.key==='Escape'){ inp.dataset.esc='1'; inp.blur(); }
  };
  function _pmGoContent(mid){
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    var its=m.items||[];
    if(its.length){
      var sp=document.querySelector('#projMemoBoard span[data-mid="'+mid+'"][data-iid="'+its[its.length-1].id+'"]');
      if(sp){ pmInlineStart(sp); return; }
    }
    pmInlineAddStart(mid);   // 내용이 없으면 첫 내용 입력줄
  }
  window.pmVendInlineBlur = function(inp){
    setTimeout(_pmVendSugHide,140);
    var goc=inp.dataset.goc==='1'; delete inp.dataset.goc;
    var mid=inp.dataset.mid;
    function fin(changed){
      if(goc){
        _pmVendEditFor=null; _pmKeepDraft=true;
        _pmRender(true);
        setTimeout(function(){ _pmGoContent(mid); _pmKeepDraft=false; },30);
      } else if(changed){ _pmRender(true); }
    }
    if(inp.dataset.esc==='1'){ delete inp.dataset.esc; _pmRender(true); return; }
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m){ return; }
    if(!(myMemberId && m.memberId===myMemberId)){ return; }
    var vi=Number(inp.dataset.vi);
    var v=String(inp.value||'').trim();
    if(!Array.isArray(m.vendors)) m.vendors=[];
    if(v===''){ m.vendors.splice(vi,1); }
    else if(m.vendors[vi]!==v){
      if(m.vendors.indexOf(v)>=0){ fin(true); return; }   // 중복이면 원복
      m.vendors[vi]=v;
    } else { fin(false); return; }   // 변경 없음
    _pmSave(); fin(true);
  };"""),

("""    inp.onkeydown=function(ev){
      if(ev.key==='Enter'){ ev.preventDefault(); var s=_pmVendSugFirstFor(inp); if(s) inp.value=s; inp.dataset.again='1'; inp.blur(); }
      else if(ev.key==='Escape'){ inp.dataset.esc='1'; inp.blur(); }
    };""",
 """    inp.onkeydown=function(ev){
      if(ev.key==='Enter'){ ev.preventDefault(); var s=_pmVendSugFirstFor(inp); if(s) inp.value=s; inp.dataset.goc='1'; inp.blur(); }
      else if(ev.key==='Escape'){ inp.dataset.esc='1'; inp.blur(); }
    };"""),
("""  window.pmVendAddCommit = function(inp){
    setTimeout(_pmVendSugHide,140);
    var mid=inp.dataset.mid;
    if(inp.dataset.esc==='1'){ _pmRender(true); return; }
    var m=projMemos.find(function(x){ return x.id===mid; });
    var v=String(inp.value||'').trim();
    var saved=false;
    if(m && v && myMemberId && m.memberId===myMemberId){
      if(!Array.isArray(m.vendors)) m.vendors=[];
      if(m.vendors.indexOf(v)<0){ m.vendors.push(v); _pmSave(); saved=true; }
    }
    var again=saved && inp.dataset.again==='1';
    _pmRender(true);
    if(again) setTimeout(function(){ pmVendAddStart(mid); },30);
  };""",
 """  window.pmVendAddCommit = function(inp){
    setTimeout(_pmVendSugHide,140);
    var mid=inp.dataset.mid;
    var goc=inp.dataset.goc==='1';
    if(inp.dataset.esc==='1'){ _pmRender(true); return; }
    var m=projMemos.find(function(x){ return x.id===mid; });
    var v=String(inp.value||'').trim();
    if(m && v && myMemberId && m.memberId===myMemberId){
      if(!Array.isArray(m.vendors)) m.vendors=[];
      if(m.vendors.indexOf(v)<0){ m.vendors.push(v); _pmSave(); }
    }
    if(goc){
      _pmVendEditFor=null; _pmKeepDraft=true;
      _pmRender(true);
      setTimeout(function(){ _pmGoContent(mid); _pmKeepDraft=false; },30);
      return;
    }
    _pmRender(true);
  };"""),
]

def apply_r96(s, path):
    for i,(old,new) in enumerate(R96_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R96 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r96(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r95 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r95 2026-08-19 -->', '<!-- test build r96 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
