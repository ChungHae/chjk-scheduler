# -*- coding: utf-8 -*-
# r58: 상세주소를 주소 옆으로 (우편번호 | 주소 | 상세주소 한 줄)
R58_EDITS = [
("""      +   _clxFld('addr','주소 (도로명)',inf.addr,2)
      +   '<div id="clxPostWrap" style="grid-column:1/-1;display:none;height:430px;border:1px solid #c8d2de;position:relative"></div>'
      +   _clxFld('addr2','상세주소',inf.addr2,3)""",
 """      +   _clxFld('addr','주소 (도로명)',inf.addr,1)
      +   _clxFld('addr2','상세주소',inf.addr2,1)
      +   '<div id="clxPostWrap" style="grid-column:1/-1;display:none;height:430px;border:1px solid #c8d2de;position:relative"></div>'"""),
]
def apply_r58(s, path):
    for i,(old,new) in enumerate(R58_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R58 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r58(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r57 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r57 2026-08-13 -->', '<!-- test build r58 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
