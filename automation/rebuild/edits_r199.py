# -*- coding: utf-8 -*-
# r199(공통): .pf-btn.active 선택 표시가 안 보이던 문제
#  원인: 카드매출·매입처·링크의 필터는 JS 로 inline style(#1B3A6B)을 직접 칠해서 파랗게 보이지만,
#   매입매출(미수현황·집계·업로드)의 지역 버튼, 집계의 월별/거래처별, 업체 관리의 지점 버튼은
#   class 'active' 만 붙이는데 .pf-btn.active CSS 규칙이 아예 없었다 → 눌러도 모양 변화 없음.
#  해결: 다른 필터와 같은 색(#1B3A6B)으로 .pf-btn.active 규칙 1개 추가. inline 방식 필터는 active 클래스를
#   쓰지 않으므로 영향 없음.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD = "    .cho-btn.active { background:#1B3A6B; color:#fff; border-color:#1B3A6B; }\n"
NEW = OLD + ("    /* r199: class 로 선택 표시하는 필터 버튼(매입매출 지역·집계 모드·업체 지점) — 다른 필터와 같은 색 */\n"
             "    .pf-btn.active, .pf-btn.active:hover { background:#1B3A6B; color:#fff; border-color:#1B3A6B; font-weight:700; }\n")

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD, NEW, 1, 'r199 css (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r199 2026-09-22 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
