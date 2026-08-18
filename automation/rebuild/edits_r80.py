# -*- coding: utf-8 -*-
# r80: 프로젝트 등록창을 표 스타일(날짜/내용/삭제)·가로 전체 폭으로 변경 (재작성본 v3)

R80_EDITS = [
("""  function _projFormRowHtml(){
    return '<div class="projFormRow" style="display:flex;gap:8px;align-items:flex-start">'
      + '<input type="date" class="pfr-date" value="'+dk(new Date())+'" style="'+_PJ_DATE+'">'
      + '<textarea class="pfr-text" placeholder="진행한 내용을 적어주세요. (비워두면 이 줄은 저장되지 않습니다)" style="'+_PJ_TA+';min-height:80px" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'"></textarea>'
      + '<button type="button" onclick="projFormDelRow(this)" title="줄 삭제" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:2px 3px;color:#dc2626;display:inline-flex;align-items:center;margin-top:5px" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'
      + '</div>';
  }""",
 """  function _projFormRowHtml(){
    var TD='padding:0;border-bottom:1px solid #eef2f7;border-right:1px solid #eef2f7;vertical-align:top';
    return '<tr class="projFormRow">'
      + '<td style="'+TD+'"><input type="date" class="pfr-date" value="'+dk(new Date())+'" style="width:100%;min-height:46px;box-sizing:border-box;border:none;outline:none;padding:0 10px;font-size:12.5px;font-family:inherit;color:#374151;background:transparent" onfocus="this.closest(\\'td\\').style.background=\\'#f4f8fe\\'" onblur="this.closest(\\'td\\').style.background=\\'\\'"></td>'
      + '<td style="'+TD+'"><textarea class="pfr-text" placeholder="진행한 내용을 적어주세요. (비워두면 이 줄은 저장되지 않습니다)" style="display:block;width:100%;min-height:46px;box-sizing:border-box;border:none;outline:none;resize:vertical;padding:13px 12px;font-size:12.5px;line-height:1.6;font-family:inherit;color:#374151;background:transparent" onfocus="this.closest(\\'td\\').style.background=\\'#f4f8fe\\'" onblur="this.closest(\\'td\\').style.background=\\'\\'"></textarea></td>'
      + '<td style="'+TD+';text-align:center;vertical-align:middle"><button type="button" onclick="projFormDelRow(this)" title="줄 삭제" style="border:none;background:none;cursor:pointer;padding:2px 3px;color:#dc2626;display:inline-flex;align-items:center" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button></td>'
      + '</tr>';
  }"""),

("""    var d=document.createElement('div'); d.innerHTML=_projFormRowHtml();
    var row=d.firstChild; box.appendChild(row);
    try{ row.querySelector('.pfr-text').focus(); }catch(_e){}
  };
  window.projFormDelRow = function(btn){""",
 """    var d=document.createElement('tbody'); d.innerHTML=_projFormRowHtml();
    var row=d.firstChild; box.appendChild(row);
    try{ row.querySelector('.pfr-text').focus(); }catch(_e){}
  };
  window.projFormDelRow = function(btn){"""),

("""    fv.innerHTML = '<div style="background:#fff;border:1px solid #c8d2de">'
      + '<div style="padding:9px 14px;border-bottom:1px solid #c8d2de;background:#f4f6f9;display:flex;align-items:center;gap:8px">'
      +   '<span style="width:3px;height:15px;background:#1a1a1a;flex-shrink:0"></span>'
      +   '<span style="font-size:13.5px;font-weight:700;color:#1a1a1a">프로젝트 등록</span>'
      + '</div>'
      + '<div style="padding:14px;display:flex;flex-direction:column;gap:10px">'
      +   '<input id="projTitleInput" type="text" placeholder="프로젝트 명" maxlength="120" style="width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #c8d2de;border-radius:0;font-size:13.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
      +   '<div id="projFormRows" style="display:flex;flex-direction:column;gap:8px">'
      +     _projFormRowHtml()
      +   '</div>'
      + '</div>'
      + '<div style="display:flex;align-items:center;gap:6px;padding:0 14px 14px">'
      +   '<button type="button" onclick="projFormAddRow()" style="'+_PJ_BTN+';background:#fff;color:#1B3A6B;border:1px solid #1B3A6B">&#65291; 기록 줄 추가</button>'
      +   '<span style="flex:1"></span>'
      +   '<button type="button" onclick="cancelProjectForm()" style="'+_PJ_BTN+';background:#fff;color:#444;border:1px solid #c8d2de">취소</button>'
      +   '<button type="button" onclick="saveProjectEdit()" style="'+_PJ_BTN+';background:#1a1a1a;color:#fff;border:1px solid #1a1a1a">저장</button>'
      + '</div></div>';""",
 """    var TH='padding:9px 10px;background:#fafafa;color:#888;font-weight:500;font-size:12px;text-align:center;border-bottom:2px solid #d3dce6;border-right:1px solid #e3e9f0;white-space:nowrap';
    fv.innerHTML = '<div style="background:#fff;border:1px solid #d6deea;border-left:none;border-right:none;margin:0 calc(var(--mpx, 24px)*-1)">'
      + '<div style="padding:9px 14px;border-bottom:1px solid #c8d2de;background:#f4f6f9;display:flex;align-items:center;gap:8px">'
      +   '<span style="width:3px;height:15px;background:#1a1a1a;flex-shrink:0"></span>'
      +   '<span style="font-size:13.5px;font-weight:700;color:#1a1a1a">프로젝트 등록</span>'
      + '</div>'
      + '<div style="padding:12px 14px;border-bottom:1px solid #e3e9f0">'
      +   '<input id="projTitleInput" type="text" placeholder="프로젝트 명" maxlength="120" style="width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #c8d2de;border-radius:0;font-size:13.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
      + '</div>'
      + '<table style="width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:12.5px">'
      + '<colgroup><col style="width:150px"><col><col style="width:54px"></colgroup>'
      + '<thead><tr><th style="'+TH+'">날짜</th><th style="'+TH+'">내용</th><th style="'+TH+'"></th></tr></thead>'
      + '<tbody id="projFormRows">'+_projFormRowHtml()+'</tbody>'
      + '</table>'
      + '<div style="display:flex;align-items:center;gap:6px;padding:12px 14px;border-top:1px solid #e3e9f0">'
      +   '<button type="button" onclick="projFormAddRow()" style="'+_PJ_BTN+';background:#fff;color:#1B3A6B;border:1px solid #1B3A6B">&#65291; 기록 줄 추가</button>'
      +   '<span style="flex:1"></span>'
      +   '<button type="button" onclick="cancelProjectForm()" style="'+_PJ_BTN+';background:#fff;color:#444;border:1px solid #c8d2de">취소</button>'
      +   '<button type="button" onclick="saveProjectEdit()" style="'+_PJ_BTN+';background:#1a1a1a;color:#fff;border:1px solid #1a1a1a">저장</button>'
      + '</div></div>';"""),
]

def apply_r80(s, path):
    for i,(old,new) in enumerate(R80_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R80 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r80(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r79 2026-08-14 -->') == 1
            s = s.replace('<!-- test build r79 2026-08-14 -->', '<!-- test build r80 2026-08-14 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
