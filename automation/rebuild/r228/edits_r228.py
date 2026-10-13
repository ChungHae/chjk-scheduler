# -*- coding: utf-8 -*-
# r228 (사용자 요청 2026-10-13): 견적 다운로드를 r218 이전처럼 **PDF 만** 받도록 되돌린다.
#   r218 에서 PDF 와 함께 엑셀(.xlsx)을 자동 저장했고 r223 에서 그 엑셀을 고객용 견적서로 바꿨는데, 이제 엑셀은 같이 내려보내지 않는다.
#   - 두 경로(미리보기 [저장 후 다운로드], qSavePdfQuote → qDownloadPdf) 모두에서 _qPrepQuoteXlsx / _qSaveQuoteXlsx 호출 제거
#   - 확인창·완료 안내문을 "PDF 파일을 다운로드합니다" / "PDF 로 내려받았습니다" 로 환원
#   - 고객용 견적서 워크북 생성기(_qBuildQuoteSheetWb, r223)와 _qPrepQuoteXlsx/_qSaveQuoteXlsx 는 **지우지 않고 남겨둔다**
#     (나중에 버튼 하나로 다시 쓸 수 있게). '일반 엑셀' 버튼(견적목록 엑셀, exportQuoteExcel)은 손대지 않는다.
import io, sys

OPS = [
 # ① qDownloadPdf — 엑셀 준비·저장 제거
 ["    var _xwb=await _qPrepQuoteXlsx();   // r218\n"
  "    pm.createPdf(dd).download(_fn+'.pdf');\n"
  "    _qSaveQuoteXlsx(_xwb, _fn);   // r218\n",
  "    pm.createPdf(dd).download(_fn+'.pdf');   // r228: PDF 만 (엑셀 동시 저장 제거)\n",
  1, "DL"],
 # ② 미리보기 [저장 후 다운로드] — 엑셀 준비 제거
 ["            var _saved=true;   // r186\n            var _xwb=await _qPrepQuoteXlsx();   // r218\n",
  "            var _saved=true;   // r186\n",
  1, "PV_PREP"],
 # ③ 미리보기 — 엑셀 저장 제거
 ["              _qSaveQuoteXlsx(_xwb, _fn);   // r218\n", "", 1, "PV_SAVE"],
 # ④ 확인창 문구 (두 경로)
 ["'견적번호 <b>'+esc(no)+'</b> 로 저장 후 PDF 와 엑셀 파일을 함께 다운로드합니다.\\n\\n파일명 · 견적서 '+esc(no)+'.pdf / .xlsx'",
  "'견적번호 <b>'+esc(no)+'</b> 로 저장 후 PDF 파일을 다운로드합니다.\\n\\n파일명 · 견적서 '+esc(no)+'.pdf'",
  2, "CONFIRM"],
 # ⑤ 완료 안내문 (두 경로)
 ["견적을 저장하고 PDF·엑셀로 내려받았습니다.", "견적을 저장하고 PDF 로 내려받았습니다.", 2, "DONE"],
 # ⑥ 남겨두는 헬퍼에 표시
 ["  async function _qPrepQuoteXlsx(){ try{ await _ensureXlsxLib(); return _qBuildQuoteSheetWb(); }catch(_e){ return null; } }   // r223: PDF 와 같은 모양의 고객용 견적서",
  "  // r228: 아래 두 개와 _qBuildQuoteSheetWb 는 지금은 쓰지 않는다 (PDF 만 내려감). 고객용 견적서 엑셀을 다시 쓰려면 이 둘을 호출하면 된다.\n"
  "  async function _qPrepQuoteXlsx(){ try{ await _ensureXlsxLib(); return _qBuildQuoteSheetWb(); }catch(_e){ return null; } }   // r223: PDF 와 같은 모양의 고객용 견적서",
  1, "KEEP"],
]

MARKER = ["<!-- test build r227 2026-10-13 -->", "<!-- test build r228 2026-10-13 -->"]

# 적용 후 남아 있으면 안 되는 것
FORBIDDEN = ["_qSaveQuoteXlsx(_xwb", "PDF 와 엑셀 파일을 함께", "PDF·엑셀로 내려받았습니다"]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R228 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def apply_r228(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    for w in FORBIDDEN:
        if w in s: raise SystemExit('R228 FAIL 잔재 남음: %s (%d)' % (w, s.count(w)))
    # 고객용 견적서 생성기는 남아 있어야 한다
    for w in ['_qBuildQuoteSheetWb', '_qPrepQuoteXlsx', '_qSaveQuoteXlsx', '_qBuildQuoteXlsxWb', 'exportQuoteExcel']:
        if w not in s: raise SystemExit('R228 FAIL %s 가 사라짐' % w)
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r228(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r228 applied:', path)
