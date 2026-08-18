# -*- coding: utf-8 -*-
# r40 재작성본: 줄 삭제 휴지통 아이콘, 줄추가·취소·저장 한 줄(28px), 등록 폭 1020px
R40_EDITS = [
("""    <div id="projFormView" style="display:none;max-width:780px;margin:0 auto"></div>""",
 """    <div id="projFormView" style="display:none;max-width:1020px;margin:0 auto"></div>"""),

("""      + '<button type="button" onclick="projFormDelRow(this)" title="줄 삭제" style="'+_PJ_SBTN+';color:#dc2626;border-color:#e5c0c0">&#10005;</button>'""",
 """      + '<button type="button" onclick="projFormDelRow(this)" title="줄 삭제" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:2px 3px;color:#dc2626;display:inline-flex;align-items:center;margin-top:5px" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'"""),

("""      +   '<div id="projFormRows" style="display:flex;flex-direction:column;gap:8px">'
      +     _projFormRowHtml()
      +   '</div>'
      +   '<div><button type="button" onclick="projFormAddRow()" style="'+_PJ_SBTN+';height:26px">&#65291; 기록 줄 추가</button></div>'
      + '</div>'
      + '<div style="display:flex;justify-content:flex-end;gap:6px;padding:0 14px 14px">'
      +   '<button type="button" onclick="cancelProjectForm()" style="'+_PJ_BTN+';background:#fff;color:#444;border:1px solid #c8d2de">취소</button>'
      +   '<button type="button" onclick="saveProjectEdit()" style="'+_PJ_BTN+';background:#1a1a1a;color:#fff;border:1px solid #1a1a1a">저장</button>'
      + '</div></div>';""",
 """      +   '<div id="projFormRows" style="display:flex;flex-direction:column;gap:8px">'
      +     _projFormRowHtml()
      +   '</div>'
      + '</div>'
      + '<div style="display:flex;align-items:center;gap:6px;padding:0 14px 14px">'
      +   '<button type="button" onclick="projFormAddRow()" style="'+_PJ_BTN+';background:#fff;color:#1B3A6B;border:1px solid #1B3A6B">&#65291; 기록 줄 추가</button>'
      +   '<span style="flex:1"></span>'
      +   '<button type="button" onclick="cancelProjectForm()" style="'+_PJ_BTN+';background:#fff;color:#444;border:1px solid #c8d2de">취소</button>'
      +   '<button type="button" onclick="saveProjectEdit()" style="'+_PJ_BTN+';background:#1a1a1a;color:#fff;border:1px solid #1a1a1a">저장</button>'
      + '</div></div>';"""),
]
def apply_r40(s, path):
    for i,(old,new) in enumerate(R40_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R40 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
