# -*- coding: utf-8 -*-
# r224 (사용자 요청 2026-10-12): 법인카드 사용 내역 정리 — 회계 > 카드사용 탭 + 개인 일정 '내 카드'.
#   자료: Firebase `teamdata_test_carduse/{issuer}/{YYYYMMDD}/{id}` (GitHub Actions 수집기가 쓰는 자리 — 카드매출과 같은 틀)
#         + `_meta/{issuer}`, `_cards`(카드 끝4자리→사용자), `_tags`(건별 용도·사용자·메모), `_learn`(가맹점→용도 자동), `_cats`(용도 목록).
#   화면: 월별 집계 타일 · 카드/사용자/용도 소계 · 건별 목록(용도·사용자·메모 바로 입력, 가맹점 학습) · 매입계산서 대사 · 엑셀 다운로드
#         · (관리자) 카드사 엑셀 수동 업로드(머리글 키워드로 자동 판별) · 카드 등록.
#   개인: 메모장 "내 카드" 버튼 → 본인 카드 건만 보고 용도·메모 입력. 미분류 건이 있으면 메모장 맨 위 배너.
#
# ※ 이 리비전은 편집 내용(OPS)이 커서 한 곳(apply_r224.js)에만 두고, 이 파일은 그 OPS 를 읽어 적용한다.
#    r216~r223 과 같은 방식으로 쓰면 된다:  python3 edits_r224.py <index.html> [<test/index.html>]
import io, sys, json, os, re

def load_ops():
    here = os.path.dirname(os.path.abspath(__file__))
    with io.open(os.path.join(here, 'apply_r224.js'), 'r', encoding='utf-8') as f: js = f.read()
    m = re.search(r'var OPS = (\[.*?\]);\n  for\(var i=0', js, re.S)
    if not m: raise SystemExit('apply_r224.js 에서 OPS 를 찾지 못했습니다')
    return json.loads(m.group(1))

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R224 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r224(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in load_ops():
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r224(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r224 applied:', path)
