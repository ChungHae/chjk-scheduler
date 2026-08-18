# -*- coding: utf-8 -*-
# r42: 등록된 프로젝트 클릭 시 화면 전환 대신 목록에서 아래로 펼쳐지는(아코디언) 방식으로 변경

PROJ_JS7 = '''  // ─── 프로젝트 (날짜별 진행 기록 누적 · 팝업 없이 페이지 내 전환) ─────
  // 전 직원 열람 가능, 기록 추가/수정/삭제는 작성자 본인만.
  // [{id, memberId, authorName, title, logs:[{id,date:'YYYY-MM-DD',text,ts,done}], createdAt, updatedAt}]
  // 목록에서 프로젝트를 클릭하면 그 아래로 상세가 펼쳐진다. 펼친 상태의 모든 변경(이동·수정·삭제·추가·완료체크·제목)은
  // 초안에만 반영되고 [저장]을 눌러야 실제 저장된다.
  function _projSave(){
    save('sched_projects', projectsList);
    localStorage.setItem('sched_local_ts', Date.now().toString());
    try{ debouncedFbSave(); }catch(_e){}
  }
  function _projFmtD(ts){
    if(!ts) return '';
    var d = new Date(ts);
    return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
  }
  function _projAuthor(p){
    var m = members.find(function(x){ return x.id===p.memberId; });
    return m ? m.name : (p.authorName || '');
  }
  function _projLogs(p){
    if (Array.isArray(p.logs)) return p.logs;
    if (p.content) return [{ id:'lg_legacy', date:_projFmtD(p.createdAt||Date.now()), text:p.content, ts:(p.createdAt||0) }];
    return [];
  }
  // 표시 순서: 날짜순 정렬 (같은 날짜 안에서는 저장된 배열 순서 유지 → ▲▼로 조정)
  function _projLogsView(logs){
    return (logs||[]).map(function(lg,i){ return {lg:lg, i:i}; }).sort(function(a,b){
      var da=String(a.lg.date||''), db2=String(b.lg.date||'');
      return da===db2 ? (a.i-b.i) : (da<db2?-1:1);
    }).map(function(x){ return x.lg; });
  }
  function _projDLabel(ds){
    var dt=new Date(ds+'T12:00:00'); if(isNaN(dt.getTime())) return esc(ds||'');
    var DAY=['일','월','화','수','목','금','토'];
    return esc(ds)+'('+DAY[dt.getDay()]+')';
  }
  var _projMode = { view:'list', id:null };   // 'list' | 'form'(신규 등록)
  var _projExpId = null;      // 펼쳐진 프로젝트 id
  var _projLogEditId = null;
  var _projTitleEdit = false;
  var _projDraft = null;      // 펼친 프로젝트 초안 {id, title, logs[]}
  var _projDirty = false;     // 저장되지 않은 변경 여부
  var _PJ_BTN  = 'padding:0 14px;height:28px;box-sizing:border-box;display:inline-flex;align-items:center;border-radius:0;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit';
  var _PJ_SBTN = 'padding:0 8px;height:22px;box-sizing:border-box;display:inline-flex;align-items:center;background:#fff;border:1px solid #c8d2de;border-radius:0;font-size:11px;font-weight:600;color:#556;cursor:pointer;font-family:inherit';
  var _PJ_DATE = 'height:30px;width:130px;flex-shrink:0;box-sizing:border-box;padding:0 6px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit;outline:none';
  var _PJ_TA   = 'flex:1;min-width:0;box-sizing:border-box;padding:7px 10px;border:1px solid #c8d2de;border-radius:0;font-size:13px;color:#374151;line-height:1.6;font-family:inherit;resize:vertical;outline:none';
  function _projForceRender(){
    var lv=document.getElementById('projListView'), fv=document.getElementById('projFormView'), dv=document.getElementById('projDetailView');
    if(!lv||!fv||!dv) return;
    dv.style.display='none';   // 상세 화면은 더 이상 쓰지 않음 (목록 안 펼침으로 대체)
    lv.style.display = _projMode.view==='list' ? '' : 'none';
    fv.style.display = _projMode.view==='form' ? '' : 'none';
    if(_projMode.view==='list') _projRenderList();
    else _projRenderForm();
  }
  window.renderProjectPage = function(){
    // 동기화 폴링 등 외부 진입점 — 작성/수정 중이거나 저장 전 변경이 있으면 화면을 건드리지 않는다
    if(_projMode.view==='form') return;
    if(_projExpId){
      if(_projDirty || _projLogEditId || _projTitleEdit) return;
      var _t=document.getElementById('projLogText');
      if(_t && _t.value && _t.value.trim()) return;
    }
    var _ae=document.activeElement;
    if(_ae && (_ae.tagName==='INPUT'||_ae.tagName==='TEXTAREA') && /^proj/.test(_ae.id||'')) return;
    _projForceRender();
  };
  function _projGo(view, id){
    _projMode = { view:view, id:(id||null) };
    _projExpId = null;
    _projLogEditId = null;
    _projTitleEdit = false;
    _projDraft = null;
    _projDirty = false;
    _projForceRender();
    try{ window.scrollTo(0,0); }catch(_e){}
  }
  function _projExpand(id){
    _projExpId = id; _projDraft = null; _projDirty = false; _projLogEditId = null; _projTitleEdit = false;
    _projForceRender();
  }
  function _projCollapse(){
    _projExpId = null; _projDraft = null; _projDirty = false; _projLogEditId = null; _projTitleEdit = false;
    _projForceRender();
  }
  // 펼친 프로젝트 상세 패널 HTML
  function _projPanelHtml(p, mine){
    var logs = _projLogsView(_projDraft.logs);
    var rows = logs.length ? logs.map(function(lg, li){
      if(mine && _projLogEditId===lg.id){
        return '<div style="padding:9px 2px;border-bottom:1px solid #eef2f7">'
          + '<div style="display:flex;gap:8px;align-items:flex-start">'
          +   '<input id="projLogEditDate" type="date" value="'+esc(lg.date)+'" style="'+_PJ_DATE+'">'
          +   '<textarea id="projLogEditText" style="'+_PJ_TA+';min-height:60px">'+esc(lg.text||'')+'</textarea>'
          +   '<span style="display:flex;flex-direction:column;gap:4px;flex-shrink:0">'
          +     '<button onclick="saveProjectLogEdit(\\''+lg.id+'\\')" style="'+_PJ_SBTN+';background:#1a1a1a;border-color:#1a1a1a;color:#fff">확인</button>'
          +     '<button onclick="cancelProjectLogEdit()" style="'+_PJ_SBTN+'">취소</button>'
          +   '</span>'
          + '</div></div>';
      }
      var _prevSame = li>0 && String(logs[li-1].date)===String(lg.date);
      var _nextSame = li<logs.length-1 && String(logs[li+1].date)===String(lg.date);
      return '<div style="display:flex;gap:10px;padding:9px 2px;border-bottom:1px solid #eef2f7;align-items:flex-start">'
        + '<span style="flex-shrink:0;width:108px;font-size:11.5px;font-weight:700;color:#4a6c99;padding-top:2px">'+_projDLabel(lg.date)+'</span>'
        + '<input type="checkbox" '+(lg.done?'checked ':'')+(mine?('onchange="toggleProjectLog(\\''+lg.id+'\\')" '):'disabled ')+'title="완료 표시" style="width:15px;height:15px;accent-color:#1B3A6B;margin-top:3px;flex-shrink:0;cursor:'+(mine?'pointer':'default')+'">'
        + '<div style="flex:1;min-width:0;font-size:13px;line-height:1.65;white-space:pre-wrap;word-break:break-all;'+(lg.done?'text-decoration:line-through;color:#9ca3af':'color:#374151')+'">'+esc(lg.text||'')+'</div>'
        + (mine ? ('<span style="flex-shrink:0;display:flex;gap:4px;align-items:center">'
            + (_prevSame ? '<button onclick="moveProjectLog(\\''+lg.id+'\\',-1)" style="'+_PJ_SBTN+';padding:0 6px" title="위로 (같은 날짜 안에서만)">&#9650;</button>'
                         : '<button disabled style="'+_PJ_SBTN+';padding:0 6px;opacity:.3;cursor:default" title="같은 날짜끼리만 이동 가능">&#9650;</button>')
            + (_nextSame ? '<button onclick="moveProjectLog(\\''+lg.id+'\\',1)" style="'+_PJ_SBTN+';padding:0 6px" title="아래로 (같은 날짜 안에서만)">&#9660;</button>'
                         : '<button disabled style="'+_PJ_SBTN+';padding:0 6px;opacity:.3;cursor:default" title="같은 날짜끼리만 이동 가능">&#9660;</button>')
            + '<button onclick="editProjectLog(\\''+lg.id+'\\')" style="'+_PJ_SBTN+'">수정</button>'
            + '<button onclick="deleteProjectLog(\\''+lg.id+'\\')" style="'+_PJ_SBTN+';color:#dc2626;border-color:#e5c0c0">삭제</button>'
            + '</span>') : '')
        + '</div>';
    }).join('') : '<div style="text-align:center;color:#b6bec9;font-size:12px;padding:22px 0">아직 기록이 없습니다.</div>';
    var addForm = mine ? ('<div style="border-top:2px solid #1B3A6B;padding:10px 14px 12px;background:#fbfcfe">'
      + '<div style="font-size:12px;font-weight:700;color:#1a1a1a;margin-bottom:6px">기록 추가</div>'
      + '<div style="display:flex;gap:8px;align-items:flex-start">'
      +   '<input id="projLogDate" type="date" value="'+dk(new Date())+'" style="'+_PJ_DATE+'">'
      +   '<textarea id="projLogText" placeholder="진행한 내용을 적어주세요." style="'+_PJ_TA+';min-height:60px" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'"></textarea>'
      + '</div>'
      + '<div style="display:flex;justify-content:flex-end;margin-top:6px">'
      +   '<button onclick="addProjectLog()" style="'+_PJ_BTN+';background:#1a1a1a;color:#fff;border:1px solid #1a1a1a">기록 추가</button>'
      + '</div></div>') : '';
    var meta = esc(_projAuthor(p))+' &middot; 시작 '+_projFmtD(p.createdAt)+' &middot; 기록 '+logs.length+'건';
    return '<div style="border-top:1px solid #e3eaf2;background:#fff;cursor:default">'
      + '<div style="padding:8px 14px;font-size:11.5px;color:#8b97a5;border-bottom:1px solid #eef2f7">'+meta+'</div>'
      + '<div style="padding:2px 14px 8px">'+rows+'</div>'
      + addForm
      + (mine ? ('<div style="display:flex;align-items:center;gap:10px;padding:10px 14px 14px;border-top:1px solid #eef2f7">'
        +   '<button type="button" onclick="deleteProject(\\''+p.id+'\\')" style="'+_PJ_BTN+';background:#fff;color:#dc2626;border:1px solid #dc2626">프로젝트 삭제</button>'
        +   '<span style="flex:1"></span>'
        +   (_projDirty?'<span style="font-size:11.5px;color:#dc2626;font-weight:600">저장되지 않은 변경사항이 있습니다</span>':'')
        +   (_projDirty?('<button type="button" onclick="projSaveDetail()" style="'+_PJ_BTN+';background:#1a1a1a;color:#fff;border:1px solid #1a1a1a">저장</button>')
                       :('<button type="button" disabled style="'+_PJ_BTN+';background:#f4f6f9;color:#a8b3c0;border:1px solid #dfe5ec;cursor:default">저장</button>'))
        + '</div>') : '')
      + '</div>';
  }
  function _projRenderList(){
    var box = document.getElementById('projectList'); if(!box) return;
    var list = projectsList.slice().sort(function(a,b){ return (b.updatedAt||b.createdAt||0)-(a.updatedAt||a.createdAt||0); });
    if(!list.length){
      _projExpId=null;
      box.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:52px 16px;color:#b6bec9;font-size:13px;line-height:1.8">등록된 프로젝트가 없습니다.<br>우측 상단의 [프로젝트 등록] 버튼으로 첫 프로젝트를 만들어보세요.</div>';
      return;
    }
    if(_projExpId && !list.some(function(x){ return x.id===_projExpId; })) _projExpId=null;
    box.innerHTML = list.map(function(p){
      var mine = myMemberId && p.memberId===myMemberId;
      var exp = _projExpId===p.id;
      // 펼친 프로젝트의 초안 준비 (깨끗한 상태면 최신 데이터로 동기화)
      if(exp){
        if(!_projDraft || _projDraft.id!==p.id){ _projDraft=null; _projDirty=false; }
        if(!_projDirty){ _projDraft = { id:p.id, title:p.title, logs: JSON.parse(JSON.stringify(_projLogs(p))) }; }
      }
      var titlePart;
      if(exp && mine && _projTitleEdit){
        titlePart = '<input id="projTitleInline" type="text" maxlength="120" value="'+esc(_projDraft.title||'')+'" onclick="event.stopPropagation()" onkeydown="if(event.key===\\'Enter\\')projTitleSave()" style="flex:1;min-width:0;height:26px;box-sizing:border-box;padding:0 8px;border:1px solid #1B3A6B;border-radius:0;font-size:13px;font-weight:700;color:#14305c;font-family:inherit;outline:none">'
          + '<button onclick="event.stopPropagation();projTitleSave()" style="'+_PJ_SBTN+';background:#1a1a1a;border-color:#1a1a1a;color:#fff;flex-shrink:0">확인</button>'
          + '<button onclick="event.stopPropagation();projTitleCancel()" style="'+_PJ_SBTN+';flex-shrink:0">취소</button>';
      } else {
        titlePart = '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px;font-weight:700;color:#14305c">'+esc(exp?(_projDraft.title||'(제목 없음)'):(p.title||'(제목 없음)'))+'</span>'
          + ((exp && mine)?'<button onclick="event.stopPropagation();projTitleEditStart()" title="제목 수정" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:0 3px;color:#5b7ba6;display:inline-flex;align-items:center" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#5b7ba6\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg></button>':'')
          + '<span style="flex:1"></span>';
      }
      var header = '<div onclick="openProjectView(\\''+p.id+'\\')" style="padding:11px 16px;cursor:pointer;display:flex;align-items:center;gap:8px;'+(exp?'background:#f4f8fe':'')+'" '+(exp?'':('onmouseover="this.style.background=\\'#f7fafd\\'" onmouseout="this.style.background=\\'#fff\\'"'))+'>'
        + '<span style="flex-shrink:0;width:0;height:0;border-left:5px solid #8b97a5;border-top:4px solid transparent;border-bottom:4px solid transparent;'+(exp?'transform:rotate(90deg);':'')+'"></span>'
        + titlePart
        + '<span style="flex-shrink:0;font-size:12px;color:#8b97a5">'+esc(_projAuthor(p))+' &middot; '+_projFmtD(p.createdAt)+'</span>'
        + '</div>';
      return '<div style="background:#fff;border:1px solid #d8e1ec;border-left:3px solid '+(exp?'#1B3A6B':(mine?'#1B3A6B':'#c3cfde'))+'">'
        + header
        + (exp ? _projPanelHtml(p, mine) : '')
        + '</div>';
    }).join('');
  }
  function _projFormRowHtml(){
    return '<div class="projFormRow" style="display:flex;gap:8px;align-items:flex-start">'
      + '<input type="date" class="pfr-date" value="'+dk(new Date())+'" style="'+_PJ_DATE+'">'
      + '<textarea class="pfr-text" placeholder="진행한 내용을 적어주세요. (비워두면 이 줄은 저장되지 않습니다)" style="'+_PJ_TA+';min-height:80px" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'"></textarea>'
      + '<button type="button" onclick="projFormDelRow(this)" title="줄 삭제" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:2px 3px;color:#dc2626;display:inline-flex;align-items:center;margin-top:5px" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'
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
  function _projRenderForm(){
    var fv = document.getElementById('projFormView'); if(!fv) return;
    fv.innerHTML = '<div style="background:#fff;border:1px solid #c8d2de">'
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
      + '</div></div>';
    setTimeout(function(){ var i=document.getElementById('projTitleInput'); if(i) try{ i.focus(); }catch(_e){} }, 60);
  }
  window.projBackToList = function(){ _projGo('list', null); };
  window.cancelProjectForm = function(){ _projGo('list', null); };
  // 목록에서 프로젝트 클릭: 펼침/접기 토글 (저장 전 변경이 있으면 확인)
  window.openProjectView = function(id){
    if(_projExpId===id){
      if(_projDirty){
        showConfirmModal('변경사항 미저장','저장하지 않은 변경사항이 있습니다.\\n저장하지 않고 닫을까요?', function(){ _projCollapse(); }, '저장 안 함', '#dc2626');
        return;
      }
      _projCollapse(); return;
    }
    if(_projDirty){
      showConfirmModal('변경사항 미저장','저장하지 않은 변경사항이 있습니다.\\n저장하지 않고 다른 프로젝트를 열까요?', function(){ _projExpand(id); }, '열기', '#dc2626');
      return;
    }
    _projExpand(id);
  };
  window.openProjectNew = function(){
    if(!myMemberId){ showInfoModal('알림','프로필을 먼저 설정해주세요.'); return; }
    if(_projDirty){
      showConfirmModal('변경사항 미저장','저장하지 않은 변경사항이 있습니다.\\n저장하지 않고 등록 화면으로 이동할까요?', function(){ _projGo('form', null); }, '이동', '#dc2626');
      return;
    }
    _projGo('form', null);
  };
  window.projTitleEditStart = function(){
    _projTitleEdit = true; _projForceRender();
    setTimeout(function(){ var i=document.getElementById('projTitleInline'); if(i){ try{ i.focus(); i.select(); }catch(_e){} } }, 60);
  };
  window.projTitleCancel = function(){ _projTitleEdit = false; _projForceRender(); };
  window.projTitleSave = function(){
    if(!_projDraft) return;
    var t = (document.getElementById('projTitleInline').value||'').trim();
    if(!t){ showInfoModal('프로젝트','프로젝트 명을 입력해주세요.'); return; }
    if(t!==_projDraft.title){ _projDraft.title = t; _projDirty = true; }
    _projTitleEdit = false;
    _projForceRender();
  };
  window.saveProjectEdit = function(){
    var t = (document.getElementById('projTitleInput').value||'').trim();
    if(!t){ showInfoModal('프로젝트','프로젝트 명을 입력해주세요.'); return; }
    var now = Date.now();
    var me = members.find(function(x){ return x.id===myMemberId; });
    var logs = [];
    var rows0 = document.querySelectorAll('#projFormRows .projFormRow');
    for(var ri=0; ri<rows0.length; ri++){
      var tx=(rows0[ri].querySelector('.pfr-text').value||'').trim();
      if(!tx) continue;
      var dt=rows0[ri].querySelector('.pfr-date').value || dk(new Date());
      logs.push({ id:'lg'+now+'_'+ri+'_'+Math.floor(Math.random()*10000), date:dt, text:tx, ts:now+ri, done:false });
    }
    var np = { id:'prj'+now+'_'+Math.floor(Math.random()*10000), memberId:myMemberId, authorName:(me?me.name:''), title:t, logs:logs, createdAt:now, updatedAt:now };
    projectsList.push(np);
    _projSave();
    _projGo('list', null);
    _projExpand(np.id);   // 방금 만든 프로젝트를 펼쳐서 보여준다
  };
  // ── 펼친 프로젝트 초안 조작 (저장 전까지 실제 데이터에 반영되지 않음) ──
  function _projDraftEditable(){
    if(!_projDraft) return false;
    var p = projectsList.find(function(x){ return x.id===_projDraft.id; });
    return !!(p && p.memberId===myMemberId);
  }
  window.moveProjectLog = function(lid, dir){
    if(!_projDraftEditable()) return;
    var view = _projLogsView(_projDraft.logs);
    var vi=-1; for(var z=0;z<view.length;z++){ if(view[z].id===lid){ vi=z; break; } }
    if(vi<0) return;
    var tgt=view[vi+dir];
    if(!tgt || String(tgt.date)!==String(view[vi].date)) return;   // 같은 날짜끼리만 이동
    var arr=_projDraft.logs, ia=-1, ib=-1;
    for(var y=0;y<arr.length;y++){ if(arr[y].id===lid) ia=y; if(arr[y].id===tgt.id) ib=y; }
    if(ia<0||ib<0) return;
    var tmp=arr[ia]; arr[ia]=arr[ib]; arr[ib]=tmp;
    _projDirty=true; _projForceRender();
  };
  window.toggleProjectLog = function(lid){
    if(!_projDraftEditable()) return;
    var lg=_projDraft.logs.find(function(x){ return x.id===lid; }); if(!lg) return;
    lg.done = !lg.done;
    _projDirty=true; _projForceRender();
  };
  window.addProjectLog = function(){
    if(!_projDraftEditable()) return;
    var d = document.getElementById('projLogDate').value;
    var t = (document.getElementById('projLogText').value||'').trim();
    if(!d){ showInfoModal('프로젝트','날짜를 선택해주세요.'); return; }
    if(!t){ showInfoModal('프로젝트','내용을 입력해주세요.'); return; }
    _projDraft.logs.push({ id:'lg'+Date.now()+'_'+Math.floor(Math.random()*10000), date:d, text:t, ts:Date.now(), done:false });
    _projDirty=true; _projForceRender();
  };
  window.editProjectLog = function(lid){
    if(!_projDraftEditable()) return;
    _projLogEditId = lid; _projForceRender();
    setTimeout(function(){ var te=document.getElementById('projLogEditText'); if(te) te.focus(); }, 60);
  };
  window.cancelProjectLogEdit = function(){ _projLogEditId = null; _projForceRender(); };
  window.saveProjectLogEdit = function(lid){
    if(!_projDraftEditable()) return;
    var d = document.getElementById('projLogEditDate').value;
    var t = (document.getElementById('projLogEditText').value||'').trim();
    if(!d){ showInfoModal('프로젝트','날짜를 선택해주세요.'); return; }
    if(!t){ showInfoModal('프로젝트','내용을 입력해주세요.'); return; }
    var lg=_projDraft.logs.find(function(x){ return x.id===lid; });
    if(lg){ if(lg.date!==d||lg.text!==t){ lg.date=d; lg.text=t; _projDirty=true; } }
    _projLogEditId = null;
    _projForceRender();
  };
  window.deleteProjectLog = function(lid){
    if(!_projDraftEditable()) return;
    _projDraft.logs = _projDraft.logs.filter(function(x){ return x.id!==lid; });
    _projDirty=true; _projForceRender();
  };
  window.projSaveDetail = function(){
    if(!_projDraft || !_projDirty) return;
    var p = projectsList.find(function(x){ return x.id===_projDraft.id; });
    if(!p || p.memberId!==myMemberId){ showInfoModal('프로젝트','저장할 수 없습니다. (프로젝트가 삭제되었거나 권한이 없습니다)'); return; }
    p.title = _projDraft.title;
    p.logs = JSON.parse(JSON.stringify(_projDraft.logs));
    delete p.content;
    p.updatedAt = Date.now();
    _projDirty = false;
    _projSave(); _projForceRender();
  };
  window.deleteProject = function(id){
    var p = projectsList.find(function(x){ return x.id===id; }); if(!p) return;
    if(p.memberId!==myMemberId){ showInfoModal('알림','본인이 작성한 프로젝트만 삭제할 수 있습니다.'); return; }
    showConfirmModal('프로젝트 삭제', esc(p.title)+' 프로젝트를 삭제할까요?\\n모든 기록이 함께 삭제되며 되돌릴 수 없습니다.', function(){
      projectsList = projectsList.filter(function(x){ return x.id!==id; });
      _projCollapse();
      _projSave();
      _projForceRender();
    }, '삭제', '#dc2626');
  };
'''

JS_START = "  // ─── 프로젝트 (날짜별 진행 기록 누적 · 팝업 없이 페이지 내 전환) ─────"
JS_END = "  function _vacUnlimited(id){"
SWITCH_OLD = "    if (page === 'project'){ _projMode={view:'list',id:null}; _projLogEditId=null; renderProjectPage(); }"
SWITCH_NEW = "    if (page === 'project'){ _projMode={view:'list',id:null}; _projExpId=null; _projLogEditId=null; _projTitleEdit=false; _projDraft=null; _projDirty=false; renderProjectPage(); }"

def apply_r42(s, path):
    a = s.index(JS_START)
    b = s.index(JS_END, a)
    s = s[:a] + PROJ_JS7 + s[b:]
    n = s.count(SWITCH_OLD)
    if n != 1: raise SystemExit('R42 switch FAIL %s count %d' % (path, n))
    return s.replace(SWITCH_OLD, SWITCH_NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r42(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r41 2026-08-12 -->') == 1
            s = s.replace('<!-- test build r41 2026-08-12 -->', '<!-- test build r42 2026-08-12 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
