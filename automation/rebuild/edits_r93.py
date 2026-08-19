# -*- coding: utf-8 -*-
# r93: 메모 카드에서 직접 줄 추가 + 연필(수정) 버튼 제거. (재작성본 v2)

R93_EDITS = [
("""  function _pmRender(force){""",
 """  window.pmInlineAddStart = function(mid){
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    var btn=document.querySelector('#projMemoBoard button[data-pmadd="'+mid+'"]'); if(!btn) return;
    var row=document.createElement('div');
    row.style.cssText='display:flex;align-items:center;gap:4px;border-bottom:1px solid rgba(182,169,79,.35)';
    var inp=document.createElement('input');
    inp.type='text'; inp.placeholder='새 내용';
    inp.style.cssText='flex:1;min-width:0;border:none;background:transparent;font-size:12px;color:#374151;font-family:inherit;outline:none;padding:2px;height:24px;box-sizing:border-box';
    inp.dataset.mid=mid;
    inp.onkeydown=function(ev){
      if(ev.key==='Enter'){ ev.preventDefault(); inp.dataset.again='1'; inp.blur(); }
      else if(ev.key==='Escape'){ inp.value=''; inp.blur(); }
    };
    inp.onblur=function(){ pmInlineAddSave(inp); };
    row.appendChild(inp);
    btn.parentNode.parentNode.insertBefore(row, btn.parentNode);
    try{ inp.focus(); }catch(_e){}
  };
  window.pmInlineAddSave = function(inp){
    var mid=inp.dataset.mid;
    var m=projMemos.find(function(x){ return x.id===mid; });
    var v=String(inp.value||'').trim();
    var saved=false;
    if(m && v && myMemberId && m.memberId===myMemberId){
      if(!Array.isArray(m.items)) m.items=[];
      m.items.push({ id:'pi'+Date.now().toString(36)+Math.random().toString(36).slice(2,5), text:v, done:false, date:dk(new Date()) });
      _pmSave(); saved=true;
    }
    var again=saved && inp.dataset.again==='1';
    _pmRender(true);
    if(again) setTimeout(function(){ pmInlineAddStart(mid); },30);   // 엔터로 저장하면 바로 다음 줄 계속 입력
  };
  function _pmRender(force){"""),

("""        + '<div style="flex:1;min-height:0;overflow:auto">'+itemsHtml+'</div>'""",
 """        + '<div style="flex:1;min-height:0;overflow:auto">'+itemsHtml
        +   (mine?('<div style="display:flex;align-items:center;margin-top:2px"><button data-pmadd="'+m.id+'" onclick="pmInlineAddStart(this.dataset.pmadd)" title="내용 줄 추가" style="border:none;background:none;cursor:pointer;color:#b6a94f;font-size:11px;padding:2px;display:inline-flex;align-items:center;gap:3px;font-family:inherit" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#b6a94f\\'">&#65291; 줄 추가</button></div>'):'')
        + '</div>'"""),

("""        +   (mine ? (
              '<button data-id="'+m.id+'" onclick="pmEditStart(this.dataset.id)" title="수정" style="border:none;background:none;cursor:pointer;padding:1px 2px;color:#5b7ba6;display:inline-flex;align-items:center;flex-shrink:0" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#5b7ba6\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px;display:block"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg></button>'
            + '<button data-id="'+m.id+'" onclick="pmDelete(this.dataset.id)" title="삭제" """,
 """        +   (mine ? (
              '<button data-id="'+m.id+'" onclick="pmDelete(this.dataset.id)" title="삭제" """),
]

def apply_r93(s, path):
    for i,(old,new) in enumerate(R93_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R93 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r93(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r92 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r92 2026-08-19 -->', '<!-- test build r93 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
