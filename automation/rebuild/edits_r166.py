# -*- coding: utf-8 -*-
# r166: 매입매출 > "자료 업로드" 탭을 마스터 계정(chjk) 전용으로 (사용자 지시, 즉시 배포)
#
#  판단 근거:
#   - "마스터 계정인 chjk 계정만" 이므로 _isAdmin() 이 아니라 _vacIsMaster() 기준.
#     (_isAdmin 은 role==='admin' 인 다른 계정도 통과한다)
#   - 자료 업로드 탭 진입 경로는 딱 두 곳뿐임을 전수 확인:
#       ① 서브탭 버튼 <button data-fxtab="up" onclick="fxSwitchTab('up')">
#       ② window.fxSwitchTab('up') 직접 호출 (코드 내 다른 호출처 없음)
#     그래서 (가) 버튼 숨김 (나) fxSwitchTab 차단 (다) _fxTab 이 'up' 인 채로 남는 경우 'ar' 로 되돌림
#     세 겹으로 막는다. 화면이 떠 있는 상태에서 계정이 바뀌어도 renderFxPage 가 다시 판정한다.
#   - 매입매출 페이지 진입(switchPage) 은 renderFxPage() 를 부르므로 여기 한 곳만 손보면 된다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R166 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r166(s, path):
    # (1) 권한 헬퍼 + 탭 전환 차단
    s = rep(s,
        "  window.fxSwitchTab = function(t){ _fxTab = t; _fxArPage=1; renderFxPage(); };",
        "  // r166: '자료 업로드' 탭은 마스터 관리자(chjk) 계정만 사용 (사용자 지시)\n"
        "  function _fxUpAllowed(){ try{ return !!_vacIsMaster(); }catch(e){ return false; } }\n"
        "  window.fxSwitchTab = function(t){\n"
        "    if(t==='up' && !_fxUpAllowed()){ showInfoModal('권한','자료 업로드는 마스터 관리자(chjk) 계정만 사용할 수 있습니다.'); return; }\n"
        "    _fxTab = t; _fxArPage=1; renderFxPage();\n"
        "  };",
        1, 'FXSWITCH')

    # (2) 렌더 시점에 버튼 숨김 + 'up' 상태로 남아 있으면 미수현황으로 되돌림
    s = rep(s,
        "    var nv=document.getElementById('fxSubNav');\n"
        "    if(nv) nv.querySelectorAll('.file-grp-tab').forEach(function(b){ b.classList.toggle('active', b.dataset.fxtab===_fxTab); });",
        "    if(_fxTab==='up' && !_fxUpAllowed()) _fxTab='ar';   // r166: 업로드 탭은 마스터 전용\n"
        "    var nv=document.getElementById('fxSubNav');\n"
        "    if(nv){ var _ub=nv.querySelector('[data-fxtab=\"up\"]'); if(_ub) _ub.style.display = _fxUpAllowed() ? '' : 'none'; }\n"
        "    if(nv) nv.querySelectorAll('.file-grp-tab').forEach(function(b){ b.classList.toggle('active', b.dataset.fxtab===_fxTab); });",
        1, 'FXRENDER')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r166(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r165 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r165 2026-08-26 -->', '<!-- test build r166 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
