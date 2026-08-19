# -*- coding: utf-8 -*-
# r91: 메모 작성/수정을 별도 등록창이 아닌 '노란 포스트잇 카드 그 자체'에서 하도록 변경. (재작성본 v2)

R91_EDITS = [
("""  function _pmItemRowHtml(it){
    it=it||{};
    return '<div class="pm-item-row" data-iid="'+esc(it.id||'')+'" data-done="'+(it.done?'1':'0')+'" data-date="'+esc(it.date||'')+'" style="display:flex;gap:6px;align-items:center">'
      + '<input type="text" class="pm-item-text" value="'+esc(it.text||'')+'" placeholder="할 일 / 내용" style="flex:1;min-width:0;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;color:#374151;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
      + (it.date?('<span style="flex-shrink:0;font-size:11px;color:#9ca3af">'+esc(_pmFmtDs(it.date))+'</span>'):'')
      + '<button type="button" onclick="pmDelItemRow(this)" title="줄 삭제" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:2px 3px;color:#dc2626;display:inline-flex;align-items:center" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'
      + '</div>';
  }""",
 """  function _pmItemRowHtml(it){
    it=it||{};
    return '<div class="pm-item-row" data-iid="'+esc(it.id||'')+'" data-done="'+(it.done?'1':'0')+'" data-date="'+esc(it.date||'')+'" style="display:flex;gap:4px;align-items:center;border-bottom:1px solid rgba(182,169,79,.35)">'
      + '<input type="text" class="pm-item-text" value="'+esc(it.text||'')+'" placeholder="할 일 / 내용" style="flex:1;min-width:0;height:24px;box-sizing:border-box;padding:0 2px;border:none;background:transparent;font-size:12px;color:#374151;font-family:inherit;outline:none">'
      + (it.date?('<span style="flex-shrink:0;font-size:10px;color:#b6a94f">'+esc(_pmFmtDs(it.date))+'</span>'):'')
      + '<button type="button" onclick="pmDelItemRow(this)" title="줄 삭제" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:1px 2px;color:#dc2626;display:inline-flex;align-items:center" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:12px;height:12px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'
      + '</div>';
  }
  function _pmFormCardHtml(em){
    var rowsHtml=(em&&em.items&&em.items.length)?em.items.map(_pmItemRowHtml).join(''):_pmItemRowHtml({});
    return '<div id="pmFormCard" style="aspect-ratio:1/1;background:#fff9c4;border:1px solid #d97706;box-shadow:0 2px 8px rgba(0,0,0,.14);display:flex;flex-direction:column;padding:9px 10px;min-width:0">'
      + '<div style="position:relative;flex-shrink:0">'
      + '<input id="projMemoVendor" type="text" placeholder="업체명 (검색/입력 후 엔터, 여러 개 가능)" autocomplete="off" oninput="pmVendorSearch(this)" onkeydown="pmVendorKey(event)" style="width:100%;box-sizing:border-box;padding:2px 0 4px;border:none;border-bottom:1px solid rgba(182,169,79,.5);background:transparent;font-size:12px;font-weight:700;color:#14305c;font-family:inherit;outline:none" onfocus="this.style.borderBottomColor=\\'#1B3A6B\\';pmVendorSearch(this)" onblur="this.style.borderBottomColor=\\'rgba(182,169,79,.5)\\';pmVendorBlur()">'
      + '<div id="pmVendorSug" style="display:none;position:absolute;top:100%;left:0;right:0;z-index:60;background:#fff;border:1px solid #c8d2de;max-height:180px;overflow:auto;box-shadow:0 8px 22px rgba(15,23,42,.18)"></div>'
      + '</div>'
      + '<div id="pmVendorChips" style="display:none;flex-wrap:wrap;gap:4px;margin-top:5px;flex-shrink:0"></div>'
      + '<div style="flex:1;min-height:0;overflow:auto;margin-top:4px"><div id="pmItemRows" style="display:flex;flex-direction:column;gap:2px">'+rowsHtml+'</div></div>'
      + '<div style="display:flex;align-items:center;gap:4px;margin-top:6px;flex-shrink:0">'
      +   '<button type="button" onclick="pmAddItemRow()" title="내용 줄 추가" style="'+_PJ_SBTN+';height:19px;font-size:10.5px;padding:0 6px;color:#1B3A6B;border-color:#1B3A6B">&#65291; 줄</button>'
      +   '<span style="flex:1"></span>'
      +   '<button type="button" onclick="pmToggleForm(false)" style="'+_PJ_SBTN+';height:19px;font-size:10.5px;padding:0 6px">취소</button>'
      +   '<button type="button" onclick="pmSaveMemo()" style="'+_PJ_SBTN+';height:19px;font-size:10.5px;padding:0 6px;background:#1a1a1a;border-color:#1a1a1a;color:#fff">'+(em?'저장':'등록')+'</button>'
      + '</div>'
      + '</div>';
  }"""),

("""    var cards=shown.map(function(m){
      var mine=myMemberId && m.memberId===myMemberId;""",
 """    var cards=shown.map(function(m){
      if(_pmForm && _pmEditId===m.id) return _pmFormCardHtml(m);
      var mine=myMemberId && m.memberId===myMemberId;"""),

("""    var formCard='';
    if(_pmForm){
      var em=_pmEditId?projMemos.find(function(x){ return x.id===_pmEditId; }):null;
      var rowsHtml=(em&&em.items&&em.items.length)?em.items.map(_pmItemRowHtml).join(''):_pmItemRowHtml({});
      formCard = '<div id="pmFormCard" style="grid-column:1/-1;background:#fffdf0;border:1px solid #e6d97a;padding:11px 12px;display:flex;flex-direction:column;gap:7px">'
        + (em?('<div style="font-size:11.5px;font-weight:700;color:#b45309">메모 수정</div>'):'')
        + '<div style="position:relative">'
        + '<input id="projMemoVendor" type="text" placeholder="업체명 (선택) &mdash; 검색/입력 후 엔터로 여러 업체 추가" autocomplete="off" oninput="pmVendorSearch(this)" onkeydown="pmVendorKey(event)" style="width:100%;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\';pmVendorSearch(this)" onblur="this.style.borderColor=\\'#c8d2de\\';pmVendorBlur()">'
        + '<div id="pmVendorSug" style="display:none;position:absolute;top:100%;left:0;right:0;z-index:60;background:#fff;border:1px solid #c8d2de;max-height:200px;overflow:auto;box-shadow:0 8px 22px rgba(15,23,42,.14)"></div>'
        + '</div>'
        + '<div id="pmVendorChips" style="display:none;flex-wrap:wrap;gap:6px"></div>'
        + '<div id="pmItemRows" style="display:flex;flex-direction:column;gap:6px">'+rowsHtml+'</div>'
        + '<div style="display:flex;align-items:center;gap:6px">'
        +   '<button type="button" onclick="pmAddItemRow()" style="'+_PJ_SBTN+';color:#1B3A6B;border-color:#1B3A6B">&#65291; 내용 추가</button>'
        +   '<span style="flex:1"></span>'
        +   '<button type="button" onclick="pmToggleForm(false)" style="'+_PJ_SBTN+'">취소</button>'
        +   '<button type="button" onclick="pmSaveMemo()" style="'+_PJ_SBTN+';background:#1a1a1a;border-color:#1a1a1a;color:#fff">'+(em?'저장':'등록')+'</button>'
        + '</div>'
        + '</div>';
    }""",
 """    var formCard='';
    if(_pmForm && !_pmEditId){ formCard=_pmFormCardHtml(null); }"""),
]

def apply_r91(s, path):
    for i,(old,new) in enumerate(R91_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R91 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r91(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r90 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r90 2026-08-19 -->', '<!-- test build r91 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
