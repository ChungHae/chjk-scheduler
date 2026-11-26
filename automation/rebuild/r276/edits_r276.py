# -*- coding: utf-8 -*-
# r276 — 메뉴 이름 정리: 상단 [업무 사이트] → [업무], 그 아래 하위 탭 [업무 사이트] → [사이트]
#   사용자 지시(2026-11-26): "업무 사이트 이름을 업무로 변경하고 밑의 카테고리의 업무사이트를 사이트로 변경"
#   r252 가 구 '기타' → '업무 사이트' 로 바꿀 때 ① 상단 탭 ② 하위 탭 ③ 페이지 제목(inv-flat-label)
#   세 군데를 같은 이름으로 맞췄다. 상단이 '업무' 가 되면 그 아래는 '사이트' 가 맞으므로
#   하위 탭과 페이지 제목을 함께 '사이트' 로 바꾼다(제목만 옛 이름으로 남으면 빠뜨린 것처럼 보인다).
#   id(tabEtc·etcSubNav)·data-page(links)·switchPage('links') 는 건드리지 않는다 — 이름만 바뀐다.
#  사용:  python3 edits_r276.py <index.html> [--test]
import io, sys, re

path = sys.argv[1]
IS_TEST = ('--test' in sys.argv)
s = io.open(path, encoding='utf-8').read()
orig = len(s)

def rep(old, new, cnt, label):
    global s
    n = s.count(old)
    assert n == cnt, 'ANCHOR %s: expected %d, found %d' % (label, cnt, n)
    s = s.replace(old, new)
    print('  ok  %s' % label)

# 이미 적용된 판에 두 번 돌리지 않게
assert s.count('<button class="page-tab" id="tabEtc">업무 사이트</button>') == 1, \
    'FORBIDDEN(이미 r276 적용됐거나 상단 탭 이름이 다름)'

# ① 상단 탭 이름
rep('<button class="page-tab" id="tabEtc">업무 사이트</button><!-- r252: 구 \'기타\' -->',
    '<button class="page-tab" id="tabEtc">업무</button><!-- r252: 구 \'기타\' · r276: 이름 정리 -->',
    1, '① 상단 탭 업무 사이트 → 업무')

# ② 하위 탭 이름
rep('<button class="sub-tab" data-page="links">업무 사이트</button>',
    '<button class="sub-tab" data-page="links">사이트</button><!-- r276: 이름 정리 -->',
    1, '② 하위 탭 업무 사이트 → 사이트')

# ③ 페이지 제목(툴바 왼쪽 라벨)
rep('<span class="inv-flat-label">업무 사이트</span>',
    '<span class="inv-flat-label">사이트</span>',
    1, '③ 페이지 제목 업무 사이트 → 사이트')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r276 2026-11-26 -->')
    print('  ok  test marker %s -> r276' % m.group(0))

# NEED — 바뀐 이름이 들어갔는지
for k in ['<button class="page-tab" id="tabEtc">업무</button>',
          '<button class="sub-tab" data-page="links">사이트</button>',
          '<span class="inv-flat-label">사이트</span>']:
    assert k in s, 'NEED missing: ' + k
# KEEP — 동작에 쓰이는 id·키는 그대로
for k in ['id="tabEtc"', 'id="etcSubNav"', 'data-page="links"', "switchPage('links')",
          "var _ETC=['links']", 'renderLinksPage()', 'id="pageLinks"']:
    assert k in s, 'KEEP missing: ' + k
# FORBIDDEN — 옛 이름이 화면에 남아 있으면 안 된다
assert '업무 사이트' not in s, 'FORBIDDEN: 옛 이름 "업무 사이트" 가 남아 있다'
assert '업무사이트' not in s, 'FORBIDDEN: 옛 이름 "업무사이트" 가 남아 있다'

io.open(path, 'w', encoding='utf-8').write(s)
print('r276 적용 완료: %d -> %d' % (orig, len(s)))
