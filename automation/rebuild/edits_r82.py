# -*- coding: utf-8 -*-
# r82: 프로젝트 등록창 '세부 정보' (선택 입력) 추가. (재작성본 v2)
#      - 프로젝트 명 옆 [세부 정보] 버튼 → 아래로 입력 영역 토글
#      - 업체명: 업체관리 목록에서 검색·복수 선택(칩), 선택 업체마다 담당자 선택 영역 생성
#      - 담당자: 업체 상세의 담당자들 중 복수 선택, "이름 직급 (연락처)" 형식 표기
#      - 모기업 / 장비명 / 내용 자유 입력
#      - 저장 시 project.detail = {vendors:[{name,contacts:[{name,rank,phone}]}],parent,equip,note}
#      - 목록 펼침 상세 상단에 세부 정보 표시

import io

HELPERS = r'''  // ─── 프로젝트 세부 정보 (선택 입력) ───
  var _pjD = null;
  function _pjDReset(){ _pjD = { open:false, vendors:[], parent:'', equip:'', note:'' }; }
  function _pjDFmtContact(c){
    var s=String((c&&c.name)||'').trim();
    var rk=String((c&&c.rank)||'').trim();
    if(rk) s+=(s?' ':'')+rk;
    var ph=String((c&&c.phone)||'').trim()||String((c&&c.phone2)||'').trim();
    if(ph) s+=(s?' ':'')+'('+ph+')';
    return s||'(이름 없음)';
  }
  window.projDetailToggle = function(){
    if(!_pjD) _pjDReset();
    _pjD.open=!_pjD.open;
    var w=document.getElementById('projDetailWrap'); if(!w) return;
    w.style.display=_pjD.open?'':'none';
    var b=document.getElementById('btnProjDetail');
    if(b){ b.style.background=_pjD.open?'#1B3A6B':'#fff'; b.style.color=_pjD.open?'#fff':'#1B3A6B'; }
    if(_pjD.open){ _pjDRender(); setTimeout(function(){ var i=document.getElementById('pjdVendorInput'); if(i) try{ i.focus(); }catch(_e){} },40); }
  };
  window.pjdParentInput=function(el){ if(_pjD) _pjD.parent=el.value; };
  window.pjdEquipInput=function(el){ if(_pjD) _pjD.equip=el.value; };
  window.pjdNoteInput=function(el){ if(_pjD) _pjD.note=el.value; };
  window.pjdVendorSearch=function(el){
    var box=document.getElementById('pjdVendorSug'); if(!box) return;
    var q=String(el.value||'').trim().toLowerCase();
    if(!q){ box.style.display='none'; box.innerHTML=''; return; }
    try{ ensureClientList(); }catch(_e){}
    var hit=allClients().filter(function(c){ return String(c[0]).toLowerCase().indexOf(q)>=0 && !_pjD.vendors.some(function(v){ return v.name===c[0]; }); }).slice(0,30);
    if(!hit.length){ box.style.display='none'; box.innerHTML=''; return; }
    box.innerHTML=hit.map(function(c){ return '<div onmousedown="pjdVendorAdd(this.dataset.nm)" data-nm="'+esc(c[0])+'" style="padding:7px 10px;cursor:pointer;font-size:12.5px;color:#374151;border-bottom:1px solid #f1f5f9" onmouseover="this.style.background=\'#f4f8fe\'" onmouseout="this.style.background=\'\'">'+esc(c[0])+'</div>'; }).join('');
    box.style.display='block';
  };
  window.pjdVendorBlur=function(){ setTimeout(function(){ var b=document.getElementById('pjdVendorSug'); if(b) b.style.display='none'; },150); };
  window.pjdVendorAdd=function(nm){
    if(!_pjD) _pjDReset();
    if(!nm || _pjD.vendors.some(function(v){ return v.name===nm; })) return;
    _pjD.vendors.push({ name:nm, sel:[] });
    _pjDRender();
    setTimeout(function(){ var i=document.getElementById('pjdVendorInput'); if(i){ i.value=''; try{ i.focus(); }catch(_e){} } },20);
  };
  window.pjdVendorDel=function(nm){
    if(!_pjD) return;
    _pjD.vendors=_pjD.vendors.filter(function(v){ return v.name!==nm; });
    _pjDRender();
  };
  window.pjdContactToggle=function(nm, idx){
    if(!_pjD) return;
    var v=_pjD.vendors.find(function(x){ return x.name===nm; }); if(!v) return;
    idx=Number(idx);
    var p=v.sel.indexOf(idx);
    if(p>=0) v.sel.splice(p,1); else v.sel.push(idx);
    _pjDRender();
  };
  function _pjDRender(){
    var w=document.getElementById('projDetailBody'); if(!w || !_pjD) return;
    var IN='width:100%;box-sizing:border-box;height:30px;padding:0 8px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;color:#374151;font-family:inherit;outline:none;background:#fff';
    var LB='font-size:11px;font-weight:700;color:#5b7ba6';
    var chips=_pjD.vendors.map(function(v){
      return '<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 9px;background:#f4f8fe;border:1px solid #aac4e6;font-size:12px;color:#14305c;font-weight:600">'+esc(v.name)
        + '<span data-nm="'+esc(v.name)+'" onclick="pjdVendorDel(this.dataset.nm)" title="선택 해제" style="cursor:pointer;color:#8b97a5;font-weight:700;line-height:1" onmouseover="this.style.color=\'#dc2626\'" onmouseout="this.style.color=\'#8b97a5\'">&#10005;</span></span>';
    }).join('');
    var conts=_pjD.vendors.map(function(v){
      var inf=_clxInfo(v.name); var cs=(inf.contacts||[]);
      var inner;
      if(!cs.length){ inner='<span style="font-size:12px;color:#b6bec9">업체 관리에 등록된 담당자가 없습니다</span>'; }
      else inner=cs.map(function(c,i){
        var on=v.sel.indexOf(i)>=0;
        return '<span data-nm="'+esc(v.name)+'" data-i="'+i+'" onclick="pjdContactToggle(this.dataset.nm, this.dataset.i)" style="display:inline-flex;align-items:center;padding:4px 10px;border:1px solid '+(on?'#1B3A6B':'#c8d2de')+';background:'+(on?'#1B3A6B':'#fff')+';color:'+(on?'#fff':'#374151')+';font-size:12px;cursor:pointer;user-select:none">'+esc(_pjDFmtContact(c))+'</span>';
      }).join('');
      return '<div style="display:flex;flex-direction:column;gap:5px"><span style="'+LB+'">담당자 &middot; '+esc(v.name)+'</span><div style="display:flex;flex-wrap:wrap;gap:6px">'+inner+'</div></div>';
    }).join('');
    w.innerHTML =
      '<div style="display:flex;flex-direction:column;gap:11px">'
      + '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">'
      +   '<div style="display:flex;flex-direction:column;gap:3px;position:relative"><span style="'+LB+'">업체명</span>'
      +     '<input id="pjdVendorInput" placeholder="업체명 검색 후 선택 (여러 업체 가능)" autocomplete="off" oninput="pjdVendorSearch(this)" onfocus="pjdVendorSearch(this)" onblur="pjdVendorBlur()" style="'+IN+'" onfocusin="this.style.borderColor=\'#1B3A6B\'" onfocusout="this.style.borderColor=\'#c8d2de\'">'
      +     '<div id="pjdVendorSug" style="display:none;position:absolute;top:100%;left:0;right:0;z-index:60;background:#fff;border:1px solid #c8d2de;max-height:220px;overflow:auto;box-shadow:0 8px 22px rgba(15,23,42,.14)"></div>'
      +   '</div>'
      +   '<div style="display:flex;flex-direction:column;gap:3px"><span style="'+LB+'">모기업</span><input value="'+esc(_pjD.parent)+'" oninput="pjdParentInput(this)" style="'+IN+'" onfocus="this.style.borderColor=\'#1B3A6B\'" onblur="this.style.borderColor=\'#c8d2de\'"></div>'
      +   '<div style="display:flex;flex-direction:column;gap:3px"><span style="'+LB+'">장비명</span><input value="'+esc(_pjD.equip)+'" oninput="pjdEquipInput(this)" style="'+IN+'" onfocus="this.style.borderColor=\'#1B3A6B\'" onblur="this.style.borderColor=\'#c8d2de\'"></div>'
      + '</div>'
      + (chips?('<div style="display:flex;flex-wrap:wrap;gap:6px">'+chips+'</div>'):'')
      + conts
      + '<div style="display:flex;flex-direction:column;gap:3px"><span style="'+LB+'">내용</span><textarea oninput="pjdNoteInput(this)" style="width:100%;min-height:56px;box-sizing:border-box;padding:7px 10px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;color:#374151;line-height:1.6;font-family:inherit;resize:vertical;outline:none;background:#fff" onfocus="this.style.borderColor=\'#1B3A6B\'" onblur="this.style.borderColor=\'#c8d2de\'">'+esc(_pjD.note)+'</textarea></div>'
      + '</div>';
  }
'''

