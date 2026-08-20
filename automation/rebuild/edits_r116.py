# -*- coding: utf-8 -*-
# r116: 메모 내용 작성/수정 시 Ctrl+Enter = 줄바꿈 (한 항목 안에서 여러 줄),
#       Enter = 기존처럼 저장(마지막 줄이면 다음 내용칸). input → textarea 전환 + 표시 시 \n → <br>

R116_EDITS = [

# (1) 표시: 줄바꿈 렌더링
("""'">'+esc(it.text)+'<span style="font-size:10px;color:#b6a94f;""",
 """'">'+esc(it.text).replace(/\\n/g,'<br>')+'<span style="font-size:10px;color:#b6a94f;""", 1),

# (2) 인라인 수정: textarea + Ctrl+Enter 줄바꿈
("""    var inp=document.createElement('input');
    inp.type='text'; inp.value=it.text||'';
    inp.style.cssText='flex:1;min-width:0;border:none;border-bottom:1px solid #1B3A6B;background:transparent;font-size:12px;color:#374151;font-family:inherit;outline:none;padding:0';
    inp.dataset.mid=mid; inp.dataset.iid=iid;
    inp.onkeydown=function(ev){ if(ev.key==='Enter'){ ev.preventDefault(); var _its=m.items||[]; if(_its.length&&_its[_its.length-1].id===iid) inp.dataset.next='1'; inp.blur(); } else if(ev.key==='Escape'){ inp.value=it.text||''; inp.blur(); } };
    inp.onblur=function(){ pmInlineEditSave(inp); };
    sp.parentNode.replaceChild(inp, sp);
    try{ inp.focus(); var _L=inp.value.length; inp.setSelectionRange(_L,_L); }catch(_e){}""",
 """    var inp=document.createElement('textarea');
    inp.rows=1; inp.value=it.text||'';
    inp.style.cssText='flex:1;min-width:0;border:none;border-bottom:1px solid #1B3A6B;background:transparent;font-size:12px;color:#374151;font-family:inherit;outline:none;padding:0;resize:none;line-height:1.5;overflow:hidden';
    inp.dataset.mid=mid; inp.dataset.iid=iid;
    var _fit=function(){ inp.style.height='auto'; inp.style.height=inp.scrollHeight+'px'; };
    inp.oninput=_fit;
    inp.onkeydown=function(ev){
      if(ev.key==='Enter'){
        ev.preventDefault();
        if(ev.ctrlKey){ var _s=inp.selectionStart,_e=inp.selectionEnd; inp.value=inp.value.slice(0,_s)+'\\n'+inp.value.slice(_e); inp.selectionStart=inp.selectionEnd=_s+1; _fit(); return; }   // Ctrl+Enter = 줄바꿈
        var _its=m.items||[]; if(_its.length&&_its[_its.length-1].id===iid) inp.dataset.next='1'; inp.blur();
      } else if(ev.key==='Escape'){ inp.value=it.text||''; inp.blur(); }
    };
    inp.onblur=function(){ pmInlineEditSave(inp); };
    sp.parentNode.replaceChild(inp, sp);
    try{ inp.focus(); var _L=inp.value.length; inp.setSelectionRange(_L,_L); _fit(); }catch(_e){}""", 1),

# (3) 새 줄 입력: textarea + Ctrl+Enter 줄바꿈
("""    var inp=document.createElement('input');
    inp.type='text'; inp.placeholder='새 내용';
    inp.style.cssText='flex:1;min-width:0;border:none;background:transparent;font-size:12px;color:#374151;font-family:inherit;outline:none;padding:2px;height:24px;box-sizing:border-box';
    inp.dataset.mid=mid;
    inp.onkeydown=function(ev){
      if(ev.key==='Enter'){ ev.preventDefault(); inp.dataset.again='1'; inp.blur(); }
      else if(ev.key==='Escape'){ inp.value=''; inp.blur(); }
    };""",
 """    var inp=document.createElement('textarea');
    inp.rows=1; inp.placeholder='새 내용';
    inp.style.cssText='flex:1;min-width:0;border:none;background:transparent;font-size:12px;color:#374151;font-family:inherit;outline:none;padding:2px;height:24px;box-sizing:border-box;resize:none;line-height:1.5;overflow:hidden';
    inp.dataset.mid=mid;
    var _fit=function(){ inp.style.height='auto'; inp.style.height=Math.max(24,inp.scrollHeight)+'px'; };
    inp.oninput=_fit;
    inp.onkeydown=function(ev){
      if(ev.key==='Enter'){
        ev.preventDefault();
        if(ev.ctrlKey){ var _s=inp.selectionStart,_e=inp.selectionEnd; inp.value=inp.value.slice(0,_s)+'\\n'+inp.value.slice(_e); inp.selectionStart=inp.selectionEnd=_s+1; _fit(); return; }   // Ctrl+Enter = 줄바꿈
        inp.dataset.again='1'; inp.blur();
      }
      else if(ev.key==='Escape'){ inp.value=''; inp.blur(); }
    };""", 1),
]

def apply_r116(s, path):
    for i,(old,new,exp) in enumerate(R116_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R116 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r116(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r115 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r115 2026-08-20 -->', '<!-- test build r116 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
