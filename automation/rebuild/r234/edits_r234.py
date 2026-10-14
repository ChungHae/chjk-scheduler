# -*- coding: utf-8 -*-
# r234 (사용자 요청 2026-10-14): 견적서(PDF·엑셀·HTML) 안내문에 온라인몰 airmall24.co.kr 안내 한 줄 추가.
#   PDF 는 두 경로(미리보기 HTML 인쇄판 / pdfmake 다운로드판) 모두. pdfmake 는 안내문 줄 수로 세로 중앙을 맞추므로 _noteN 3→4.
import io, sys, json

LINE = '· 온라인몰 airmall24.co.kr 에서도 바로 주문하실 수 있습니다.'

OPS = [
  # ① PDF 미리보기(인쇄판 HTML)
  ["· 결제 및 납기 조건은 협의에 따릅니다. — ${SUP.corp}</div>",
   "· 결제 및 납기 조건은 협의에 따릅니다.<br>· 온라인몰 <b>airmall24.co.kr</b> 에서도 바로 주문하실 수 있습니다. — ${SUP.corp}</div>", 1, "PDF_PREVIEW"],
  # ② 엑셀(일반 엑셀 = 고객용 견적서)
  ["notes.push('· 결제 및 납기 조건은 협의에 따릅니다. — '+SUP.corp);",
   "notes.push('· 결제 및 납기 조건은 협의에 따릅니다.'); notes.push('" + LINE + " — '+SUP.corp);", 1, "XLSX"],
  # ③ pdfmake 다운로드판
  ["noteLines.push({text:'· 결제 및 납기 조건은 협의에 따릅니다. — '+SUP.corp});",
   "noteLines.push({text:'· 결제 및 납기 조건은 협의에 따릅니다.'}); noteLines.push({text:'" + LINE + " — '+SUP.corp});", 1, "PDFMAKE"],
  ["var _noteN=3+(_qMemo?String(_qMemo).split('\\n').length:0);",
   "var _noteN=4+(_qMemo?String(_qMemo).split('\\n').length:0);   // r234: 온라인몰 안내 한 줄 추가", 1, "PDFMAKE_N"],
  # ④ HTML 견적서(r233) 확인 사항 + 꼬리말
  ["'표기 품번 외 옵션(오토스위치·포트 나사·스트로크 등) 변경이 필요하시면 알려주십시오. 추가 견적드리겠습니다.'\n    ];",
   "'표기 품번 외 옵션(오토스위치·포트 나사·스트로크 등) 변경이 필요하시면 알려주십시오. 추가 견적드리겠습니다.',\n      '온라인몰 <a href=\"https://airmall24.co.kr\" target=\"_blank\" rel=\"noopener\" style=\"color:#1B3A6B;font-weight:700\">airmall24.co.kr</a> 에서도 바로 주문하실 수 있습니다.'\n    ];", 1, "HTML_NOTE"],
  ["· 결제 및 납기 조건은 협의에 따릅니다.<br>· 자료 링크는",
   "· 결제 및 납기 조건은 협의에 따릅니다. · 온라인몰 airmall24.co.kr<br>· 자료 링크는", 1, "HTML_FOOT"],
  ["<!-- test build r233 2026-10-14 -->", "<!-- test build r234 2026-10-14 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R234 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r234(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r234 브라우저 적용기 — edits_r234.py 의 OPS. r233 적용본 위에 적용.",
             "function r234Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R234 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r234Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r234(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r234 applied:', path)
