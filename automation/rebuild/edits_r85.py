# -*- coding: utf-8 -*-
# r85: 프로젝트 최상단 포스트잇 메모장. (재작성본 v2)
#      - 정사각형 카드, 한 줄 4개 · 기본 최대 2줄(8칸, 초과분은 "+N개 더 보기" 카드로 펼침)
#      - [＋ 메모 등록] → 업체명(선택)·내용 입력 카드 → 등록 시 맨 앞에 추가
#      - 체크박스로 완료 표시(취소선·흐림), 작성자는 [숨김] 처리 가능
#      - [숨김 메모 표시] 체크 시 숨김 메모도 회색 카드로 표시, 작성자는 [복원] 가능
#      - 완료/숨김/복원은 작성자 본인만, 열람은 전 직원 (프로젝트 권한 규칙과 동일)
#      - 데이터: sched_proj_memos [{id,memberId,authorName,vendor,text,done,hidden,createdAt}] — Firebase 동기화 포함

MEMO_CODE = '''  // ─── 프로젝트 포스트잇 메모 (팀 공유, 완료/숨김은 작성자만) ───
  var _pmForm=false, _pmShowHidden=false, _pmShowAll=false;
  function _pmSave(){
    save('sched_proj_memos', projMemos);
    localStorage.setItem('sched_local_ts', Date.now().toString());
    try{ debouncedFbSave(); }catch(_e){}
  }
  function _pmFmtD(ts){ if(!ts) return ''; var d=new Date(ts); return (d.getMonth()+1)+'/'+d.getDate(); }
  window.pmToggleForm = function(on){
    _pmForm = (on===undefined) ? !_pmForm : !!on;
    _pmRender(true);
    if(_pmForm) setTimeout(function(){ var i=document.getElementById('projMemoVendor'); if(i) try{ i.focus(); }catch(_e){} },40);
  };
  window.pmSaveMemo = function(){
    var v=(document.getElementById('projMemoVendor')||{value:''}).value.trim();
    var t=(document.getElementById('projMemoText')||{value:''}).value.trim();
    if(!t){ showInfoModal('메모','내용을 입력해주세요.'); return; }
    var me=members.find(function(x){ return x.id===myMemberId; });
    projMemos.unshift({ id:'pm'+Date.now().toString(36)+Math.random().toString(36).slice(2,6), memberId:myMemberId||'', authorName:(me?me.name:''), vendor:v, text:t, done:false, hidden:false, createdAt:Date.now() });
    _pmForm=false;
    _pmSave(); _pmRender(true);
  };
  window.pmToggleDone = function(id){
    var m=projMemos.find(function(x){ return x.id===id; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)){ _pmRender(true); return; }
    m.done=!m.done;
    _pmSave(); _pmRender(true);
  };
  window.pmHide = function(id){
    var m=projMemos.find(function(x){ return x.id===id; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    m.hidden=true; _pmSave(); _pmRender(true);
  };
  window.pmRestore = function(id){
    var m=projMemos.find(function(x){ return x.id===id; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    m.hidden=false; _pmSave(); _pmRender(true);
  };
  window.pmToggleHidden = function(el){ _pmShowHidden=!!el.checked; _pmShowAll=false; _pmRender(true); };
  window.pmToggleAll = function(){ _pmShowAll=!_pmShowAll; _pmRender(true); };
  function _pmRender(force){
    var box=document.getElementById('projMemoBoard'); if(!box) return;
    if(!force && _pmForm && document.getElementById('projMemoText')) return;   // 작성 중 외부 재렌더 금지
    var list=projMemos.filter(function(m){ return _pmShowHidden ? true : !m.hidden; });
    var CAP=8;
    var shown=list, more=0;
    if(!_pmShowAll && list.length>CAP){ shown=list.slice(0,CAP-1); more=list.length-(CAP-1); }
    var cards=shown.map(function(m){
      var mine=myMemberId && m.memberId===myMemberId;
      var bg=m.hidden?'#f3f4f6':(m.done?'#fdfbe6':'#fff9c4');
      var bd=m.hidden?'#d1d5db':(m.done?'#e8e0a0':'#e6d97a');
      return '<div style="aspect-ratio:1/1;background:'+bg+';border:1px solid '+bd+';box-shadow:0 2px 5px rgba(0,0,0,.07);display:flex;flex-direction:column;padding:10px 11px;min-width:0;'+((m.done||m.hidden)?'opacity:.75;':'')+'">'
        + '<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">'
        +   '<input type="checkbox" '+(m.done?'checked ':'')+(mine?('data-id="'+m.id+'" onchange="pmToggleDone(this.dataset.id)" style="cursor:pointer;'):'disabled style="')+'width:14px;height:14px;accent-color:#1B3A6B;flex-shrink:0" title="완료 표시">'
        +   '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;'+(m.done?'text-decoration:line-through;color:#9ca3af;':'')+'">'+(m.vendor?esc(m.vendor):'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'
        +   (m.hidden?'<span style="flex-shrink:0;font-size:10px;font-weight:700;color:#9ca3af;border:1px solid #d1d5db;padding:1px 5px">숨김</span>':'')
        + '</div>'
        + '<div style="flex:1;min-height:0;overflow:hidden;font-size:12px;line-height:1.55;color:#4b5563;white-space:pre-wrap;word-break:break-all;'+(m.done?'text-decoration:line-through;color:#b0b6bf;':'')+'">'+esc(m.text)+'</div>'
        + '<div style="display:flex;align-items:center;gap:5px;margin-top:6px;font-size:10.5px;color:#a8a26b">'
        +   '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(m.authorName||'')+' &middot; '+_pmFmtD(m.createdAt)+'</span>'
        +   '<span style="flex:1"></span>'
        +   (mine ? (m.hidden
              ? '<button data-id="'+m.id+'" onclick="pmRestore(this.dataset.id)" style="'+_PJ_SBTN+';height:19px;font-size:10.5px;padding:0 6px">복원</button>'
              : '<button data-id="'+m.id+'" onclick="pmHide(this.dataset.id)" title="완료된 메모 숨기기" style="'+_PJ_SBTN+';height:19px;font-size:10.5px;padding:0 6px">숨김</button>') : '')
        + '</div>'
        + '</div>';
    }).join('');
    if(more>0){
      cards += '<div onclick="pmToggleAll()" style="aspect-ratio:1/1;background:#fbfcfe;border:1px dashed #aab8ca;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:12.5px;font-weight:700;color:#5b7ba6" onmouseover="this.style.background=\\'#f4f8fe\\'" onmouseout="this.style.background=\\'#fbfcfe\\'">&#65291;'+more+'개 더 보기</div>';
    } else if(_pmShowAll && list.length>CAP){
      cards += '<div onclick="pmToggleAll()" style="aspect-ratio:1/1;background:#fbfcfe;border:1px dashed #aab8ca;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:12.5px;font-weight:700;color:#5b7ba6" onmouseover="this.style.background=\\'#f4f8fe\\'" onmouseout="this.style.background=\\'#fbfcfe\\'">접기</div>';
    }
    var formCard='';
    if(_pmForm){
      formCard = '<div id="pmFormCard" style="grid-column:1/-1;background:#fffdf0;border:1px solid #e6d97a;padding:11px 12px;display:flex;flex-direction:column;gap:7px">'
        + '<input id="projMemoVendor" type="text" placeholder="업체명 (선택)" style="width:100%;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
        + '<textarea id="projMemoText" placeholder="메모 내용을 적어주세요." style="width:100%;min-height:64px;box-sizing:border-box;padding:7px 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;color:#374151;line-height:1.6;font-family:inherit;resize:vertical;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'"></textarea>'
        + '<div style="display:flex;justify-content:flex-end;gap:6px">'
        +   '<button type="button" onclick="pmToggleForm(false)" style="'+_PJ_SBTN+'">취소</button>'
        +   '<button type="button" onclick="pmSaveMemo()" style="'+_PJ_SBTN+';background:#1a1a1a;border-color:#1a1a1a;color:#fff">등록</button>'
        + '</div>'
        + '</div>';
    }
    box.innerHTML =
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
      + '<span style="font-size:12.5px;font-weight:700;color:#1a1a1a">메모</span>'
      + '<button type="button" onclick="pmToggleForm()" style="'+_PJ_SBTN+'">&#65291; 메모 등록</button>'
      + '<span style="flex:1"></span>'
      + '<label style="display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:#6b7280;cursor:pointer;user-select:none"><input type="checkbox" '+(_pmShowHidden?'checked ':'')+'onchange="pmToggleHidden(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 메모 표시</label>'
      + '</div>'
      + ((cards||formCard) ? ('<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">'+formCard+cards+'</div>') : '<div style="text-align:center;padding:12px;border:1px dashed #d6deea;color:#b6bec9;font-size:12px">등록된 메모가 없습니다. [&#65291; 메모 등록]으로 첫 메모를 남겨보세요.</div>');
  }
'''

