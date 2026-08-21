# -*- coding: utf-8 -*-
# r121: (1) "숨김 프로젝트 표시" ↔ "숨김 메모 표시" 체크박스 순서 교체
#       (2) 프로젝트 목록 열 순서: 등록일 → 프로젝트명 → 등록자 → 최근 기록 → 기록 수
#           (본인 표시 파란 세로선은 첫 열인 등록일 칸으로 이동)

# (old, new, expected_count)
R121_EDITS = [

# (1) 체크박스 순서 교체
("""<label style="display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:#6b7280;cursor:pointer;user-select:none;white-space:nowrap;margin-left:10px;flex:0 0 auto"><input type="checkbox" onchange="pmToggleHidden(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 메모 표시</label>
        <label style="display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:#6b7280;cursor:pointer;user-select:none;white-space:nowrap;margin-left:10px;flex:0 0 auto"><input type="checkbox" onchange="projToggleHiddenP(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 프로젝트 표시</label>""",
 """<label style="display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:#6b7280;cursor:pointer;user-select:none;white-space:nowrap;margin-left:10px;flex:0 0 auto"><input type="checkbox" onchange="projToggleHiddenP(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 프로젝트 표시</label>
        <label style="display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:#6b7280;cursor:pointer;user-select:none;white-space:nowrap;margin-left:10px;flex:0 0 auto"><input type="checkbox" onchange="pmToggleHidden(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 메모 표시</label>""", 1),

# (2a) colgroup: 등록일(16.66) 이 첫 열, 프로젝트명(33.36) 이 둘째 열
("""      + '<colgroup><col style="width:33.36%"><col style="width:16.66%"><col style="width:16.66%"><col style="width:16.66%"><col style="width:16.66%"></colgroup>'""",
 """      + '<colgroup><col style="width:16.66%"><col style="width:33.36%"><col style="width:16.66%"><col style="width:16.66%"><col style="width:16.66%"></colgroup>'""", 1),

# (2b) 헤더 순서
("""      +   '<th style="'+TH+'">프로젝트명</th><th style="'+TH+'">등록자</th><th style="'+TH+'">등록일</th><th style="'+TH+'">최근 기록</th><th style="'+TH+'">기록 수</th>'""",
 """      +   '<th style="'+TH+'">등록일</th><th style="'+TH+'">프로젝트명</th><th style="'+TH+'">등록자</th><th style="'+TH+'">최근 기록</th><th style="'+TH+'">기록 수</th>'""", 1),

# (2c) 행 셀 순서 (파란 본인 표시는 등록일 칸으로)
("""        + '<td style="'+TD+';font-weight:700;color:#14305c;box-shadow:inset 3px 0 0 '+(mine?'#1B3A6B':'transparent')+'">'+titlePart+'</td>'
        + '<td style="'+TD+';text-align:center">'+esc(_projAuthor(p))+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+_projFmtD(p.createdAt)+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(lastD||'-')+'</td>'""",
 """        + '<td style="'+TD+';text-align:center;color:#6b7280;box-shadow:inset 3px 0 0 '+(mine?'#1B3A6B':'transparent')+'">'+_projFmtD(p.createdAt)+'</td>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+titlePart+'</td>'
        + '<td style="'+TD+';text-align:center">'+esc(_projAuthor(p))+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(lastD||'-')+'</td>'""", 1),
]

def apply_r121(s, path):
    for i,(old,new,exp) in enumerate(R121_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R121 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r121(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r120 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r120 2026-08-21 -->', '<!-- test build r121 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
