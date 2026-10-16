# -*- coding: utf-8 -*-
# r237 (사용자 보고 2026-10-16): 회계 > 자료 업로드 '적재 현황' 두 가지 수정
#   ① 사업장을 '실제 통장'(obiz) 기준으로 센다.
#      [사업장 이동 배정](fxPickCrossVend) 으로 서울 계좌 입금을 화성 거래처 수금으로
#      옮기면 e.biz 가 '화성' 으로 바뀌고 e.obiz='서울' 이 남는다. 적재 현황이 e.biz 를
#      보고 있어서 '화성 기업은행 2024.09.10' 처럼 없는 통장이 있는 것처럼 보였다.
#      (실제 자료 확인: 화성 bank='기업' 2건 = 둘 다 obiz='서울', id 도 'B|서울|기업|…')
#      수금·미수 계산은 그대로 e.biz 를 쓰므로 영향 없다.
#   ② 더 쓰지 않는 통장(iM뱅크, 2022-12-25 거래 종료)은 적재 현황에서 숨긴다.
#      자료는 그대로 두므로 과거 수금·미수는 변하지 않는다.
import io, sys

OLD = """    (fxDeposits||[]).forEach(function(e){
      var isNote=(e.kind==='note');
      var nm=e.bank||(isNote?'어음':'기타');
      put((isNote?'3':'2')+nm, nm, isNote?'어음':'입금', e.biz, e.date);
    });"""

NEW = """    (fxDeposits||[]).forEach(function(e){
      var isNote=(e.kind==='note');
      var nm=e.bank||(isNote?'어음':'기타');
      if(_FX_UPHIDE[nm]) return;                                  // r237: 안 쓰는 통장은 숨김
      // r237: 사업장은 '실제 통장'(obiz) 기준. [사업장 이동 배정] 으로 옮긴 입금이
      //  없는 통장을 있는 것처럼 보이게 하던 문제(화성 기업은행 2건).
      put((isNote?'3':'2')+nm, nm, isNote?'어음':'입금', (e.obiz||e.biz), e.date);
    });"""

# _FX_UPHIDE 선언은 _fxUpStat 바로 앞에
OLD2 = """  // r230→r231: 자료 업로드 맨 위 '적재 현황'"""
NEW2 = """  // r237: 적재 현황에서 숨길 통장 (자료·수금 계산에는 그대로 쓰인다)
  //   iM뱅크(대구) = 2022-12-25 로 거래 종료 — 사용자 2026-10-16 \"일단 숨김\"
  var _FX_UPHIDE = { 'iM': 1 };
  // r230→r231: 자료 업로드 맨 위 '적재 현황'"""

MARKER = ["<!-- test build r236 2026-10-16 -->", "<!-- test build r237 2026-10-16 -->"]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp:
        raise SystemExit('R237 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def apply_r237(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    s = rep(s, OLD2, NEW2, 1, 'UPHIDE_DECL')
    s = rep(s, OLD, NEW, 1, 'DEP_LOOP')
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    # 잔재 검사 — _fxUpStat 안에 e.biz 직접 사용이 남아 있으면 안 된다(계산서 두 줄은 obiz 가 없음)
    seg = s[s.index('function _fxUpStat'):s.index('function _fxUpStat') + 2600]
    if 'put((isNote?\'3\':\'2\')+nm, nm, isNote?\'어음\':\'입금\', e.biz' in seg:
        raise SystemExit('R237 FAIL e.biz 잔재')
    for need in ['_FX_UPHIDE[nm]', "(e.obiz||e.biz)"]:
        if need not in seg:
            raise SystemExit('R237 FAIL 누락: ' + need)
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f:
            s = f.read()
        s = apply_r237(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(s)
        print('r237 applied:', path)
