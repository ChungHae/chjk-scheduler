# -*- coding: utf-8 -*-
# r147: [채권 연령 계산 버그 수정 — 마이너스(수정) 계산서/기초이월]
#  증상: 미수 잔액은 0원인데 채권 연령 특정 구간(예: 90일 초과)에 금액이 남아 표시됨.
#
#  원인: 채무(FIFO 대상) 목록 obls 에 세금계산서 전부(e.total)를 부호 구분 없이
#  그대로 넣고 있었음. 그런데 마이너스(수정) 세금계산서 — 반품·공급가 조정 등으로
#  금액이 음수인 계산서 — 나 음수 기초이월도 실제로는 "채무 증가"가 아니라
#  "채무 감소(변제와 동일 성격)"인데, obls 에 섞여 날짜순 FIFO 소진 순서를 타면서
#  이미 앞쪽에서 "미수(unpaid)"로 확정된 항목을 뒤늦게 상쇄하지 못하는 경우가
#  생김 — 전체 합계(잔액)는 0으로 정확히 맞아떨어지지만, 그 사이에 찍힌 미수 잔여
#  항목(과거 날짜)이 그대로 연령 구간에 얹혀 있게 됨.
#  (양수 조정(a.amount>0)만 obls 에 넣고 음수 조정은 이미 credit 에 합산하던
#   기존 방식과 계산서·기초이월도 동일하게 맞춤.)
#
#  수정: 계산서·기초이월도 "양수만 채무(obls)로, 음수는 변제(credit)로" 처리하도록
#  통일. 이러면 obls 의 모든 항목이 항상 0 이상이 되어, 전체 잔액이 0이 되는 순간
#  미수(unpaid) 잔여물도 항상 함께 0이 되는 것이 수학적으로 보장됨.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R147 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r147(s, path):
    s = rep(s, """      var obls=[];
      if(L.opening) obls.push({date:L.openDate||'0000-00-00', amt:L.opening, due:_fxDue(L.openDate||today, term)});
      L.invs.forEach(function(e){ obls.push({date:e.date, amt:e.total, due:_fxDue(e.date, term)}); });
      L.adjs.forEach(function(a){ if(a.amount>0) obls.push({date:a.date, amt:a.amount, due:_fxDue(a.date, term)}); });
      obls.sort(function(a,b){ return a.date<b.date?-1:a.date>b.date?1:0; });
      var credit = L.deps.reduce(function(s,e){ return s+(e.amount||0); },0)
                 + L.adjs.reduce(function(s,a){ return s+(a.amount<0?-a.amount:0); },0);""",
            """      // r147: 채무는 항상 0 이상만 obls 에 (마이너스 계산서·음수 기초이월은 변제(credit)로 합산)
      var obls=[];
      if(L.opening>0) obls.push({date:L.openDate||'0000-00-00', amt:L.opening, due:_fxDue(L.openDate||today, term)});
      L.invs.forEach(function(e){ if(e.total>0) obls.push({date:e.date, amt:e.total, due:_fxDue(e.date, term)}); });
      L.adjs.forEach(function(a){ if(a.amount>0) obls.push({date:a.date, amt:a.amount, due:_fxDue(a.date, term)}); });
      obls.sort(function(a,b){ return a.date<b.date?-1:a.date>b.date?1:0; });
      var credit = L.deps.reduce(function(s,e){ return s+(e.amount||0); },0)
                 + L.adjs.reduce(function(s,a){ return s+(a.amount<0?-a.amount:0); },0)
                 + L.invs.reduce(function(s,e){ return s+(e.total<0?-e.total:0); },0)
                 + (L.opening<0 ? -L.opening : 0);""", 1, 'FIFO')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r147(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r146 2026-08-25 -->') == 1
            s = s.replace('<!-- test build r146 2026-08-25 -->', '<!-- test build r147 2026-08-25 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
