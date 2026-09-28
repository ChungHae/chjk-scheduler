# -*- coding: utf-8 -*-
# r204(회계): 합계 줄 판정에 '총 N건' 형태 추가 (우리은행)
#  우리은행 거래내역조회 파일의 마지막 줄은 `총 73건 | 40,857,950원 | 35,010,197원` 형태라
#  r190 의 합계 판정(합계/소계/총계/계 정확히 일치)에 걸리지 않아 "거래일시를 읽지 못해 1행을 건너뛰었습니다"
#  라는 헛경고가 떴다. 자료가 빠진 것은 아니다(입금 8건 합계 35,010,197원 = 파일의 입금합계와 일치).
#  → 합계 줄로 인정해 경고를 내지 않는다.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD = "              var _sumRow = (row6||[]).some(function(c){ return /^(합계|소계|총계|계)$/.test(_fxCell(c)); });\n"
NEW = ("              // r204: 우리은행은 마지막 줄이 '총 73건' 형태다 — 이것도 합계 줄로 본다.\n"
       "              var _sumRow = (row6||[]).some(function(c){ var _t=_fxCell(c); return /^(합계|소계|총계|계)$/.test(_t) || /^총\\s*[\\d,]+\\s*건$/.test(_t); });\n")

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD, NEW, 1, 'r204 합계줄 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r204 2026-09-28 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
