# -*- coding: utf-8 -*-
# r101: (1) 메모 제목 "(업체 미지정)" → "(제목 없음)"
#       (2) "＋ 업체 추가" 버튼 라벨 → "＋ 업체 / 제목 추가" (접힌 제목 + 수정모드, 2곳)
#       (3) "＋ 줄 추가" 버튼 행에도 괘선(구분선) 표시

# (old, new, expected_count)
R101_EDITS = [

(""":'<span style="color:#b6a94f;font-weight:600">(업체 미지정)</span>')+'</span>'""",
 """:'<span style="color:#b6a94f;font-weight:600">(제목 없음)</span>')+'</span>'""", 1),

("""&#65291; 업체 추가</button>""",
 """&#65291; 업체 / 제목 추가</button>""", 2),

("""flex-shrink:0;display:flex;align-items:center;margin-top:2px""",
 """flex-shrink:0;display:flex;align-items:center;padding:2px 0;border-bottom:1px solid rgba(182,169,79,.28)""", 1),
]

def apply_r101(s, path):
    for i,(old,new,exp) in enumerate(R101_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R101 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r101(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r100 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r100 2026-08-20 -->', '<!-- test build r101 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
