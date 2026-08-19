# -*- coding: utf-8 -*-
# r87: 포스트잇 메모 개편. (재작성본 v2)
#      - 메모 등록 버튼 → 툴바의 아이콘(주황 메모지, 프로젝트 등록 옆)으로 이동
#      - 숨김 메모 표시 체크박스 → 툴바 직원 필터 옆으로 이동
#      - 메모 구조 변경: 업체명(제목) + 내용 여러 줄(items), 완료 체크는 각 내용 줄에
#      - 각 내용 줄에 작성 날짜 자동 기록·표시 (M/D)
#      - 등록창: 내용 줄 계속 추가 가능 (＋ 내용 추가), 줄 삭제(휴지통)
#      - 작성자 본인 수정(연필)·삭제(휴지통, 확인 모달) 가능
#      - 한 줄 5개 정사각형, 기본 최대 2줄(10칸, 초과분 "+N개 더 보기")
#      - 구버전 데이터({text,done}) 자동 마이그레이션 → items 1줄

START_MEMO = "  // ─── 프로젝트 포스트잇 메모 (팀 공유, 완료/숨김은 작성자만) ───"
END_MEMO = "  function _projRenderForm(){"

NEW_MEMO = '''  // ─── 프로젝트 포스트잇 메모 (팀 공유, 완료/숨김/수정/삭제는 작성자만) ───
  var _pmForm=false, _pmEditId=null, _pmShowHidden=false, _pmShowAll=false;
  function _pmNormList(list){
    return (Array.isArray(list)?list:[]).map(function(m){
      if(m && !Array.isArray(m.items)){
        var d=m.createdAt?new Date(m.createdAt):new Date();
        var ds=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
        m.items=[{ id:'pi'+(m.id||'m')+'0', text:String(m.text||''), done:!!m.done, date:ds }];
        delete m.text; delete m.done;
      }
      return m;
    });
  }
  function _pmSave(){
    save('sched_proj_memos', projMemos);
    localStorage.setItem('sched_local_ts', Date.now().toString());
    try{ debouncedFbSave(); }catch(_e){}
  }
  function _pmFmtD(ts){ if(!ts) return ''; var d=new Date(ts); return (d.getMonth()+1)+'/'+d.getDate(); }
  function _pmFmtDs(ds){ if(!ds) return ''; var p=String(ds).split('-'); return p.length===3 ? (Number(p[1])+'/'+Number(p[2])) : String(ds); }
  window.pmToggleForm = function(on){
    var next = (on===undefined) ? !_pmForm : !!on;
    if(!next) _pmEditId=null;
    _pmForm = next;
    _pmRender(true);
    if(_pmForm) setTimeout(function(){ var i=document.getElementById('projMemoVendor'); if(i) try{ i.focus(); }catch(_e){} },40);
  };
  window.pmEditStart = function(id){
    var m=projMemos.find(function(x){ return x.id===id; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    _pmEditId=id; _pmForm=true;
    _pmRender(true);
    setTimeout(function(){ var i=document.getElementById('projMemoVendor'); if(i) try{ i.focus(); }catch(_e){} },40);
  };
  window.pmDelete = function(id){
    var m=projMemos.find(function(x){ return x.id===id; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)) return;
    showConfirmModal('메모 삭제', (m.vendor?esc(m.vendor)+' ':'')+'메모를 삭제할까요?\\n삭제하면 되돌릴 수 없습니다. (보관만 하려면 숨김을 사용하세요)', function(){
      projMemos=projMemos.filter(function(x){ return x.id!==id; });
      if(_pmEditId===id){ _pmEditId=null; _pmForm=false; }
      _pmSave(); _pmRender(true);
    }, '삭제', '#dc2626');
  };
  window.pmAddItemRow = function(){
    var box=document.getElementById('pmItemRows'); if(!box) return;
    var d=document.createElement('div'); d.innerHTML=_pmItemRowHtml({});
    var row=d.firstChild; box.appendChild(row);
    try{ row.querySelector('.pm-item-text').focus(); }catch(_e){}
  };
  window.pmDelItemRow = function(btn){
    var box=document.getElementById('pmItemRows'); if(!box) return;
    var row=btn.closest('.pm-item-row'); if(!row) return;
    if(box.querySelectorAll('.pm-item-row').length<=1){ row.querySelector('.pm-item-text').value=''; return; }
    row.remove();
  };
  function _pmItemRowHtml(it){
    it=it||{};
    return '<div class="pm-item-row" data-iid="'+esc(it.id||'')+'" data-done="'+(it.done?'1':'0')+'" data-date="'+esc(it.date||'')+'" style="display:flex;gap:6px;align-items:center">'
      + '<input type="text" class="pm-item-text" value="'+esc(it.text||'')+'" placeholder="할 일 / 내용" style="flex:1;min-width:0;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;color:#374151;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
      + (it.date?('<span style="flex-shrink:0;font-size:11px;color:#9ca3af">'+esc(_pmFmtDs(it.date))+'</span>'):'')
      + '<button type="button" onclick="pmDelItemRow(this)" title="줄 삭제" style="flex-shrink:0;border:none;background:none;cursor:pointer;padding:2px 3px;color:#dc2626;display:inline-flex;align-items:center" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'
      + '</div>';
  }
  window.pmSaveMemo = function(){
    var v=(document.getElementById('projMemoVendor')||{value:''}).value.trim();
    var rows=document.querySelectorAll('#pmItemRows .pm-item-row');
    var items=[];
    for(var i=0;i<rows.length;i++){
      var tx=(rows[i].querySelector('.pm-item-text').value||'').trim();
      if(!tx) continue;
      items.push({ id: rows[i].dataset.iid || ('pi'+Date.now().toString(36)+Math.random().toString(36).slice(2,5)+i),
                   text: tx, done: rows[i].dataset.done==='1',
                   date: rows[i].dataset.date || dk(new Date()) });
    }
    if(!items.length){ showInfoModal('메모','내용을 한 줄 이상 입력해주세요.'); return; }
    if(_pmEditId){
      var m=projMemos.find(function(x){ return x.id===_pmEditId; });
      if(m && myMemberId && m.memberId===myMemberId){ m.vendor=v; m.items=items; }
      _pmEditId=null;
    } else {
      var me=members.find(function(x){ return x.id===myMemberId; });
      projMemos.unshift({ id:'pm'+Date.now().toString(36)+Math.random().toString(36).slice(2,6), memberId:myMemberId||'', authorName:(me?me.name:''), vendor:v, items:items, hidden:false, createdAt:Date.now() });
    }
    _pmForm=false;
    _pmSave(); _pmRender(true);
  };
  window.pmToggleDone = function(mid, iid){
    var m=projMemos.find(function(x){ return x.id===mid; }); if(!m) return;
    if(!(myMemberId && m.memberId===myMemberId)){ _pmRender(true); return; }
    var it=(m.items||[]).find(function(x){ return x.id===iid; }); if(!it) return;
    it.done=!it.done;
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
  window.pmVendorSearch = function(el){
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
    var t=document.querySelector('#pmItemRows .pm-item-text'); if(t) setTimeout(function(){ try{ t.focus(); }catch(_e){} },20);
  };
  window.pmVendorBlur = function(){ setTimeout(function(){ var b=document.getElementById('pmVendorSug'); if(b) b.style.display='none'; },150); };
  function _pmRender(force){
    var box=document.getElementById('projMemoBoard'); if(!box) return;
    if(!force && _pmForm && document.getElementById('pmItemRows')) return;   // 작성 중 외부 재렌더 금지
    var list=projMemos.filter(function(m){ return _pmShowHidden ? true : !m.hidden; });
    var CAP=10;
    var shown=list, more=0;
    if(!_pmShowAll && list.length>CAP){ shown=list.slice(0,CAP-1); more=list.length-(CAP-1); }
    var cards=shown.map(function(m){
      var mine=myMemberId && m.memberId===myMemberId;
      var its=m.items||[];
      var allDone=its.length>0 && its.every(function(x){ return x.done; });
      var bg=m.hidden?'#f3f4f6':(allDone?'#fdfbe6':'#fff9c4');
      var bd=m.hidden?'#d1d5db':(allDone?'#e8e0a0':'#e6d97a');
      var itemsHtml=its.map(function(it){
        return '<div style="display:flex;align-items:flex-start;gap:5px;margin-bottom:3px">'
          + '<input type="checkbox" '+(it.done?'checked ':'')+(mine?('data-mid="'+m.id+'" data-iid="'+esc(it.id)+'" onchange="pmToggleDone(this.dataset.mid,this.dataset.iid)" style="cursor:pointer;'):'disabled style="')+'width:13px;height:13px;accent-color:#1B3A6B;flex-shrink:0;margin-top:2px" title="완료 표시">'
          + '<span style="flex:1;min-width:0;font-size:12px;line-height:1.5;color:#4b5563;word-break:break-all;'+(it.done?'text-decoration:line-through;color:#b0b6bf;':'')+'">'+esc(it.text)+'<span style="font-size:10px;color:#b6a94f;margin-left:4px;white-space:nowrap;text-decoration:none;display:inline-block">'+_pmFmtDs(it.date)+'</span></span>'
          + '</div>';
      }).join('');
      return '<div style="aspect-ratio:1/1;background:'+bg+';border:1px solid '+bd+';box-shadow:0 2px 5px rgba(0,0,0,.07);display:flex;flex-direction:column;padding:9px 10px;min-width:0;'+((allDone||m.hidden)?'opacity:.75;':'')+'">'
        + '<div style="display:flex;align-items:center;gap:5px;margin-bottom:5px;flex-shrink:0">'
        +   '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;'+(allDone?'text-decoration:line-through;color:#9ca3af;':'')+'">'+(m.vendor?esc(m.vendor):'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'
        +   (m.hidden?'<span style="flex-shrink:0;font-size:10px;font-weight:700;color:#9ca3af;border:1px solid #d1d5db;padding:1px 5px">숨김</span>':'')
        + '</div>'
        + '<div style="flex:1;min-height:0;overflow:auto">'+itemsHtml+'</div>'
        + '<div style="display:flex;align-items:center;gap:3px;margin-top:5px;font-size:10.5px;color:#a8a26b;flex-shrink:0">'
        +   '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(m.authorName||'')+' &middot; '+_pmFmtD(m.createdAt)+'</span>'
        +   '<span style="flex:1"></span>'
        +   (mine ? (
              '<button data-id="'+m.id+'" onclick="pmEditStart(this.dataset.id)" title="수정" style="border:none;background:none;cursor:pointer;padding:1px 2px;color:#5b7ba6;display:inline-flex;align-items:center;flex-shrink:0" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#5b7ba6\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px;display:block"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg></button>'
            + '<button data-id="'+m.id+'" onclick="pmDelete(this.dataset.id)" title="삭제" style="border:none;background:none;cursor:pointer;padding:1px 2px;color:#dc2626;display:inline-flex;align-items:center;flex-shrink:0" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'
            + (m.hidden
              ? '<button data-id="'+m.id+'" onclick="pmRestore(this.dataset.id)" style="'+_PJ_SBTN+';height:19px;font-size:10.5px;padding:0 6px;flex-shrink:0">복원</button>'
              : '<button data-id="'+m.id+'" onclick="pmHide(this.dataset.id)" title="메모 숨기기 (숨김 메모 표시로 다시 볼 수 있음)" style="'+_PJ_SBTN+';height:19px;font-size:10.5px;padding:0 6px;flex-shrink:0">숨김</button>')) : '')
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
      var em=_pmEditId?projMemos.find(function(x){ return x.id===_pmEditId; }):null;
      var rowsHtml=(em&&em.items&&em.items.length)?em.items.map(_pmItemRowHtml).join(''):_pmItemRowHtml({});
      formCard = '<div id="pmFormCard" style="grid-column:1/-1;background:#fffdf0;border:1px solid #e6d97a;padding:11px 12px;display:flex;flex-direction:column;gap:7px">'
        + (em?('<div style="font-size:11.5px;font-weight:700;color:#b45309">메모 수정</div>'):'')
        + '<div style="position:relative">'
        + '<input id="projMemoVendor" type="text" value="'+esc(em?em.vendor||'':'')+'" placeholder="업체명 (선택) &mdash; 입력하면 업체 목록에서 선택할 수 있습니다" autocomplete="off" oninput="pmVendorSearch(this)" style="width:100%;height:28px;box-sizing:border-box;padding:0 9px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none;background:#fff" onfocus="this.style.borderColor=\\'#1B3A6B\\';pmVendorSearch(this)" onblur="this.style.borderColor=\\'#c8d2de\\';pmVendorBlur()">'
        + '<div id="pmVendorSug" style="display:none;position:absolute;top:100%;left:0;right:0;z-index:60;background:#fff;border:1px solid #c8d2de;max-height:200px;overflow:auto;box-shadow:0 8px 22px rgba(15,23,42,.14)"></div>'
        + '</div>'
        + '<div id="pmItemRows" style="display:flex;flex-direction:column;gap:6px">'+rowsHtml+'</div>'
        + '<div style="display:flex;align-items:center;gap:6px">'
        +   '<button type="button" onclick="pmAddItemRow()" style="'+_PJ_SBTN+';color:#1B3A6B;border-color:#1B3A6B">&#65291; 내용 추가</button>'
        +   '<span style="flex:1"></span>'
        +   '<button type="button" onclick="pmToggleForm(false)" style="'+_PJ_SBTN+'">취소</button>'
        +   '<button type="button" onclick="pmSaveMemo()" style="'+_PJ_SBTN+';background:#1a1a1a;border-color:#1a1a1a;color:#fff">'+(em?'저장':'등록')+'</button>'
        + '</div>'
        + '</div>';
    }
    box.innerHTML = (cards||formCard)
      ? ('<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px">'+formCard+cards+'</div>')
      : '';
  }
'''

