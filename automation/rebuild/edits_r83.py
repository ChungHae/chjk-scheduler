# -*- coding: utf-8 -*-
# r83: 프로젝트 세부 정보 개선. (재작성본 v2)
#      1) [세부 정보] 버튼을 프로젝트 명 왼쪽으로 이동
#      2) 프로젝트 명 입력칸 높이를 버튼 높이(28px)로 축소
#      3) 세부 정보 '내용' 작성칸 높이 3배 (56px→168px)
#      4) 등록 완료 후에도 펼침 화면에서 세부 정보 수정/추가 가능

R83_EDITS = [
# 1+2. 제목 줄: 버튼을 왼쪽으로, 입력칸 높이 28px
("""      + '<div style="padding:12px 14px;border-bottom:1px solid #e3e9f0;display:flex;gap:8px;align-items:center">'
      +   '<input id="projTitleInput" type="text" placeholder="프로젝트 명" maxlength="120" style="flex:1;min-width:0;box-sizing:border-box;padding:8px 10px;border:1px solid #c8d2de;border-radius:0;font-size:13.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
      +   '<button type="button" id="btnProjDetail" onclick="projDetailToggle()" style="'+_PJ_BTN+';background:#fff;color:#1B3A6B;border:1px solid #1B3A6B;flex-shrink:0">세부 정보</button>'
      + '</div>'""",
 """      + '<div style="padding:12px 14px;border-bottom:1px solid #e3e9f0;display:flex;gap:8px;align-items:center">'
      +   '<button type="button" id="btnProjDetail" onclick="projDetailToggle()" style="'+_PJ_BTN+';background:#fff;color:#1B3A6B;border:1px solid #1B3A6B;flex-shrink:0">세부 정보</button>'
      +   '<input id="projTitleInput" type="text" placeholder="프로젝트 명" maxlength="120" style="flex:1;min-width:0;height:28px;box-sizing:border-box;padding:0 10px;border:1px solid #c8d2de;border-radius:0;font-size:13px;font-weight:700;color:#14305c;font-family:inherit;outline:none" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
      + '</div>'"""),

# 3. 내용 칸 높이 3배
("""'+LB+'">내용</span><textarea oninput="pjdNoteInput(this)" style="width:100%;min-height:56px;""",
 """'+LB+'">내용</span><textarea oninput="pjdNoteInput(this)" style="width:100%;min-height:168px;"""),

# 4a. 렌더 대상 전환 변수 + 상태 변수
("""  var _pjD = null;
  function _pjDReset(){ _pjD = { open:false, vendors:[], parent:'', equip:'', note:'' }; }""",
 """  var _pjD = null;
  var _pjDTargetId = 'projDetailBody';   // 폼/펼침수정 어느 쪽에 그릴지
  var _pjDEditFor = null;                // 펼침 화면에서 세부 정보 수정 중인 프로젝트 id
  function _pjDReset(){ _pjD = { open:false, vendors:[], parent:'', equip:'', note:'' }; }"""),

# 4b. 폼 토글 시 렌더 대상을 폼으로
("""  window.projDetailToggle = function(){
    if(!_pjD) _pjDReset();""",
 """  window.projDetailToggle = function(){
    _pjDTargetId='projDetailBody';
    if(!_pjD) _pjDReset();"""),

# 4c. _pjDRender 대상 교체
("""    var w=document.getElementById('projDetailBody'); if(!w || !_pjD) return;""",
 """    var w=document.getElementById(_pjDTargetId); if(!w || !_pjD) return;"""),

# 4d. 펼침 화면 수정 시작/저장/취소 함수
("""  function _pjDRender(){""",
 """  function _pjDDetSnapshot(){
    if(!_pjD) return null;
    var _dv=_pjD.vendors.map(function(v){
      var _cs=(_clxInfo(v.name).contacts)||[];
      return { name:v.name, contacts:v.sel.map(function(i){ var c=_cs[i]||{}; return { name:String(c.name||''), rank:String(c.rank||''), phone:String(c.phone||c.phone2||'') }; }).filter(function(c){ return c.name||c.phone; }) };
    });
    var _dp=String(_pjD.parent||'').trim(), _de=String(_pjD.equip||'').trim(), _dn=String(_pjD.note||'').trim();
    return (_dv.length||_dp||_de||_dn) ? { vendors:_dv, parent:_dp, equip:_de, note:_dn } : null;
  }
  window.projDetailEditStart = function(pid){
    var p=projectsList.find(function(x){ return x.id===pid; }); if(!p) return;
    if(!(myMemberId && p.memberId===myMemberId)) return;
    _pjDReset(); _pjD.open=true;
    var det=p.detail||{};
    _pjD.parent=det.parent||''; _pjD.equip=det.equip||''; _pjD.note=det.note||'';
    (det.vendors||[]).forEach(function(v){
      var cs=(_clxInfo(v.name).contacts)||[];
      var sel=[];
      (v.contacts||[]).forEach(function(sc){
        for(var ci=0;ci<cs.length;ci++){
          if(sel.indexOf(ci)>=0) continue;
          var c=cs[ci];
          if(String(c.name||'')===String(sc.name||'') && (String(c.phone||c.phone2||'')===String(sc.phone||'') || String(c.rank||'')===String(sc.rank||''))){ sel.push(ci); break; }
        }
      });
      _pjD.vendors.push({ name:v.name, sel:sel });
    });
    _pjDEditFor=pid;
    _pjDTargetId='projDetailBody2';
    _projRenderList();
    setTimeout(function(){ _pjDRender(); },30);
  };
  window.projDetailEditSave = function(pid){
    var p=projectsList.find(function(x){ return x.id===pid; }); if(!p||!_pjD) return;
    var det=_pjDDetSnapshot();
    if(det) p.detail=det; else delete p.detail;
    p.updatedAt=Date.now();
    _projSave();
    _pjDEditFor=null;
    _projRenderList();
  };
  window.projDetailEditCancel = function(){ _pjDEditFor=null; _projRenderList(); };
  function _pjDRender(){"""),

# 4e. 등록 저장도 스냅샷 헬퍼 사용 (중복 로직 제거)
("""    if(_pjD){
      var _dv=_pjD.vendors.map(function(v){
        var _cs=(_clxInfo(v.name).contacts)||[];
        return { name:v.name, contacts:v.sel.map(function(i){ var c=_cs[i]||{}; return { name:String(c.name||''), rank:String(c.rank||''), phone:String(c.phone||c.phone2||'') }; }).filter(function(c){ return c.name||c.phone; }) };
      });
      var _dp=String(_pjD.parent||'').trim(), _de=String(_pjD.equip||'').trim(), _dn=String(_pjD.note||'').trim();
      if(_dv.length||_dp||_de||_dn) np.detail={ vendors:_dv, parent:_dp, equip:_de, note:_dn };
    }""",
 """    if(_pjD){
      var _npDet=_pjDDetSnapshot();
      if(_npDet) np.detail=_npDet;
    }"""),

# 4f. 펼침 패널: 수정 모드 / 표시+연필 / 추가 버튼
("""  function _projPanelHtml(p, mine){
    var _det=p.detail, _detHtml='';
    if(_det && ((_det.vendors&&_det.vendors.length)||_det.parent||_det.equip||_det.note)){
      var _R=function(k,v){ return v?('<div style="display:flex;gap:10px;font-size:12.5px;line-height:1.7"><span style="flex-shrink:0;width:44px;font-weight:700;color:#5b7ba6">'+k+'</span><span style="color:#374151;min-width:0">'+v+'</span></div>'):''; };
      var _vh=(_det.vendors||[]).map(function(v){
        var _cc=(v.contacts||[]).map(function(c){ return esc(c.name)+(c.rank?' '+esc(c.rank):'')+(c.phone?' ('+esc(c.phone)+')':''); }).join(', ');
        return '<b style="color:#14305c">'+esc(v.name)+'</b>'+(_cc?' &mdash; '+_cc:'');
      }).join('<br>');
      _detHtml='<div style="margin:10px 14px 2px;padding:10px 12px;background:#f8fafc;border:1px solid #e3e9f0;display:flex;flex-direction:column;gap:3px">'
        + _R('업체명', _vh) + _R('모기업', esc(_det.parent||'')) + _R('장비명', esc(_det.equip||'')) + _R('내용', esc(_det.note||'').replace(/\\n/g,'<br>'))
        + '</div>';
    }
    var logs = _projLogsView(_projDraft.logs);""",
 """  function _projPanelHtml(p, mine){
    var _det=p.detail, _detHtml='';
    var _hasDet=!!(_det && ((_det.vendors&&_det.vendors.length)||_det.parent||_det.equip||_det.note));
    if(_pjDEditFor===p.id && mine){
      _detHtml='<div style="margin:10px 14px 2px;padding:12px;background:#fbfcfe;border:1px solid #d8e1ec">'
        + '<div style="display:flex;align-items:center;margin-bottom:9px"><span style="font-size:12px;font-weight:700;color:#1a1a1a">세부 정보 수정</span><span style="flex:1"></span>'
        + '<button type="button" onclick="projDetailEditCancel()" style="'+_PJ_SBTN+'">취소</button>'
        + '<button type="button" data-pid="'+p.id+'" onclick="projDetailEditSave(this.dataset.pid)" style="'+_PJ_SBTN+';background:#1a1a1a;border-color:#1a1a1a;color:#fff;margin-left:6px">저장</button></div>'
        + '<div id="projDetailBody2"></div></div>';
    } else if(_hasDet){
      var _R=function(k,v){ return v?('<div style="display:flex;gap:10px;font-size:12.5px;line-height:1.7"><span style="flex-shrink:0;width:44px;font-weight:700;color:#5b7ba6">'+k+'</span><span style="color:#374151;min-width:0">'+v+'</span></div>'):''; };
      var _vh=(_det.vendors||[]).map(function(v){
        var _cc=(v.contacts||[]).map(function(c){ return esc(c.name)+(c.rank?' '+esc(c.rank):'')+(c.phone?' ('+esc(c.phone)+')':''); }).join(', ');
        return '<b style="color:#14305c">'+esc(v.name)+'</b>'+(_cc?' &mdash; '+_cc:'');
      }).join('<br>');
      _detHtml='<div style="margin:10px 14px 2px;padding:10px 12px;background:#f8fafc;border:1px solid #e3e9f0;display:flex;flex-direction:column;gap:3px;position:relative">'
        + (mine?('<button type="button" data-pid="'+p.id+'" onclick="projDetailEditStart(this.dataset.pid)" title="세부 정보 수정" style="position:absolute;top:7px;right:7px;border:none;background:none;cursor:pointer;padding:2px 3px;color:#5b7ba6;display:inline-flex;align-items:center" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#5b7ba6\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg></button>'):'')
        + _R('업체명', _vh) + _R('모기업', esc(_det.parent||'')) + _R('장비명', esc(_det.equip||'')) + _R('내용', esc(_det.note||'').replace(/\\n/g,'<br>'))
        + '</div>';
    } else if(mine){
      _detHtml='<div style="margin:10px 14px 2px"><button type="button" data-pid="'+p.id+'" onclick="projDetailEditStart(this.dataset.pid)" style="'+_PJ_SBTN+'">&#65291; 세부 정보 추가</button></div>';
    }
    var logs = _projLogsView(_projDraft.logs);"""),
]

def apply_r83(s, path):
    for i,(old,new) in enumerate(R83_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R83 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r83(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r82 2026-08-14 -->') == 1
            s = s.replace('<!-- test build r82 2026-08-14 -->', '<!-- test build r83 2026-08-14 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
