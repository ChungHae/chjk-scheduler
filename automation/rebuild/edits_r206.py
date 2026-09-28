# -*- coding: utf-8 -*-
# r206(회계): 상호가 같고 사업자번호가 다른 거래처가 아예 검색되지 않던 문제
#  증상: 화성 계산서의 '에프에이코리아(주) / 119-81-21778' 을 입금 매칭에서 찾을 수 없었다.
#  원인: 거래처 목록에는 같은 상호가 '312-85-35092' 로 등록돼 있었고,
#        드롭다운 아래 '계산서에만 있는 거래처' 칸을 만드는 _fxInvOnlyOpts 가
#        사업자번호뿐 아니라 **상호가 같기만 해도** 후보에서 빼고 있었다.
#        → 번호가 달라도 통째로 숨어 양쪽 칸 어디에도 안 나온다.
#  같은 유형 7건 확인(계산서 기준):
#    씨아이텍 127-45-52629 / 한국과학 617-24-39371 / 시온전기 113-21-97747 /
#    (주)TPC메카트로닉스 137-85-00221 / 크린토피아강서지사 109-07-68548 /
#    한국에스엠씨공압(주) 109-81-42868 / 에프에이코리아(주) 119-81-21778
#  사용자 지시: "우선은 나도 어떻게 된건지 알수가 없으니 모든 업체가 다 별개로 존재하게 했으면 해."
#  처리:
#   (1) _fxInvOnlyOpts — 사업자번호가 있으면 **번호로만** 판단한다.
#       상호 기준 제외는 사업자번호가 아예 없는 계산서에만 적용(종전 의도 유지).
#   (2) fxPickNewVend — 상호가 같아도 사업자번호가 다르면 기존 업체로 합치지 않고 새로 등록한다.
#       거래처 목록·검색·배정이 모두 '상호' 키로 동작하므로, 이름이 겹칠 때는
#       상호 뒤에 사업자번호를 붙여 `에프에이코리아(주) (119-81-21778)` 로 등록한다.
#       미수현황 원장 키는 사업자번호가 우선이라(_fxLedgersOne), 이름이 달라도
#       그 번호의 계산서와 정상적으로 한 원장에 묶인다.
#       사업자번호가 없는 경우는 종전대로 기존 업체로 본다.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD1 = """      var digits=String(e.vbiz||'').replace(/[^0-9]/g,'');
      if(digits && byBiz[digits]) return;
      if(byName[e.vendor]) return;
"""
NEW1 = """      var digits=String(e.vbiz||'').replace(/[^0-9]/g,'');
      // r206: 사업자번호가 있으면 번호로만 판단한다.
      //  상호까지 보면 '같은 상호·다른 사업자번호'인 거래처가 통째로 숨어 검색되지 않았다.
      if(digits){ if(byBiz[digits]) return; }
      else if(byName[e.vendor]) return;
"""

OLD2 = """    if((allClients()||[]).some(function(c){ return c && c[0]===name; })){ fxPickVend(i, name); return; }
    showConfirmModal('업체 등록 + 배정',
      '"'+esc(name)+'"'+(vbiz?' ('+vbiz+')':'')+' 업체가 일정 > 업체에 없습니다.\\n일정 > 업체에 등록하고 이 입금을 배정할까요?',
      function(){
        try{ ensureClientList(); }catch(_e){}
        // r158: 이 입금이 들어온 사업장을 업체의 지점으로 기록
        var _d0=_fxUnList[i];
        var _d0b=(_d0&&_d0.biz)||'서울';
        // r163: 계산서에 종사업장번호가 있으면 함께 등록
        clientList.push(_cliMake(name, vbiz||'', _d0b, _fxVsbOf(_d0b, name, vbiz)));
        _saveClients();
        fxPickVend(i, name);
      }, '등록 + 배정', '#1B3A6B');
"""
NEW2 = """    // r206: 상호가 같아도 사업자번호가 다르면 다른 업체다.
    //  거래처 목록·검색·배정이 모두 '상호' 키로 동작하므로,
    //  이름이 겹치면 상호 뒤에 사업자번호를 붙여 등록한다.
    //  (미수현황 원장 키는 사업자번호가 우선이라 이름이 달라도 같은 원장으로 묶인다)
    var _sameNm=(allClients()||[]).some(function(c){ return c && c[0]===name; });
    if(_sameNm && !vbiz){ fxPickVend(i, name); return; }
    var _reg = _sameNm ? (name+' ('+vbiz+')') : name;
    if(_sameNm && (allClients()||[]).some(function(c){ return c && c[0]===_reg; })){ fxPickVend(i, _reg); return; }
    showConfirmModal('업체 등록 + 배정',
      '"'+esc(name)+'"'+(vbiz?' ('+vbiz+')':'')+' 업체가 일정 > 업체에 없습니다.\\n'
      + (_sameNm ? '같은 상호가 다른 사업자번호로 이미 있어, 구분하려고 "'+esc(_reg)+'" 로 등록합니다.\\n' : '')
      + '일정 > 업체에 등록하고 이 입금을 배정할까요?',
      function(){
        try{ ensureClientList(); }catch(_e){}
        // r158: 이 입금이 들어온 사업장을 업체의 지점으로 기록
        var _d0=_fxUnList[i];
        var _d0b=(_d0&&_d0.biz)||'서울';
        // r163: 계산서에 종사업장번호가 있으면 함께 등록
        clientList.push(_cliMake(_reg, vbiz||'', _d0b, _fxVsbOf(_d0b, name, vbiz)));   // r206
        _saveClients();
        fxPickVend(i, _reg);
      }, '등록 + 배정', '#1B3A6B');
"""

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD1, NEW1, 1, 'r206 _fxInvOnlyOpts (%s)' % path)
    s = rep(s, OLD2, NEW2, 1, 'r206 fxPickNewVend (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r206 2026-09-28 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
