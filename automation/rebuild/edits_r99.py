# -*- coding: utf-8 -*-
# r99: (1) 마지막 내용 줄 인라인 수정 중 엔터 → 저장 후 다음 내용칸 열기
#      (2) 메모 내용이 없어도 메모장처럼 구분선(괘선) 상시 노출

R99_EDITS = [

# (1a) pmInlineStart 엔터: 마지막 줄이면 next 플래그
("""    inp.onkeydown=function(ev){ if(ev.key==='Enter'){ ev.preventDefault(); inp.blur(); } else if(ev.key==='Escape'){ inp.value=it.text||''; inp.blur(); } };""",
 """    inp.onkeydown=function(ev){ if(ev.key==='Enter'){ ev.preventDefault(); var _its=m.items||[]; if(_its.length&&_its[_its.length-1].id===iid) inp.dataset.next='1'; inp.blur(); } else if(ev.key==='Escape'){ inp.value=it.text||''; inp.blur(); } };"""),

# (1b) pmInlineEditSave: next 플래그면 저장 후 새 내용 입력줄 열기
("""  window.pmInlineEditSave = function(inp){
    var m=projMemos.find(function(x){ return x.id===inp.dataset.mid; });
    var it=m?(m.items||[]).find(function(x){ return x.id===inp.dataset.iid; }):null;
    var v=String(inp.value||'').trim();
    if(it && v && v!==it.text){ it.text=v; _pmSave(); }
    _pmRender(true);
  };""",
 """  window.pmInlineEditSave = function(inp){
    var mid=inp.dataset.mid;
    var next=inp.dataset.next==='1';
    var m=projMemos.find(function(x){ return x.id===mid; });
    var it=m?(m.items||[]).find(function(x){ return x.id===inp.dataset.iid; }):null;
    var v=String(inp.value||'').trim();
    if(it && v && v!==it.text){ it.text=v; _pmSave(); }
    _pmRender(true);
    if(next) setTimeout(function(){ pmInlineAddStart(mid); },30);   // 마지막 줄 엔터 → 다음 내용칸 계속
  };"""),

# (2a) 내용 줄: 모든 줄 아래에 괘선 (기존: 줄 사이에만)
("""        return '<div style="display:flex;align-items:flex-start;gap:5px;padding:3px 0;'+(_ii<its.length-1?'border-bottom:1px solid rgba(182,169,79,.28);':'')+'">'""",
 """        return '<div style="flex-shrink:0;display:flex;align-items:flex-start;gap:5px;padding:3px 0;border-bottom:1px solid rgba(182,169,79,.28)">'"""),

# (2b) 내용 컨테이너: flex column + 빈 공간을 괘선으로 채우는 필러
("""        + '<div style="flex:1;min-height:0;overflow:auto">'+itemsHtml
        +   (mine?('<div style="display:flex;align-items:center;margin-top:2px"><button data-pmadd="'+m.id+'" onclick="pmInlineAddStart(this.dataset.pmadd)" title="내용 줄 추가" style="border:none;background:none;cursor:pointer;color:#b6a94f;font-size:11px;padding:2px;display:inline-flex;align-items:center;gap:3px;font-family:inherit" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#b6a94f\\'">&#65291; 줄 추가</button></div>'):'')
        + '</div>'""",
 """        + '<div style="flex:1;min-height:0;overflow:auto;display:flex;flex-direction:column">'+itemsHtml
        +   (mine?('<div style="flex-shrink:0;display:flex;align-items:center;margin-top:2px"><button data-pmadd="'+m.id+'" onclick="pmInlineAddStart(this.dataset.pmadd)" title="내용 줄 추가" style="border:none;background:none;cursor:pointer;color:#b6a94f;font-size:11px;padding:2px;display:inline-flex;align-items:center;gap:3px;font-family:inherit" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#b6a94f\\'">&#65291; 줄 추가</button></div>'):'')
        +   '<div style="flex:1;background:repeating-linear-gradient(to bottom,transparent 0,transparent 24px,rgba(182,169,79,.28) 24px,rgba(182,169,79,.28) 25px)"></div>'
        + '</div>'"""),

# (2c) 인라인 새 줄 입력행도 flex column 안에서 줄어들지 않게
("""    row.style.cssText='display:flex;align-items:center;gap:4px;border-bottom:1px solid rgba(182,169,79,.35)';""",
 """    row.style.cssText='flex-shrink:0;display:flex;align-items:center;gap:4px;border-bottom:1px solid rgba(182,169,79,.35)';"""),
]

def apply_r99(s, path):
    for i,(old,new) in enumerate(R99_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R99 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r99(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r98 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r98 2026-08-19 -->', '<!-- test build r99 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
