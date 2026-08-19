# -*- coding: utf-8 -*-
# r88: 메모 사용성 3건. (재작성본 v2)
#      1) 수정 시 커서가 마지막 내용칸 끝에서 시작
#      2) 업체명 입력 중 엔터 → 검색 목록 최상단 업체 선택 (목록 없으면 내용칸으로 이동)
#      3) 카드 내용 줄 사이에만 메모장식 구분선 (양 끝 제외)

R88_EDITS = [
("""    _pmEditId=id; _pmForm=true;
    _pmRender(true);
    setTimeout(function(){ var i=document.getElementById('projMemoVendor'); if(i) try{ i.focus(); }catch(_e){} },40);
  };
  window.pmDelete = function(id){""",
 """    _pmEditId=id; _pmForm=true;
    _pmRender(true);
    setTimeout(function(){ var rs=document.querySelectorAll('#pmItemRows .pm-item-text'); var t=rs.length?rs[rs.length-1]:null; if(t){ try{ t.focus(); var _L=t.value.length; t.setSelectionRange(_L,_L); }catch(_e){} } },40);
  };
  window.pmDelete = function(id){"""),

("""  window.pmVendorBlur = function(){ setTimeout(function(){ var b=document.getElementById('pmVendorSug'); if(b) b.style.display='none'; },150); };""",
 """  window.pmVendorKey = function(ev){
    if(ev.key!=='Enter') return;
    ev.preventDefault();
    var box=document.getElementById('pmVendorSug');
    if(box && box.style.display==='block'){
      var first=box.querySelector('div[data-nm]');
      if(first){ pmVendorPick(first.dataset.nm); return; }
    }
    var t=document.querySelector('#pmItemRows .pm-item-text'); if(t) try{ t.focus(); }catch(_e){}
  };
  window.pmVendorBlur = function(){ setTimeout(function(){ var b=document.getElementById('pmVendorSug'); if(b) b.style.display='none'; },150); };"""),

("""autocomplete="off" oninput="pmVendorSearch(this)" style="width:100%;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\';pmVendorSearch(this)" onblur="this.style.borderColor=\\'#c8d2de\\';pmVendorBlur()">""",
 """autocomplete="off" oninput="pmVendorSearch(this)" onkeydown="pmVendorKey(event)" style="width:100%;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\';pmVendorSearch(this)" onblur="this.style.borderColor=\\'#c8d2de\\';pmVendorBlur()">"""),

("""      var itemsHtml=its.map(function(it){""",
 """      var itemsHtml=its.map(function(it, _ii){"""),

("""        return '<div style="display:flex;align-items:flex-start;gap:5px;margin-bottom:3px">'""",
 """        return '<div style="display:flex;align-items:flex-start;gap:5px;padding:3px 0;'+(_ii<its.length-1?'border-bottom:1px solid rgba(182,169,79,.28);':'')+'">'"""),
]

def apply_r88(s, path):
    for i,(old,new) in enumerate(R88_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R88 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r88(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r87 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r87 2026-08-19 -->', '<!-- test build r88 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