R87_EDITS = [
("""        <select id="projMemberFilter" class="q-flat" onchange="projFilterMember(this.value)" style="width:120px;flex:0 0 auto;background:#fff;color:#1a1a1a;cursor:pointer"></select>
        <span style="flex:1"></span>
        <button class="qic" id="btnProjectAdd" onclick="openProjectNew()" data-tip="프로젝트 등록" aria-label="프로젝트 등록" style="border-color:#1B3A6B;color:#1B3A6B"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></button>""",
 """        <select id="projMemberFilter" class="q-flat" onchange="projFilterMember(this.value)" style="width:120px;flex:0 0 auto;background:#fff;color:#1a1a1a;cursor:pointer"></select>
        <label style="display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:#6b7280;cursor:pointer;user-select:none;white-space:nowrap;margin-left:10px;flex:0 0 auto"><input type="checkbox" onchange="pmToggleHidden(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 메모 표시</label>
        <span style="flex:1"></span>
        <button class="qic" id="btnMemoAdd" onclick="pmToggleForm()" data-tip="메모 등록" aria-label="메모 등록" style="border-color:#d97706;color:#d97706"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h9.5L21 14.5V5a2 2 0 0 0-2-2Z"/><path d="M15 21v-5a2 2 0 0 1 2-2h4"/></svg></button>
        <span class="qic-div" style="width:1px;align-self:stretch;background:#d3dae4;margin:2px 4px"></span>
        <button class="qic" id="btnProjectAdd" onclick="openProjectNew()" data-tip="프로젝트 등록" aria-label="프로젝트 등록" style="border-color:#1B3A6B;color:#1B3A6B"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></button>"""),

("""  let projMemos = load('sched_proj_memos') ?? [];   // 프로젝트 포스트잇 메모 [{id,memberId,authorName,vendor,text,done,hidden,createdAt}]""",
 """  let projMemos = _pmNormList(load('sched_proj_memos') ?? []);   // 프로젝트 포스트잇 메모 [{id,memberId,authorName,vendor,items:[{id,text,done,date}],hidden,createdAt}]"""),

("""    projMemos        = load('sched_proj_memos') ?? [];""",
 """    projMemos        = _pmNormList(load('sched_proj_memos') ?? []);"""),
]

def apply_r87(s, path):
    for i,(old,new) in enumerate(R87_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R87 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    n1 = s.count(START_MEMO); n2 = s.count(END_MEMO)
    if n1 != 1 or n2 != 1: raise SystemExit('R87 FAIL %s memo slice counts %d %d' % (path, n1, n2))
    a = s.index(START_MEMO)
    b = s.index(END_MEMO, a)
    return s[:a] + NEW_MEMO + s[b:]

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r87(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r86 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r86 2026-08-19 -->', '<!-- test build r87 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
