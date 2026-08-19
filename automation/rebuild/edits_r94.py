# -*- coding: utf-8 -*-
# r94: 거래처명도 내용 줄과 동일한 인라인 수정 방식으로. (재작성본 v2)

R94_EDITS = [
("""  var _pmForm=false, _pmEditId=null, _pmShowHidden=false, _pmShowAll=false, _pmVendors=[];""",
 """  var _pmForm=false, _pmEditId=null, _pmShowHidden=false, _pmShowAll=false, _pmVendors=[], _pmVendEditFor=null;"""),

("""  function _pmRender(force){""",
 """  function _pmVendSugBox(){
    var b=document.getElementById('pmVendSugF');
    if(!b){
      b=document.createElement('div'); b.id='pmVendSugF';
      b.style.cssText='display:none;position:fixed;z-index:100050;background:#fff;border:1px solid #c8d2de;max-height:180px;overflow:auto;box-shadow:0 8px 22px rgba(15,23,42,.18);min-width:180px';
      document.body.appendChild(b);
    }
    return b;
  }
  function _pmVendSugHide(){ var b=document.getElementById('pmVendSugF'); if(b) b.style.display='none'; }
  function _pmVendSugFirstFor(inp){
    var b=document.getElementById('pmVendSugF');
    if(b && b.style.display==='block' && b._target===inp){ var f=b.querySelector('div[data-nm]'); if(f) return f.dataset.nm; }
    return null;
  }
  window.pmVendInlineSearch = function(inp){
    var b=_pmVendSugBox();
    var q=String(inp.value||'').trim().toLowerCase();
    if(!q){ b.style.display='none'; return; }
    try{ ensureClientList(); }catch(_e){}
    var m=projMemos.find(function(x){ return x.id===inp.dataset.mid; });
    var cur=(m&&m.vendors)||[];
    var hit=allClients().filter(function(c){ return String(c[0]).toLowerCase().indexOf(q)>=0 && cur.indexOf(c[0])<0; }).slice(0,20);
    if(!hit.length){ b.style.display='none'; return; }
    b.innerHTML=hit.map(function(c){ return '<div onmousedown="pmVendSugPick(this)" data-nm="'+esc(c[0])+'" style="padding:6px 10px;cursor:pointer;font-size:12px;color:#374151;border-bottom:1px solid #f1f5f9" onmouseover="this.style.background=\\'#f4f8fe\\'" onmouseout="this.style.background=\\'\\'">'+esc(c[0])+'</div>'; }).join('');
    var r=inp.getBoundingClientRect();
    b.style.left=r.left+'px'; b.style.top=(r.bottom+2)+'px'; b.style.minWidth=Math.max(180, r.width)+'px';
    b.style.display='block';
    b._target=inp;
  };
  window.pmVendSugPick = function(el){
    var b=_pmVendSugBox(); var inp=b._target;
    if(inp) inp.value=el.dataset.nm;
    b.style.display='none';
  };
  window.pmVendEditStartInline = function(mid){
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    _pmVendEditFor=mid;
    _pmRender(true);
    setTimeout(function(){
      var i=document.querySelector('#projMemoBoard .pm-vend-in[data-mid="'+mid+'"]');
      if(i){ try{ i.focus(); var _L=i.value.length; i.setSelectionRange(_L,_L); }catch(_e){} }
      else { pmVendAddStart(mid); }
    },40);
  };
  window.pmVendEditEnd = function(){ _pmVendEditFor=null; _pmVendSugHide(); _pmRender(true); };
  window.pmVendInlineDel = function(mid, vi){
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    (m.vendors||[]).splice(Number(vi),1);
    _pmSave(); _pmRender(true);
  };
  window.pmVendInlineKey = function(ev, inp){
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
  };
  window.pmVendAddStart = function(mid){
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    var btn=document.querySelector('#projMemoBoard button[data-pmvadd="'+mid+'"]'); if(!btn) return;
    var row=document.createElement('div');
    row.style.cssText='display:flex;align-items:center;gap:3px;border-bottom:1px solid rgba(182,169,79,.35)';
    var inp=document.createElement('input');
    inp.type='text'; inp.placeholder='업체명 검색/입력';
    inp.style.cssText='flex:1;min-width:0;border:none;background:transparent;font-size:12px;font-weight:700;color:#14305c;font-family:inherit;outline:none;padding:2px;height:22px;box-sizing:border-box';
    inp.dataset.mid=mid;
    inp.oninput=function(){ pmVendInlineSearch(inp); };
    inp.onkeydown=function(ev){
      if(ev.key==='Enter'){ ev.preventDefault(); var s=_pmVendSugFirstFor(inp); if(s) inp.value=s; inp.dataset.again='1'; inp.blur(); }
      else if(ev.key==='Escape'){ inp.dataset.esc='1'; inp.blur(); }
    };
    inp.onblur=function(){ pmVendAddCommit(inp); };
    row.appendChild(inp);
    btn.parentNode.parentNode.insertBefore(row, btn.parentNode);
    try{ inp.focus(); }catch(_e){}
  };
  window.pmVendAddCommit = function(inp){
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
  };
  function _pmRender(force){"""),

("""        + '<div style="display:flex;align-items:center;gap:5px;margin-bottom:5px;flex-shrink:0">'
        +   '<span '+(mine?('data-id="'+m.id+'" onclick="pmEditStart(this.dataset.id, true)" '):'')+'title="'+esc((m.vendors||[]).join(', '))+(mine?' (클릭하여 수정)':'')+'" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;'+(mine?'cursor:pointer;':'')+'">'+((m.vendors&&m.vendors.length)?esc(m.vendors.join(' · ')):'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'
        +   (m.hidden?'<span style="flex-shrink:0;font-size:10px;font-weight:700;color:#9ca3af;border:1px solid #d1d5db;padding:1px 5px">숨김</span>':'')
        + '</div>'""",
 """        + (function(){
            var _badge=(m.hidden?'<span style="flex-shrink:0;font-size:10px;font-weight:700;color:#9ca3af;border:1px solid #d1d5db;padding:1px 5px">숨김</span>':'');
            if(mine && _pmVendEditFor===m.id){
              var vRows=(m.vendors||[]).map(function(v,vi){
                return '<div style="display:flex;align-items:center;gap:3px;border-bottom:1px solid rgba(182,169,79,.35)">'
                  + '<input type="text" class="pm-vend-in" value="'+esc(v)+'" data-mid="'+m.id+'" data-vi="'+vi+'" oninput="pmVendInlineSearch(this)" onkeydown="pmVendInlineKey(event,this)" onblur="pmVendInlineBlur(this)" style="flex:1;min-width:0;border:none;background:transparent;font-size:12px;font-weight:700;color:#14305c;font-family:inherit;outline:none;padding:2px;height:22px;box-sizing:border-box">'
                  + '<span data-mid="'+m.id+'" data-vi="'+vi+'" onclick="pmVendInlineDel(this.dataset.mid,this.dataset.vi)" title="업체 제거" style="cursor:pointer;color:#8b97a5;font-weight:700;line-height:1;font-size:11px;padding:0 2px" onmouseover="this.style.color=\\'#dc2626\\'" onmouseout="this.style.color=\\'#8b97a5\\'">&#10005;</span>'
                  + '</div>';
              }).join('');
              return '<div style="display:flex;align-items:flex-start;gap:5px;margin-bottom:5px;flex-shrink:0">'
                + '<div style="flex:1;min-width:0;max-height:112px;overflow:auto">'+vRows
                + '<div style="display:flex;align-items:center;gap:4px;margin-top:2px">'
                +   '<button data-pmvadd="'+m.id+'" onclick="pmVendAddStart(this.dataset.pmvadd)" title="업체 추가" style="border:none;background:none;cursor:pointer;color:#b6a94f;font-size:11px;padding:2px;font-family:inherit" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#b6a94f\\'">&#65291; 업체 추가</button>'
                +   '<span style="flex:1"></span>'
                +   '<button onclick="pmVendEditEnd()" style="'+_PJ_SBTN+';height:18px;font-size:10px;padding:0 5px">완료</button>'
                + '</div></div>'
                + _badge + '</div>';
            }
            return '<div style="display:flex;align-items:center;gap:5px;margin-bottom:5px;flex-shrink:0">'
              + '<span '+(mine?('data-id="'+m.id+'" onclick="pmVendEditStartInline(this.dataset.id)" '):'')+'title="'+esc((m.vendors||[]).join(', '))+(mine?' (클릭하여 수정)':'')+'" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;'+(mine?'cursor:pointer;':'')+'">'+((m.vendors&&m.vendors.length)?esc(m.vendors.join(' · ')):'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'
              + _badge + '</div>';
          })()"""),
]

def apply_r94(s, path):
    for i,(old,new) in enumerate(R94_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R94 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r94(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r93 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r93 2026-08-19 -->', '<!-- test build r94 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