R82_EDITS = [
# 1. 헬퍼 삽입 (_projRenderForm 바로 앞)
("""  function _projRenderForm(){""",
 HELPERS + """  function _projRenderForm(){"""),

# 2. 제목 줄에 세부 정보 버튼 + 세부 정보 영역
("""      + '<div style="padding:12px 14px;border-bottom:1px solid #e3e9f0">'
      +   '<input id="projTitleInput" type="text" placeholder="프로젝트 명" maxlength="120" style="width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #c8d2de;border-radius:0;font-size:13.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
      + '</div>'""",
 """      + '<div style="padding:12px 14px;border-bottom:1px solid #e3e9f0;display:flex;gap:8px;align-items:center">'
      +   '<input id="projTitleInput" type="text" placeholder="프로젝트 명" maxlength="120" style="flex:1;min-width:0;box-sizing:border-box;padding:8px 10px;border:1px solid #c8d2de;border-radius:0;font-size:13.5px;font-weight:700;color:#14305c;font-family:inherit;outline:none" onfocus="this.style.borderColor=\\'#1B3A6B\\'" onblur="this.style.borderColor=\\'#c8d2de\\'">'
      +   '<button type="button" id="btnProjDetail" onclick="projDetailToggle()" style="'+_PJ_BTN+';background:#fff;color:#1B3A6B;border:1px solid #1B3A6B;flex-shrink:0">세부 정보</button>'
      + '</div>'
      + '<div id="projDetailWrap" style="display:none;padding:12px 14px;border-bottom:1px solid #e3e9f0;background:#fbfcfe"><div id="projDetailBody"></div></div>'"""),

# 3. 폼 진입 시 세부 정보 상태 초기화
("""      + '</div></div>';
    setTimeout(function(){ var i=document.getElementById('projTitleInput'); if(i) try{ i.focus(); }catch(_e){} }, 60);""",
 """      + '</div></div>';
    _pjDReset();
    setTimeout(function(){ var i=document.getElementById('projTitleInput'); if(i) try{ i.focus(); }catch(_e){} }, 60);"""),

# 4. 저장 시 detail 부착
("""    var np = { id:'prj'+now+'_'+Math.floor(Math.random()*10000), memberId:myMemberId, authorName:(me?me.name:''), title:t, logs:logs, createdAt:now, updatedAt:now };
    projectsList.push(np);""",
 """    var np = { id:'prj'+now+'_'+Math.floor(Math.random()*10000), memberId:myMemberId, authorName:(me?me.name:''), title:t, logs:logs, createdAt:now, updatedAt:now };
    if(_pjD){
      var _dv=_pjD.vendors.map(function(v){
        var _cs=(_clxInfo(v.name).contacts)||[];
        return { name:v.name, contacts:v.sel.map(function(i){ var c=_cs[i]||{}; return { name:String(c.name||''), rank:String(c.rank||''), phone:String(c.phone||c.phone2||'') }; }).filter(function(c){ return c.name||c.phone; }) };
      });
      var _dp=String(_pjD.parent||'').trim(), _de=String(_pjD.equip||'').trim(), _dn=String(_pjD.note||'').trim();
      if(_dv.length||_dp||_de||_dn) np.detail={ vendors:_dv, parent:_dp, equip:_de, note:_dn };
    }
    projectsList.push(np);"""),

# 5. 펼침 상세 상단에 세부 정보 표시
("""  function _projPanelHtml(p, mine){
    var logs = _projLogsView(_projDraft.logs);""",
 """  function _projPanelHtml(p, mine){
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
    var logs = _projLogsView(_projDraft.logs);"""),

# 6. 상세 패널 return에 detHtml 삽입
("""    return '<div style="border-top:1px solid #e3eaf2;background:#fff;cursor:default">'
      + '<div style="padding:2px 14px 8px">'+rows+'</div>'""",
 """    return '<div style="border-top:1px solid #e3eaf2;background:#fff;cursor:default">'
      + _detHtml
      + '<div style="padding:2px 14px 8px">'+rows+'</div>'"""),
]

def apply_r82(s, path):
    for i,(old,new) in enumerate(R82_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R82 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r82(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r81 2026-08-14 -->') == 1
            s = s.replace('<!-- test build r81 2026-08-14 -->', '<!-- test build r82 2026-08-14 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
