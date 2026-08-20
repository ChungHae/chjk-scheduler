# -*- coding: utf-8 -*-
# r104: 일정 하위 탭 개편 (v2 — live/test 공통 문자열로 스왑 방식)
#       프로젝트 탭 → "개인 일정" 이름으로 맨 앞(기존 개인 일정 자리)으로,
#       기존 개인 일정 탭 → "달력" 이름으로 기존 프로젝트 자리로.
#       두 버튼의 자리를 서로 맞바꾸는 치환이라 위치·이름이 동시에 처리됨.
#       (시작 탭은 기존처럼 personal(달력) 유지)

R104_EDITS = [
("""<button class="sub-tab active" data-page="personal">개인 일정</button>""",
 """<button class="sub-tab" data-page="project">개인 일정</button>""", 1),
("""<button class="sub-tab" data-page="project">프로젝트</button>""",
 """<button class="sub-tab active" data-page="personal">달력</button>""", 1),
]

def apply_r104(s, path):
    for i,(old,new,exp) in enumerate(R104_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R104 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r104(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r103 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r103 2026-08-20 -->', '<!-- test build r104 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
