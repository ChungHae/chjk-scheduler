# -*- coding: utf-8 -*-
# r39 재작성본: 등록 시 기록 여러 줄 입력(+줄 추가/삭제), 기록 위아래 순서 이동
R39_EDITS = [
("""    var logs = _projLogsSorted(p);
    var rows = logs.length ? logs.map(function(lg){""",
"""    var logs = _projLogs(p);
    var rows = logs.length ? logs.map(function(lg, li){"""),

("""        + (mine ? ('<span style="flex-shrink:0;display:flex;gap:4px">'
            + '<button onclick="editProjectLog(\\''+p.id+'\\',\\''+lg.id+'\\')" style="'+_PJ_SBTN+'">수정</button>'
            + '<button onclick="deleteProjectLog(\\''+p.id+'\\',\\''+lg.id+'\\')" style="'+_PJ_SBTN+';color:#dc2626;border-color:#e5c0c0">삭제</button>'
            + '</span>') : '')""",
"""        + (mine ? ('<span style="flex-shrink:0;display:flex;gap:4px;align-items:center">'
            + (li===0 ? '<button disabled style="'+_PJ_SBTN+';padding:0 6px;opacity:.3;cursor:default" title="위로">&#9650;</button>'
                      : '<button onclick="moveProjectLog(\\''+p.id+'\\',\\''+lg.id+'\\',-1)" style="'+_PJ_SBTN+';padding:0 6px" title="위로">&#9650;</button>')
            + (li===logs.length-1 ? '<button disabled style="'+_PJ_SBTN+';padding:0 6px;opacity:.3;cursor:default" title="아래로">&#9660;</button>'
                      : '<button onclick="moveProjectLog(\\''+p.id+'\\',\\''+lg.id+'\\',1)" style="'+_PJ_SBTN+';padding:0 6px" title="아래로">&#9660;</button>')
            + '<button onclick="editProjectLog(\\''+p.id+'\\',\\''+lg.id+'\\')" style="'+_PJ_SBTN+'">수정</button>'
            + '<button onclick="deleteProjectLog(\\''+p.id+'\\',\\''+lg.id+'\\')" style="'+_PJ_SBTN+';color:#dc2626;border-color:#e5c0c0">삭제</button>'
            + '</span>') : '')""",),

("""      +   '<div style="display:flex;gap:8px;align-items:flex-start">'
      +     '<input id="projLogDate0" type="date" value="'+dk(new Date())+'" style="'+_PJ_DATE+'">'
      +     '<textarea id="projLogText0" placeholder="진행한 내용을 적어주세요. (비워두면 프로젝트만 만들어집니다)" style="'+_PJ_TA+';min-height:170px" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'"></textarea>'
      +   '</div>'
      + '</div>'""",
"""      +   '<div id="projFormRows" style="display:flex;flex-direction:column;gap:8px">'
      +     _projFormRowHtml()
      +   '</div>'
      +   '<div><button type="button" onclick="projFormAddRow()" style="'+_PJ_SBTN+';height:26px">&#65291; 기록 줄 추가</button></div>'
      + '</div>'"""),

("""  function _projRenderForm(){""",
"""  function _projFormRowHtml(){
    return '<div class="projFormRow" style="display:flex;gap:8px;align-items:flex-start">'
      + '<input type="date" class="pfr-date" value="'+dk(new Date())+'" style="'+_PJ_DATE+'">'
      + '<textarea class="pfr-text" placeholder="진행한 내용을 적어주세요. (비워두면 이 줄은 저장되지 않습니다)" style="'+_PJ_TA+';min-height:80px" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'"></textarea>'
      + '<button type="button" onclick="projFormDelRow(this)" title="줄 삭제" style="'+_PJ_SBTN+';color:#dc2626;border-color:#e5c0c0">&#10005;</button>'
      + '</div>';
  }
  window.projFormAddRow = function(){
    var box=document.getElementById('projFormRows'); if(!box) return;
    var d=document.createElement('div'); d.innerHTML=_projFormRowHtml();
    var row=d.firstChild; box.appendChild(row);
    try{ row.querySelector('.pfr-text').focus(); }catch(_e){}
  };
  window.projFormDelRow = function(btn){
    var box=document.getElementById('projFormRows'); if(!box) return;
    var row=btn.closest('.projFormRow'); if(!row) return;
    if(box.querySelectorAll('.projFormRow').length<=1){
      row.querySelector('.pfr-text').value=''; row.querySelector('.pfr-date').value=dk(new Date());
      return;   // 마지막 한 줄은 비우기만 한다
    }
    row.remove();
  };
  function _projRenderForm(){"""),

("""    var logs = [];
    var d0el = document.getElementById('projLogDate0');
    var t0el = document.getElementById('projLogText0');
    var t0 = t0el ? (t0el.value||'').trim() : '';
    if(t0){
      var d0 = (d0el && d0el.value) || dk(new Date());
      logs.push({ id:'lg'+now+'_'+Math.floor(Math.random()*10000), date:d0, text:t0, ts:now });
    }""",
"""    var logs = [];
    var rows0 = document.querySelectorAll('#projFormRows .projFormRow');
    for(var ri=0; ri<rows0.length; ri++){
      var tx=(rows0[ri].querySelector('.pfr-text').value||'').trim();
      if(!tx) continue;
      var dt=rows0[ri].querySelector('.pfr-date').value || dk(new Date());
      logs.push({ id:'lg'+now+'_'+ri+'_'+Math.floor(Math.random()*10000), date:dt, text:tx, ts:now+ri });
    }"""),

("""  window.addProjectLog = function(pid){""",
"""  window.moveProjectLog = function(pid, lid, dir){
    var p = projectsList.find(function(x){ return x.id===pid; }); if(!p || p.memberId!==myMemberId) return;
    _projMigrate(p);
    var i = -1;
    for(var z=0; z<p.logs.length; z++){ if(p.logs[z].id===lid){ i=z; break; } }
    if(i<0) return;
    var j = i + dir;
    if(j<0 || j>=p.logs.length) return;
    var tmp=p.logs[i]; p.logs[i]=p.logs[j]; p.logs[j]=tmp;
    p.updatedAt = Date.now();
    _projSave(); _projForceRender();
  };
  window.addProjectLog = function(pid){"""),
]
def apply_r39(s, path):
    for i,(old,new) in enumerate(R39_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R39 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
