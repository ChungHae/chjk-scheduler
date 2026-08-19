# -*- coding: utf-8 -*-
# r86: 메모 업체명 입력에 업체관리 목록 자동완성 추가. (재작성본 v2)

R86_EDITS = [
("""  function _pmRender(force){""",
 """  window.pmVendorSearch = function(el){
    var box=document.getElementById('pmVendorSug'); if(!box) return;
    var q=String(el.value||'').trim().toLowerCase();
    if(!q){ box.style.display='none'; box.innerHTML=''; return; }
    try{ ensureClientList(); }catch(_e){}
    var hit=allClients().filter(function(c){ return String(c[0]).toLowerCase().indexOf(q)>=0; }).slice(0,30);
    if(!hit.length){ box.style.display='none'; box.innerHTML=''; return; }
    box.innerHTML=hit.map(function(c){ return '<div onmousedown="pmVendorPick(this.dataset.nm)" data-nm="'+esc(c[0])+'" style="padding:7px 10px;cursor:pointer;font-size:12.5px;color:#374151;border-bottom:1px solid #f1f5f9" onmouseover="this.style.background=\\'#f4f8fe\\'" onmouseout="this.style.background=\\'\\'">'+esc(c[0])+'</div>'; }).join('');
    box.style.display='block';
  };
  window.pmVendorPick = function(nm){
    var i=document.getElementById('projMemoVendor'); if(i) i.value=nm||'';
    var box=document.getElementById('pmVendorSug'); if(box){ box.style.display='none'; box.innerHTML=''; }
    var t=document.getElementById('projMemoText'); if(t) setTimeout(function(){ try{ t.focus(); }catch(_e){} },20);
  };
  window.pmVendorBlur = function(){ setTimeout(function(){ var b=document.getElementById('pmVendorSug'); if(b) b.style.display='none'; },150); };
  function _pmRender(force){"""),

("""        + '<input id="projMemoVendor" type="text" placeholder="업체명 (선택)" style="width:100%;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'""",
 """        + '<div style="position:relative">'
        + '<input id="projMemoVendor" type="text" placeholder="업체명 (선택) &mdash; 입력하면 업체 목록에서 선택할 수 있습니다" autocomplete="off" oninput="pmVendorSearch(this)" style="width:100%;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\';pmVendorSearch(this)" onblur="this.style.borderColor=\\'#c8d2de\\';pmVendorBlur()">'
        + '<div id="pmVendorSug" style="display:none;position:absolute;top:100%;left:0;right:0;z-index:60;background:#fff;border:1px solid #c8d2de;max-height:200px;overflow:auto;box-shadow:0 8px 22px rgba(15,23,42,.14)"></div>'
        + '</div>'"""),
]

def apply_r86(s, path):
    for i,(old,new) in enumerate(R86_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R86 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r86(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r85 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r85 2026-08-19 -->', '<!-- test build r86 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
