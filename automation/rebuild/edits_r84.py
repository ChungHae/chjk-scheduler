# -*- coding: utf-8 -*-
# r84: 프로젝트 기록 줄의 수정/삭제 버튼을 앱 표준 아이콘으로 통일. (재작성본 v3)
#      표준: 수정=연필 SVG(#5b7ba6, hover #1B3A6B, 테두리 없음) / 삭제=휴지통 SVG(#dc2626, hover #b91c1c)
#      ※ 규칙: 공통 동작(수정·삭제·추가 등) 버튼은 항상 이 표준 아이콘을 사용할 것.

R84_EDITS = [
("""            + '<button onclick="editProjectLog(\\''+lg.id+'\\')" style="'+_PJ_SBTN+'">수정</button>'
            + '<button onclick="deleteProjectLog(\\''+lg.id+'\\')" style="'+_PJ_SBTN+';color:#dc2626;border-color:#e5c0c0">삭제</button>'""",
 """            + '<button onclick="editProjectLog(\\''+lg.id+'\\')" title="수정" style="border:none;background:none;cursor:pointer;padding:2px 3px;color:#5b7ba6;display:inline-flex;align-items:center" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#5b7ba6\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg></button>'
            + '<button onclick="deleteProjectLog(\\''+lg.id+'\\')" title="삭제" style="border:none;background:none;cursor:pointer;padding:2px 3px;color:#dc2626;display:inline-flex;align-items:center" onmouseover="this.style.color=\\'#b91c1c\\'" onmouseout="this.style.color=\\'#dc2626\\'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;display:block"><path d="M4 6.5h16"/><path d="M9.5 6.5V4.6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.9"/><path d="M6.5 6.5 7.4 19a2 2 0 0 0 2 1.9h5.2a2 2 0 0 0 2-1.9l.9-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/></svg></button>'"""),
]

def apply_r84(s, path):
    for i,(old,new) in enumerate(R84_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R84 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r84(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r83 2026-08-14 -->') == 1
            s = s.replace('<!-- test build r83 2026-08-14 -->', '<!-- test build r84 2026-08-18 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
