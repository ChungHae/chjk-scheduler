# -*- coding: utf-8 -*-
# r229 (사용자 요청 2026-10-13): 견적 다운로드 창의 **[일반 엑셀]** 을 r223 의 '고객용 견적서' 양식으로 바꾼다.
#   · exportQuoteExcel 이 _qBuildQuoteSheetWb() (PDF 견적서와 같은 모양 · 수식으로 재계산) 를 만들어
#     PDF 와 같은 이름 `견적서 <번호>.xlsx` 로 저장한다.
#   · 옛 '견적목록' 양식(_qBuildQuoteXlsxWb — NO/거래처/품목/…/E가/DC율/구매가/마진율, 내부 단가 포함)은 **삭제**.
#   · [히트판 엑셀](qExportHitpan)은 손대지 않는다.
import io, sys

OPS = [
 # ① exportQuoteExcel 본문: 견적목록 → 고객용 견적서
 ["      var wb=_qBuildQuoteXlsxWb();   // r218\n"
  "      var vn=(_qCart[0].vname||'견적'); var d=new Date();\n"
  "      var ds=d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0');\n"
  "      XLSX.writeFile(wb,'견적목록_'+vn+'_'+ds+'.xlsx');\n",
  "      var wb=_qBuildQuoteSheetWb();   // r229: 고객용 견적서(PDF 와 같은 모양 · 수식)\n"
  "      var _fn=('견적서 '+(_qQuoteNo||(_qCart[0].vname||'견적'))).replace(/[<>:\"/\\\\|?*]/g,' ').replace(/\\s+/g,' ').trim();\n"
  "      XLSX.writeFile(wb, _fn+'.xlsx');\n",
  1, "EXPORT"],
 # ② 남겨둔 헬퍼 주석 갱신 (r228 에서 '안 쓴다' 고 적어둔 것)
 ["  // r218: PDF 와 같은 이름(견적서 <번호>.xlsx)으로 엑셀을 이어서 저장. 목록을 비우기 전에 미리 만들어 둔 워크북을 쓴다.\n"
  "  // r228: 아래 두 개와 _qBuildQuoteSheetWb 는 지금은 쓰지 않는다 (PDF 만 내려감). 고객용 견적서 엑셀을 다시 쓰려면 이 둘을 호출하면 된다.\n",
  "  // r229: 고객용 견적서(_qBuildQuoteSheetWb)는 [일반 엑셀] 버튼이 쓴다. 아래 두 개는 PDF 와 같이 내려보내던 r218 잔재로 지금은 쓰지 않는다\n"
  "  //       (r228 에서 동시 다운로드 중단). 다시 같이 내려보내려면 이 둘을 PDF 경로에서 호출하면 된다.\n",
  1, "NOTE"],
]

# ③ 옛 견적목록 워크북 생성기 통째로 삭제
DEL_START = "  function _qBuildQuoteXlsxWb(){   // r218: 견적목록 엑셀 워크북"
DEL_END = "      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb,ws,'견적목록');\n      return wb;\n  }\n"

MARKER = ["<!-- test build r228 2026-10-13 -->", "<!-- test build r229 2026-10-13 -->"]

FORBIDDEN = ["_qBuildQuoteXlsxWb", "'견적목록_'", "book_append_sheet(wb,ws,'견적목록')"]
KEEP = ["_qBuildQuoteSheetWb", "exportQuoteExcel", "qExportHitpan", "_qPrepQuoteXlsx", "_qSaveQuoteXlsx"]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R229 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def cut(s, a, b, label):
    if s.count(a) != 1: raise SystemExit('R229 FAIL %s startAnchor %d' % (label, s.count(a)))
    if s.count(b) != 1: raise SystemExit('R229 FAIL %s endAnchor %d' % (label, s.count(b)))
    i = s.index(a); j = s.index(b, i)
    if j < i: raise SystemExit('R229 FAIL %s order' % label)
    return s[:i] + s[j + len(b):]


def apply_r229(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    s = cut(s, DEL_START, DEL_END, "DEL_LIST_WB")
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    for w in FORBIDDEN:
        if w in s: raise SystemExit('R229 FAIL 잔재 남음: %s (%d)' % (w, s.count(w)))
    for w in KEEP:
        if w not in s: raise SystemExit('R229 FAIL %s 가 사라짐' % w)
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r229(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r229 applied:', path)
