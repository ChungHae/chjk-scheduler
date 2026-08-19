# -*- coding: utf-8 -*-
# r97: 접힌 카드 제목 옆에 ＋(업체 추가) 버튼 상시 표시. (재작성본 v2)

R97_EDITS = [
("""  window.pmVendEditEnd = function(){ _pmVendEditFor=null; _pmVendSugHide(); _pmRender(true); };""",
 """  window.pmVendEditEnd = function(){ _pmVendEditFor=null; _pmVendSugHide(); _pmRender(true); };
  window.pmVendQuickAdd = function(mid){
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    _pmVendEditFor=mid;
    _pmRender(true);
    setTimeout(function(){ pmVendAddStart(mid); },40);
  };"""),

("""            return '<div style="display:flex;align-items:center;gap:5px;margin-bottom:5px;flex-shrink:0">'
              + '<span '+(mine?('data-id="'+m.id+'" onclick="pmVendEditStartInline(this.dataset.id)" '):'')+'title="'+esc((m.vendors||[]).join(', '))+(mine?' (클릭하여 수정)':'')+'" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;'+(mine?'cursor:pointer;':'')+'">'+((m.vendors&&m.vendors.length)?esc(m.vendors.join(' · ')):'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'
              + _badge + '</div>';""",
 """            return '<div style="display:flex;align-items:center;gap:5px;margin-bottom:5px;flex-shrink:0">'
              + '<span '+(mine?('data-id="'+m.id+'" onclick="pmVendEditStartInline(this.dataset.id)" '):'')+'title="'+esc((m.vendors||[]).join(', '))+(mine?' (클릭하여 수정)':'')+'" style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;'+(mine?'cursor:pointer;':'')+'">'+((m.vendors&&m.vendors.length)?esc(m.vendors.join(' · ')):'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'
              + (mine?('<button data-id="'+m.id+'" onclick="pmVendQuickAdd(this.dataset.id)" title="업체 추가" style="flex-shrink:0;border:none;background:none;cursor:pointer;color:#b6a94f;font-size:13px;font-weight:700;padding:0 2px;line-height:1;font-family:inherit" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#b6a94f\\'">&#65291;</button>'):'')
              + _badge + '</div>';"""),
]

def apply_r97(s, path):
    for i,(old,new) in enumerate(R97_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R97 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r97(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r96 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r96 2026-08-19 -->', '<!-- test build r97 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
