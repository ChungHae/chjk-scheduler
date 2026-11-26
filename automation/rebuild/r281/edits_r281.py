# -*- coding: utf-8 -*-
# r281 — 감사 거래명세표 줄 정리 (사용자 지시 2026-11-26)
#   ① 접기/펼치기 단추를 줄 맨 앞(물류출하일 왼쪽)으로
#   ② 전표가 여러 줄일 때 항목(물류출하일·발행일·번호·품목·금액·비고)이 세로로 딱 맞게 — flex → 고정폭 grid
#   ③ 세부 내역 표의 '수량' 은 가운데 정렬
#  사용:  python3 edits_r281.py <index.html> [--test]
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

assert 'as-doc-row' not in s, 'FORBIDDEN(이미 r281 적용됨)'

# ①② 전표 줄 — 단추를 맨 앞으로, 칸을 고정폭 grid 로 맞춘다
rep("""          + '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;font-size:12.5px">'
          + '<span style="color:#8a94a6">물류출하일 '+esc(_asDot(d.ship))+'</span>'
          + '<span>발행일 <b>'+esc(d.date)+'</b></span>'
          + '<span>번호 <input value="'+(d.no==null?'':d.no)+'" oninput="asSetNo('+di+','+ci+',this.value)" style="width:48px;height:26px;text-align:center;padding:0 4px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit"></span>'
          + '<button type="button" onclick="asToggleDoc('+di+','+ci+')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:12px;padding:2px 9px;cursor:pointer;font-family:inherit;color:#1B3A6B">'
          +   (d.open?'\\u25be':'\\u25b8')+' '+d.rows.length+'품목 · '+pages+'장'
          + '</button>'
          + '<span>공급가액 <b>'+_asNum(supply)+'</b> · 세액 <b>'+_asNum(tax)+'</b> · 합계 <b>'+_asNum(supply+tax)+'</b></span>'
          + '<span style="flex:1"></span>'
          + '<span>비고 <input value="'+esc(d.memo||'')+'" oninput="asSetMemo('+di+','+ci+',this.value)" placeholder="(선택)" style="width:150px;height:26px;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit"></span>'
          + '</div>'""",
    """          // r281: 전표가 여러 줄이어도 항목이 세로로 맞도록 고정폭 격자. 접기 단추가 맨 앞.
          + '<div class="as-doc-row">'
          + '<button type="button" onclick="asToggleDoc('+di+','+ci+')" style="border:1px solid #c8d2de;background:#fff;border-radius:0;font-size:12px;padding:3px 9px;cursor:pointer;font-family:inherit;color:#1B3A6B;text-align:left">'
          +   (d.open?'\\u25be':'\\u25b8')+' '+d.rows.length+'품목 · '+pages+'장'
          + '</button>'
          + '<span style="color:#8a94a6">물류출하일 '+esc(_asDot(d.ship))+'</span>'
          + '<span>발행일 <b>'+esc(d.date)+'</b></span>'
          + '<span>번호 <input value="'+(d.no==null?'':d.no)+'" oninput="asSetNo('+di+','+ci+',this.value)" style="width:48px;height:26px;text-align:center;padding:0 4px;border:1px solid #c8d2de;border-radius:0;font-size:12.5px;font-family:inherit"></span>'
          + '<span>공급가액 <b>'+_asNum(supply)+'</b> · 세액 <b>'+_asNum(tax)+'</b> · 합계 <b>'+_asNum(supply+tax)+'</b></span>'
          + '<span style="justify-self:end;white-space:nowrap">비고 <input value="'+esc(d.memo||'')+'" oninput="asSetMemo('+di+','+ci+',this.value)" placeholder="(선택)" style="width:150px;height:26px;padding:0 7px;border:1px solid #c8d2de;border-radius:0;font-size:12px;font-family:inherit"></span>'
          + '</div>'""",
    1, '①② 전표 줄 — 단추 맨 앞 + 격자 정렬')

# ①② 격자 폭 — 칸 이름이 길어져도 흔들리지 않게 고정
rep("""    #pageAudit .asvd-item:hover { background:#f4f6f9; }""",
    """    #pageAudit .asvd-item:hover { background:#f4f6f9; }
    /* r281: 거래명세표 줄 — 전표가 여러 개여도 항목이 세로로 맞게 */
    #pageAudit .as-doc-row { display:grid; grid-template-columns:128px 152px 132px 92px minmax(260px,1fr) auto; align-items:center; column-gap:14px; row-gap:6px; font-size:12.5px; }
    #pageAudit .as-doc-row > * { min-width:0; }
    @media (max-width:980px){ #pageAudit .as-doc-row { grid-template-columns:128px 152px 132px 92px; } #pageAudit .as-doc-row > *:nth-child(n+5) { grid-column:1/-1; justify-self:start !important; } }""",
    1, '② 격자 폭 규칙')

# ③ 수량은 가운데 정렬
rep("""          + '<th style="padding:4px 6px;text-align:right;width:60px">수량</th>""",
    """          + '<th style="padding:4px 6px;text-align:center;width:60px">수량</th>""",
    1, '③ 수량 머리 가운데')

rep("""            + '<td style="padding:3px 6px;text-align:right">'+_asNum(r.qty)+'</td>'""",
    """            + '<td style="padding:3px 6px;text-align:center">'+_asNum(r.qty)+'</td>'""",
    1, '③ 수량 칸 가운데')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r281 2026-11-26 -->')
    print('  ok  test marker %s -> r281' % m.group(0))

for k in ['as-doc-row', '#pageAudit .as-doc-row { display:grid',
          'text-align:center;width:60px">수량</th>',
          'padding:3px 6px;text-align:center']:
    assert k in s, 'NEED missing: ' + k
for k in ['asToggleDoc', 'asSetNo', 'asSetMemo', 'renderAuditPage']:
    assert k in s, 'KEEP missing: ' + k
assert 'display:flex;align-items:center;gap:12px;flex-wrap:wrap;font-size:12.5px' not in s, 'FORBIDDEN: 옛 flex 줄이 남아 있다'

io.open(path, 'w', encoding='utf-8').write(s)
print('r281 적용 완료: %d -> %d' % (orig, len(s)))