R85_EDITS = [
("""      <div id="projectList" style="display:flex;flex-direction:column;gap:8px"></div>""",
 """      <div id="projMemoBoard" style="margin-bottom:12px"></div>
      <div id="projectList" style="display:flex;flex-direction:column;gap:8px"></div>"""),
("""  let clientInfo = _cliDecMap(load('sched_client_info') ?? {});""",
 """  let clientInfo = _cliDecMap(load('sched_client_info') ?? {});
  let projMemos = load('sched_proj_memos') ?? [];   // 프로젝트 포스트잇 메모 [{id,memberId,authorName,vendor,text,done,hidden,createdAt}]"""),
("""    clientInfo       = _cliDecMap(load('sched_client_info') ?? {});""",
 """    clientInfo       = _cliDecMap(load('sched_client_info') ?? {});
    projMemos        = load('sched_proj_memos') ?? [];"""),
("""        sched_client_info: _cliEncMap(clientInfo),""",
 """        sched_client_info: _cliEncMap(clientInfo),
        sched_proj_memos: projMemos,"""),
("""      sched_projects: projectsList, sched_client_info: clientInfo""",
 """      sched_projects: projectsList, sched_client_info: clientInfo, sched_proj_memos: projMemos"""),
("""    if(_projMode.view==='list') _projRenderList();
    else _projRenderForm();""",
 """    if(_projMode.view==='list'){ _projRenderList(); _pmRender(); }
    else _projRenderForm();"""),
("""  function _projRenderForm(){""",
 MEMO_CODE + """  function _projRenderForm(){"""),
]

KEYS_OLD = ",'sched_client_list','sched_projects','sched_client_info']"
KEYS_NEW = ",'sched_client_list','sched_projects','sched_client_info','sched_proj_memos']"

def apply_r85(s, path):
    for i,(old,new) in enumerate(R85_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R85 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    exp = 3 if 'testpage' in path else 2
    n = s.count(KEYS_OLD)
    if n != exp: raise SystemExit('R85 FAIL %s KEYS count %d (expect %d)' % (path, n, exp))
    return s.replace(KEYS_OLD, KEYS_NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r85(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r84 2026-08-18 -->') == 1
            s = s.replace('<!-- test build r84 2026-08-18 -->', '<!-- test build r85 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
