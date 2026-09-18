# -*- coding: utf-8 -*-
# r194: 기업은행 어음(전자매출채권)도 하나은행과 똑같이 차단
#  근거(2026-09-18 실자료 대조): 서울 기업 어음.xlsx 유효 2건이 모두 입출금 내역에 같은 금액으로 입금.
#    IBK20221031000006809 132,916,053 만기 2022-11-20(일) → 입금 2022-11-21 유일에너테크(주)
#    IBK20240628000003368  30,114,981 만기 2024-09-10      → 입금 2024-09-10 유일에너테크(주)
#  신한은 통장에 어음번호로 찍혀 제외로 빠지므로 겹치지 않는다 → 신한어음만 계속 받는다.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD = (
    "            // r193: 하나은행 어음(전자채권)은 무조건 막는다.\n"
    "            //  하나은행은 어음 결제대금이 입출금 내역에 「채권입금」으로 그대로 들어오므로\n"
    "            //  어음 파일까지 올리면 같은 돈이 두 번 잡힌다. 확인 절차 없이 차단한다.\n"
    "            if(noteKind==='하나채권'){\n"
    "              warns.push(esc(f.name)+': <b>하나은행 어음(전자채권) 파일은 올리지 않습니다 — 0건 등록하고 건너뛰었습니다.</b><br>'\n"
    "                + '하나은행은 어음 결제대금이 입출금 내역에 「채권입금」으로 그대로 들어옵니다. '\n"
    "                + '이 파일을 올리면 같은 돈이 두 번 잡히므로, 하나은행은 <b>입출금 내역만</b> 올려주세요.');\n"
    "              continue;\n"
    "            }\n"
)
NEW = (
    "            // r193/r194: 하나은행·기업은행 어음은 무조건 막는다.\n"
    "            //  두 은행 모두 어음 결제대금이 입출금 내역에 그대로 입금으로 들어오므로\n"
    "            //  어음 파일까지 올리면 같은 돈이 두 번 잡힌다. 확인 절차 없이 차단한다.\n"
    "            //   하나 : 통장에 「채권입금」으로 기록 (2021년 14건 전수 대조)\n"
    "            //   기업 : 통장에 거래처명으로 그대로 입금 (유효 2건 전수 대조, 만기일 일치)\n"
    "            //  신한은 통장에 어음번호로 찍혀 제외로 빠지므로 겹치지 않는다 → 신한어음만 받는다.\n"
    "            if(noteKind==='하나채권' || noteKind==='기업어음'){\n"
    "              var _bkNm = (noteKind==='하나채권') ? '하나은행 어음(전자채권)' : '기업은행 어음(전자매출채권)';\n"
    "              var _bkWhy = (noteKind==='하나채권')\n"
    "                ? '하나은행은 어음 결제대금이 입출금 내역에 「채권입금」으로 그대로 들어옵니다. '\n"
    "                : '기업은행은 어음이 만기결제되면 입출금 내역에 거래처명으로 그대로 입금됩니다. ';\n"
    "              var _bkNm2 = (noteKind==='하나채권') ? '하나은행' : '기업은행';\n"
    "              warns.push(esc(f.name)+': <b>'+_bkNm+' 파일은 올리지 않습니다 — 0건 등록하고 건너뛰었습니다.</b><br>'\n"
    "                + _bkWhy\n"
    "                + '이 파일을 올리면 같은 돈이 두 번 잡히므로, '+_bkNm2+'은 <b>입출금 내역만</b> 올려주세요.');\n"
    "              continue;\n"
    "            }\n"
)

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD, NEW, 1, 'r194 기업어음 차단 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r194 2026-09-18 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
