# -*- coding: utf-8 -*-
# r92: 메모 인라인 수정. (재작성본 v2)

R92_EDITS = [
("""  window.pmEditStart = function(id){""",
 """  window.pmEditStart = function(id, focusVendor){"""),
("""    setTimeout(function(){ var rs=document.querySelectorAll('#pmItemRows .pm-item-text'); var t=rs.length?rs[rs.length-1]:null; if(t){ try{ t.focus(); var _L=t.value.length; t.setSelectionRange(_L,_L); }catch(_e){} } },40);
  };
  window.pmDelete = function(id){""",
 """    setTimeout(function(){
      if(focusVendor){ var vv=document.getElementById('projMemoVendor'); if(vv) try{ vv.focus(); }catch(_e){} return; }
      var rs=document.querySelectorAll('#pmItemRows .pm-item-text'); var t=rs.length?rs[rs.length-1]:null; if(t){ try{ t.focus(); var _L=t.value.length; t.setSelectionRange(_L,_L); }catch(_e){} }
    },40);
  };
  window.pmDelete = function(id){"""),

("""  function _pmRender(force){""",
 """  window.pmInlineStart = function(sp){
    var mid=sp.dataset.mid, iid=sp.dataset.iid;
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    var it=(m.items||[]).find(function(x){ return x.id===iid; }); if(!it) return;
    var inp=document.createElement('input');
    inp.type='text'; inp.value=it.text||'';
    inp.style.cssText='flex:1;min-width:0;border:none;border-bottom:1px solid #1B3A6B;background:transparent;font-size:12px;color:#374151;font-family:inherit;outline:none;padding:0';
    inp.dataset.mid=mid; inp.dataset.iid=iid;
    inp.onkeydown=function(ev){ if(ev.key==='Enter'){ ev.preventDefault(); inp.blur(); } else if(ev.key==='Escape'){ inp.value=it.text||''; inp.blur(); } };
    inp.onblur=function(){ pmInlineEditSave(inp); };
    sp.parentNode.replaceChild(inp, sp);
    try{ inp.focus(); var _L=inp.value.length; inp.setSelectionRange(_L,_L); }catch(_e){}
  };
  window.pmInlineEditSave = function(inp){
    var m=projMemos.find(function(x){ return x.id===inp.dataset.mid; });
    var it=m?(m.items||[]).find(function(x){ return x.id===inp.dataset.iid; }):null;
    var v=String(inp.value||'').trim();
    if(it && v && v!==it.text){ it.text=v; _pmSave(); }
    _pmRender(true);
  };
  window.pmInlineDelItem = function(mid, iid){
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    var its=m.items||[];
    if(its.length<=1){ pmDelete(mid); return; }   // 마지막 줄이면 메모 전체 삭제 확인
    m.items=its.filter(function(x){ return x.id!==iid; });
    _pmSave(); _pmRender(true);
  };
  function _pmRender(force){"""),

("""    if(!force && _pmForm && document.getElementById('pmItemRows')) return;   // 작성 중 외부 재렌더 금지""",
 """    if(!force){
      if(_pmForm && document.getElementById('pmItemRows')) return;   // 작성 중 외부 재렌더 금지
      var _ae=document.activeElement;
      if(_ae && _ae.closest && _ae.closest('#projMemoBoard')) return;   // 인라인 수정 중 보호
    }"""),

("""          + '<span style="flex:1;min-width:0;font-size:12px;line-height:1.5;color:#4b5563;word-break:break-all;'+(it.done?'text-decoration:line-through;color:#b0b6bf;':'')+'">'+esc(it.text)+'<span style="font-size:10px;color:#b6a94f;margin-left:4px;white-space:nowrap;text-decoration:none;display:inline-block">'+_pmFmtDs(it.date)+'</span></span>'
          + '</div>';""",
 """          + '<span '+(mine?('data-mid="'+m.id+'" data-iid="'+esc(it.id)+'" onclick="pmInlineStart(this)" title="클릭하여 바로 수정" '):'')+'style="flex:1;min-width:0;font-size:12px;line-height:1.5;color:#4b5563;word-break:break-all;'+(mine?'cursor:text;':'')+(it.done?'text-decoration:line-through;color:#b0b6bf;':'')+'">'+esc(it.text)+'<span style="font-size:10px;color:#b6a94f;margin-left:4px;white-space:nowrap;text-decoration:none;display:inline-block">'+_pmFmtDs(it.date)+'</span></span>'
          + (mine?('<button data-mid="'+m.id+'" data-iid="'+esc(it.id)+'" onclick="pmInlineDelItem(this.dataset.mid,this.dataset.iid)" title="줄 삭제" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:1px 2px;color:#dc2626;display:inline-flex;align-items:center;margin-top:2px" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'):'')
          + '</div>';"""),

("""        +   '<span title="'+esc((m.vendors||[]).join(', '))+'" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;">'""",
 """        +   '<span '+(mine?('data-id="'+m.id+'" onclick="pmEditStart(this.dataset.id, true)" '):'')+'title="'+esc((m.vendors||[]).join(', '))+(mine?' (클릭하여 수정)':'')+'" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;'+(mine?'cursor:pointer;':'')+'">'"""),
]

def apply_r92(s, path):
    for i,(old,new) in enumerate(R92_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R92 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r92(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r91 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r91 2026-08-19 -->', '<!-- test build r92 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
