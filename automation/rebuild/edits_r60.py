# -*- coding: utf-8 -*-
# r60: 개인일정 — 공지·연차 표시 켜기/끄기 체크박스 (브라우저별 설정 저장)
R60_EDITS = [
# E1: 컨트롤바에 체크박스 2개 (잔여 연차 배지 앞)
("""      <span id="vacRemainBadge" onclick="openVacAdmin()" title="클릭하여 연차 현황 보기" style="display:none;align-items:center;gap:4px;padding:5px 12px;border-radius:20px;font-size:12px;font-weight:700;border:1.5px solid #aac4e6;background:#eaf1fb;color:#14305c;cursor:pointer">잔여 연차 <b id="vacRemainNum">-</b>일</span>""",
 """      <span id="psShowToggles" style="display:inline-flex;align-items:center;gap:10px;padding:0 4px">
        <label style="display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;color:#374151;cursor:pointer;white-space:nowrap"><input type="checkbox" id="psShowBcast" checked onchange="psToggleShow()" style="width:14px;height:14px;accent-color:#1B3A6B;cursor:pointer">공지</label>
        <label style="display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;color:#374151;cursor:pointer;white-space:nowrap"><input type="checkbox" id="psShowVac" checked onchange="psToggleShow()" style="width:14px;height:14px;accent-color:#1B3A6B;cursor:pointer">연차</label>
      </span>
      <span id="vacRemainBadge" onclick="openVacAdmin()" title="클릭하여 연차 현황 보기" style="display:none;align-items:center;gap:4px;padding:5px 12px;border-radius:20px;font-size:12px;font-weight:700;border:1.5px solid #aac4e6;background:#eaf1fb;color:#14305c;cursor:pointer">잔여 연차 <b id="vacRemainNum">-</b>일</span>"""),

# E2: 상태 저장/복원 + 토글 함수 (renderPersonalPage 앞에 추가)
("""  function renderPersonalPage() {
    updateTodayWidget();""",
 """  // 개인일정 공지/연차 표시 여부 (이 브라우저에만 저장되는 개인 설정)
  function _psShowBcast(){ try{ return localStorage.getItem('ps_show_bcast')!=='0'; }catch(_e){ return true; } }
  function _psShowVac(){ try{ return localStorage.getItem('ps_show_vac')!=='0'; }catch(_e){ return true; } }
  window.psToggleShow = function(){
    var b=document.getElementById('psShowBcast'), v=document.getElementById('psShowVac');
    try{
      if(b) localStorage.setItem('ps_show_bcast', b.checked?'1':'0');
      if(v) localStorage.setItem('ps_show_vac', v.checked?'1':'0');
    }catch(_e){}
    renderPersonalPage();
  };
  function renderPersonalPage() {
    updateTodayWidget();
    var _sb=document.getElementById('psShowBcast'); if(_sb) _sb.checked=_psShowBcast();
    var _sv=document.getElementById('psShowVac'); if(_sv) _sv.checked=_psShowVac();"""),

# E3: 달력 줄 구성에 토글 적용
("""      const _lines = [];
      bcastBarsHtml(dStr).forEach(h => _lines.push(h));
      vacBarsHtml(dStr, dow).forEach(h => _lines.push(h));""",
 """      const _lines = [];
      if (_psShowBcast()) bcastBarsHtml(dStr).forEach(h => _lines.push(h));
      if (_psShowVac()) vacBarsHtml(dStr, dow).forEach(h => _lines.push(h));"""),
]
def apply_r60(s, path):
    for i,(old,new) in enumerate(R60_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R60 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r60(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r59 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r59 2026-08-13 -->', '<!-- test build r60 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
