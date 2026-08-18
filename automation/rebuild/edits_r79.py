# -*- coding: utf-8 -*-
# r79: 프로젝트 목록을 업체 관리식 전체 폭 표로 변경 (재작성본 v3)

START = "    box.innerHTML = list.map(function(p){"
END = "  function _projFormRowHtml(){"

NEW_BODY = r'''    var TH='padding:9px 10px;background:#fafafa;color:#888;font-weight:500;font-size:12px;text-align:center;border-bottom:2px solid #d3dce6;border-right:1px solid #e3e9f0;white-space:nowrap';
    var TD='padding:10px;border-bottom:1px solid #eef2f7;border-right:1px solid #eef2f7;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle';
    var rowsHtml = list.map(function(p){
      var mine = myMemberId && p.memberId===myMemberId;
      var exp = _projExpId===p.id;
      // 펼친 프로젝트의 초안 준비 (깨끗한 상태면 최신 데이터로 동기화)
      if(exp){
        if(!_projDraft || _projDraft.id!==p.id){ _projDraft=null; _projDirty=false; }
        if(!_projDirty){ _projDraft = { id:p.id, title:p.title, logs: JSON.parse(JSON.stringify(_projLogs(p))) }; }
      }
      var titlePart;
      if(exp && mine && _projTitleEdit){
        titlePart = '<div style="display:flex;align-items:center;gap:6px;min-width:0">'
          + '<input id="projTitleInline" type="text" maxlength="120" value="'+esc(_projDraft.title||'')+'" onclick="event.stopPropagation()" onkeydown="if(event.key===\'Enter\')projTitleSave()" style="flex:1;min-width:0;height:26px;box-sizing:border-box;padding:0 8px;border:1px solid #1B3A6B;border-radius:0;font-size:13px;font-weight:700;color:#14305c;font-family:inherit;outline:none">'
          + '<button onclick="event.stopPropagation();projTitleSave()" style="'+_PJ_SBTN+';background:#1a1a1a;border-color:#1a1a1a;color:#fff;flex-shrink:0">확인</button>'
          + '<button onclick="event.stopPropagation();projTitleCancel()" style="'+_PJ_SBTN+';flex-shrink:0">취소</button>'
          + '</div>';
      } else {
        titlePart = '<div style="display:flex;align-items:center;gap:6px;min-width:0">'
          + '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(exp?(_projDraft.title||'(제목 없음)'):(p.title||'(제목 없음)'))+'</span>'
          + ((exp && mine)?'<button onclick="event.stopPropagation();projTitleEditStart()" title="제목 수정" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:0 3px;color:#5b7ba6;display:inline-flex;align-items:center" onmouseover="this.style.color=\'#1B3A6B\'" onmouseout="this.style.color=\'#5b7ba6\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg></button>':'')
          + '</div>';
      }
      var logs=_projLogs(p);
      var lastD=''; logs.forEach(function(l){ if(l.date && String(l.date)>lastD) lastD=String(l.date); });
      var dim = _projExpId && !exp;   // 다른 프로젝트가 펼쳐져 있으면 나머지는 흐리게
      var tr='<tr onclick="openProjectView(\''+p.id+'\')" style="cursor:pointer;'+(exp?'background:#f4f8fe;':'')+(dim?'opacity:.18;transition:opacity .12s;':'')+'"'
        + (dim?' onmouseover="this.style.opacity=\'.85\'" onmouseout="this.style.opacity=\'.18\'"':(exp?'':' onmouseover="this.style.background=\'#f7fafd\'" onmouseout="this.style.background=\'\'"'))+'>'
        + '<td style="'+TD+';font-weight:700;color:#14305c;box-shadow:inset 3px 0 0 '+(mine?'#1B3A6B':'transparent')+'">'+titlePart+'</td>'
        + '<td style="'+TD+';text-align:center">'+esc(_projAuthor(p))+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+_projFmtD(p.createdAt)+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(lastD||'-')+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+logs.length+'</td>'
        + '</tr>';
      if(exp){
        tr += '<tr><td colspan="5" style="padding:0;border-bottom:2px solid #1B3A6B;background:#fff;white-space:normal">'+_projPanelHtml(p, mine)+'</td></tr>';
      }
      return tr;
    }).join('');
    box.innerHTML = '<div style="background:#fff;border:1px solid #d6deea;border-left:none;border-right:none;margin:0 calc(var(--mpx, 24px)*-1)">'
      + '<table style="width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:12.5px">'
      + '<colgroup><col><col style="width:110px"><col style="width:120px"><col style="width:120px"><col style="width:80px"></colgroup>'
      + '<thead><tr>'
      +   '<th style="'+TH+'">프로젝트명</th><th style="'+TH+'">등록자</th><th style="'+TH+'">등록일</th><th style="'+TH+'">최근 기록</th><th style="'+TH+'">기록 수</th>'
      + '</tr></thead><tbody>'+rowsHtml+'</tbody></table></div>';
  }
'''

def apply_r79(s, path):
    n1 = s.count(START); n2 = s.count(END)
    if n1 != 1 or n2 != 1: raise SystemExit('R79 FAIL %s marker counts %d %d' % (path, n1, n2))
    a = s.index(START)
    b = s.index(END, a)
    return s[:a] + NEW_BODY + s[b:]

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r79(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r78 2026-08-14 -->') == 1
            s = s.replace('<!-- test build r78 2026-08-14 -->', '<!-- test build r79 2026-08-14 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
