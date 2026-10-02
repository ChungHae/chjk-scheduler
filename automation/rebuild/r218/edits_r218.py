# -*- coding: utf-8 -*-
# r218 (사용자 요청 2026-10-02): 견적서를 PDF 로 내보낼 때 같은 견적의 엑셀(.xlsx)도 동시에 같이 내려받는다.
#   - 엑셀 워크북 생성부를 _qBuildQuoteXlsxWb() 로 분리(일반 엑셀 버튼과 공용)
#   - PDF 미리보기 [저장 후 다운로드] · qDownloadPdf 두 경로 모두 PDF 다음에 엑셀을 이어서 저장 (파일명 동일: 견적서 <번호>.xlsx)
import io, sys, json

OPS = [
 # ① exportQuoteExcel 머리: 워크북 생성을 함수로 분리
 [
  "      try{ await _qPersistQuote(); }catch(_pe){ showInfoModal('견적 저장 실패', (_pe&&_pe.message||String(_pe))+'\\n\\n엑셀은 계속 만들지만, 이 견적은 저장되지 않았습니다.'); }\n      var totalBuy=0, totalSell=0, totalQty=0;\n",
  "      try{ await _qPersistQuote(); }catch(_pe){ showInfoModal('견적 저장 실패', (_pe&&_pe.message||String(_pe))+'\\n\\n엑셀은 계속 만들지만, 이 견적은 저장되지 않았습니다.'); }\n      var wb=_qBuildQuoteXlsxWb();   // r218\n      var vn=(_qCart[0].vname||'견적'); var d=new Date();\n      var ds=d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0');\n      XLSX.writeFile(wb,'견적목록_'+vn+'_'+ds+'.xlsx');\n      if(_qQuoteNo) showInfoModal('자동 저장', '이 견적은 \"'+esc(_qQuoteNo)+'\" 번호로 자동 저장되었습니다.');\n    }catch(e){ showInfoModal('알림', '엑셀 내보내기 실패: '+e.message); }\n  };\n  function _qBuildQuoteXlsxWb(){   // r218: 견적목록 엑셀 워크북 — 일반 엑셀 버튼과 PDF 동시 다운로드가 같이 쓴다 (XLSX 로드 후 호출)\n      var totalBuy=0, totalSell=0, totalQty=0;\n",
  1, "XLSX_HEAD"
 ],
 # ② exportQuoteExcel 꼬리: 워크북을 돌려준다
 [
  "      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb,ws,'견적목록');\n      var vn=(_qCart[0].vname||'견적'); var d=new Date();\n      var ds=d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0');\n      XLSX.writeFile(wb,'견적목록_'+vn+'_'+ds+'.xlsx');\n      if(_qQuoteNo) showInfoModal('자동 저장', '이 견적은 \"'+esc(_qQuoteNo)+'\" 번호로 자동 저장되었습니다.');\n    }catch(e){ showInfoModal('알림', '엑셀 내보내기 실패: '+e.message); }\n  };",
  "      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb,ws,'견적목록');\n      return wb;\n  }\n  // r218: PDF 와 같은 이름(견적서 <번호>.xlsx)으로 엑셀을 이어서 저장. 목록을 비우기 전에 미리 만들어 둔 워크북을 쓴다.\n  async function _qPrepQuoteXlsx(){ try{ await _ensureXlsxLib(); return _qBuildQuoteXlsxWb(); }catch(_e){ return null; } }\n  function _qSaveQuoteXlsx(wb, fn){ if(!wb) return; setTimeout(function(){ try{ XLSX.writeFile(wb, fn+'.xlsx'); }catch(_e){} }, 600); }",
  1, "XLSX_TAIL"
 ],
 # ③ 미리보기 [저장 후 다운로드]: 안내문 + 엑셀 동시 저장
 [
  "          showConfirmModal('견적서 저장', '견적번호 <b>'+esc(no)+'</b> 로 저장 후 PDF 파일을 다운로드합니다.\\n\\n파일명 · 견적서 '+esc(no)+'.pdf', function(){ (async function(){\n            var _saved=true;   // r186\n",
  "          showConfirmModal('견적서 저장', '견적번호 <b>'+esc(no)+'</b> 로 저장 후 PDF 와 엑셀 파일을 함께 다운로드합니다.\\n\\n파일명 · 견적서 '+esc(no)+'.pdf / .xlsx', function(){ (async function(){\n            var _saved=true;   // r186\n            var _xwb=await _qPrepQuoteXlsx();   // r218\n",
  1, "PV_CONFIRM"
 ],
 [
  "              var a=document.createElement('a'); a.href=window._qPvUrl; a.download=_fn+'.pdf';\n              document.body.appendChild(a); a.click(); a.remove();\n",
  "              var a=document.createElement('a'); a.href=window._qPvUrl; a.download=_fn+'.pdf';\n              document.body.appendChild(a); a.click(); a.remove();\n              _qSaveQuoteXlsx(_xwb, _fn);   // r218\n",
  1, "PV_DL"
 ],
 # ④ qDownloadPdf 직접 경로
 [
  "    var _fn=('견적서 '+(_qQuoteNo||'')).replace(/[<>:\"/\\\\|?*]/g,' ').replace(/\\s+/g,' ').trim();\n    pm.createPdf(dd).download(_fn+'.pdf');\n",
  "    var _fn=('견적서 '+(_qQuoteNo||'')).replace(/[<>:\"/\\\\|?*]/g,' ').replace(/\\s+/g,' ').trim();\n    var _xwb=await _qPrepQuoteXlsx();   // r218\n    pm.createPdf(dd).download(_fn+'.pdf');\n    _qSaveQuoteXlsx(_xwb, _fn);   // r218\n",
  1, "DIRECT_DL"
 ],
 # ⑤ 완료 안내문 (두 곳)
 [
  "견적을 저장하고 PDF 로 내려받았습니다.",
  "견적을 저장하고 PDF·엑셀로 내려받았습니다.",
  2, "DONE_MSG"
 ],
 [
  "로 저장 후 PDF 파일을 다운로드합니다.\\n\\n파일명 · 견적서 '+esc(no)+'.pdf', function(){ (async function(){\n      var _saved=true;   // r186\n",
  "로 저장 후 PDF 와 엑셀 파일을 함께 다운로드합니다.\\n\\n파일명 · 견적서 '+esc(no)+'.pdf / .xlsx', function(){ (async function(){\n      var _saved=true;   // r186\n",
  1, "SAVE_CONFIRM"
 ],
 [
  "<!-- test build r217 2026-10-01 -->",
  "<!-- test build r218 2026-10-02 -->",
  1, "MARKER"
 ]
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R218 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r218(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r218 브라우저 적용기 — edits_r218.py 의 OPS. r217(live 54e71557 / test 312661ce) 에 적용.",
             "function r218Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R218 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r218Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r218(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r218 applied:', path)
