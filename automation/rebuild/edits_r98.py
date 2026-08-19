# -*- coding: utf-8 -*-
# r98: 접힌 제목 옆 ＋ 버튼을 "＋ 업체 추가" 글자 버튼으로 확대 (＋ 줄 추가와 같은 스타일)

OLD = """              + (mine?('<button data-id="'+m.id+'" onclick="pmVendQuickAdd(this.dataset.id)" title="업체 추가" style="flex-shrink:0;border:none;background:none;cursor:pointer;color:#b6a94f;font-size:13px;font-weight:700;padding:0 2px;line-height:1;font-family:inherit" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#b6a94f\\'">&#65291;</button>'):'')"""
NEW = """              + (mine?('<button data-id="'+m.id+'" onclick="pmVendQuickAdd(this.dataset.id)" title="업체 추가" style="flex-shrink:0;border:none;background:none;cursor:pointer;color:#b6a94f;font-size:11px;padding:2px;font-family:inherit;white-space:nowrap" onmouseover="this.style.color=\\'#1B3A6B\\'" onmouseout="this.style.color=\\'#b6a94f\\'">&#65291; 업체 추가</button>'):'')"""

def apply_r98(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R98 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r98(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r97 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r97 2026-08-19 -->', '<!-- test build r98 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
