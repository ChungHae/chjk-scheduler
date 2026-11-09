// r261 적용기 — ① 규격 칸 한 품번 붙여넣기 → 같은 규격 있으면 클릭 없이 바로 채움 ② 메일 발송·엑셀·HTML·히트판 다운로드 뒤 자동 저장 확인 + 목록 비우기 + [다시 열기]. r260 바탕.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r261_module.js'),'utf8');
function r261Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R261 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    ["    if(txt && (txt.indexOf('\\t')>=0 || txt.indexOf('\\n')>=0)){ ev.preventDefault(); _qgPasteText(txt); }\n  }, true);",
     "    if(txt && (txt.indexOf('\\t')>=0 || txt.indexOf('\\n')>=0)){ ev.preventDefault(); _qgPasteText(txt); }\n    else if(txt && String(txt).trim() && el.getAttribute('data-mf')==='spec'){ ev.preventDefault(); _qPasteSpecAuto(el, String(txt)); }   // r261\n  }, true);", 1, "PASTE"],
    ["      XLSX.writeFile(wb, _fn+'.xlsx');\n      if(_qQuoteNo) showInfoModal('자동 저장', '이 견적은 \"'+esc(_qQuoteNo)+'\" 번호로 자동 저장되었습니다.');",
     "      XLSX.writeFile(wb, _fn+'.xlsx');\n      _qAfterOut('엑셀 다운로드');   // r261", 1, "XLSX"],
    ["if(_qQuoteNo) showInfoModal('HTML 견적서', '\"'+esc(_fn)+'.html\" 로 내려받았습니다. 카톡·메일에 파일 그대로 첨부하면 받는 쪽은 클릭만 하면 됩니다.\\n이 견적은 \"'+esc(_qQuoteNo)+'\" 번호로 자동 저장되었습니다.');",
     "_qAfterOut('HTML 다운로드');   // r261", 1, "HTML"],
    ["    var ov=document.getElementById('qHitpanOverlay'); if(ov) ov.style.display='none';\n    try{\n      await _ensureXlsxLib();",
     "    var ov=document.getElementById('qHitpanOverlay'); if(ov) ov.style.display='none';\n    try{\n      await _ensureXlsxLib();\n      try{ await _qPersistQuote(); }catch(_pe){ showInfoModal('견적 저장 실패', (_pe&&_pe.message||String(_pe))+'\\n\\n히트판 엑셀은 계속 만들지만, 이 견적은 저장되지 않았습니다.'); }   // r261", 1, "HITPAN_SAVE"],
    ["      XLSX.writeFile(wb,'히트판_'+vn+'_'+ds+'.xlsx');", "      XLSX.writeFile(wb,'히트판_'+vn+'_'+ds+'.xlsx');\n      _qAfterOut('히트판 엑셀');   // r261", 1, "HITPAN_CLEAR"],
    ["      document.getElementById('mailSendOverlay').style.display='none';\n      showInfoModal('메일 발송 완료'",
     "      document.getElementById('mailSendOverlay').style.display='none';\n      setTimeout(function(){ try{ _qAfterOut('메일 발송'); }catch(_e){} }, 0);   // r261\n      showInfoModal('메일 발송 완료'", 1, "MAIL"],
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r260 2026-11-09 -->", "<!-- test build r261 2026-11-09 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r261Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r261Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
