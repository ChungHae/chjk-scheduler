# -*- coding: utf-8 -*-
# r193: 하나은행 어음(하나채권) 업로드 차단
#  근거: 하나은행은 어음 결제대금이 입출금 내역에 「채권입금」으로 그대로 들어온다.
#        (2021 어음파일 14건 전수 대조 → 만기일·금액 동일한 채권입금 행이 100% 존재)
#        따라서 어음 파일을 올리면 같은 돈이 두 번 잡힌다. 경고만 띄우고 무조건 막는다.
import io, sys, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD = (
    "          if(noteKind){\n"
    "            var iNo, iVen, iAmt, iDt, iSt, iCxl=-1, iDue=-1;\n"
)
NEW = (
    "          if(noteKind){\n"
    "            // r193: 하나은행 어음(전자채권)은 무조건 막는다.\n"
    "            //  하나은행은 어음 결제대금이 입출금 내역에 「채권입금」으로 그대로 들어오므로\n"
    "            //  어음 파일까지 올리면 같은 돈이 두 번 잡힌다. 확인 절차 없이 차단한다.\n"
    "            if(noteKind==='하나채권'){\n"
    "              warns.push(esc(f.name)+': <b>하나은행 어음(전자채권) 파일은 올리지 않습니다 — 0건 등록하고 건너뛰었습니다.</b><br>'\n"
    "                + '하나은행은 어음 결제대금이 입출금 내역에 「채권입금」으로 그대로 들어옵니다. '\n"
    "                + '이 파일을 올리면 같은 돈이 두 번 잡히므로, 하나은행은 <b>입출금 내역만</b> 올려주세요.');\n"
    "              continue;\n"
    "            }\n"
    "            var iNo, iVen, iAmt, iDt, iSt, iCxl=-1, iDue=-1;\n"
)

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD, NEW, 1, 'r193 하나채권 차단 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r193 2026-09-18 -->', s, count=1)
        if s2 == s:
            raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
