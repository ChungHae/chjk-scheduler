# -*- coding: utf-8 -*-
# r61: 공지/연차 체크박스를 일정 등록 버튼 옆으로 이동
TOG = """      <span id="psShowToggles" style="display:inline-flex;align-items:center;gap:10px;padding:0 4px">
        <label style="display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;color:#374151;cursor:pointer;white-space:nowrap"><input type="checkbox" id="psShowBcast" checked onchange="psToggleShow()" style="width:14px;height:14px;accent-color:#1B3A6B;cursor:pointer">공지</label>
        <label style="display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;color:#374151;cursor:pointer;white-space:nowrap"><input type="checkbox" id="psShowVac" checked onchange="psToggleShow()" style="width:14px;height:14px;accent-color:#1B3A6B;cursor:pointer">연차</label>
      </span>
"""
BTN = """      <button id="btnEntryAdd" onclick="openEntryToday()" style="display:none;padding:4px 12px;border-radius:8px;border:1.5px solid #1B3A6B;background:#1B3A6B;color:#fff;font-size:12px;font-weight:700;cursor:pointer;font-family:inherit;transition:background 0.12s,border-color 0.12s" onmouseover="this.style.background='#14305c'" onmouseout="this.style.background='#1B3A6B'">일정 등록</button>
"""
def apply_r61(s, path):
    if s.count(TOG) != 1: raise SystemExit('R61 TOG FAIL %s count %d' % (path, s.count(TOG)))
    s = s.replace(TOG, '')
    if s.count(BTN) != 1: raise SystemExit('R61 BTN FAIL %s count %d' % (path, s.count(BTN)))
    return s.replace(BTN, BTN + TOG)
if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r61(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r60 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r60 2026-08-13 -->', '<!-- test build r61 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
