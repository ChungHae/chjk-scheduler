# -*- coding: utf-8 -*-
# r202(회계): 은행 이자 입금 자동 제외 보강
#  국민은행 입출금 내역의 이자 입금은 입금자명이 '이자세금:0원'(적요 '결산이자') 으로 들어온다.
#  r198 에서 넣은 규칙은 입금자명이 정확히 '예금이자'/'이자' 일 때만 걸려서 이 형태를 놓쳤다.
#  → 미배정으로 남아 사람이 매번 손으로 제외해야 했다. '이자세금'·'결산이자'·'이자지급' 을 포함하면 자동 제외.
#  ※ 거래처명에 '이자'가 들어가도(예: (주)이자테크) 걸리지 않게, 이자 관련 합성어만 본다.
#  2026-09-28 실자료: 서울 국민 804-25-0027-056 / 2021년 입금 120건 중 이자 4건(423·1,106·5,136·5,496원).
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD = "    if(/^(예금)?이자$/.test(p)) return true;     // r198: 예금이자 (거래처 수금 아님)\n"
NEW = ("    if(/^(예금)?이자$/.test(p)) return true;     // r198: 예금이자 (거래처 수금 아님)\n"
       "    if(/이자세금|결산이자|이자지급/.test(p)) return true;   // r202: 국민은행 '이자세금:0원'(적요 결산이자) 형태\n")

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD, NEW, 1, 'r202 이자 자동제외 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r202 2026-09-28 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
