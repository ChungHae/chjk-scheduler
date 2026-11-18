// r273 적용기 — 거래명세서 탭(직접 입력·견적 불러오기·인쇄·PDF·메일) + 홈택스 세금계산서 일괄발급 엑셀. r272 바탕.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r273_module.js'),'utf8');
function r273Apply(s, isTest, marker){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R273 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var ANCH="  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238";
  var OPS=[
    ['  <button class="page-tab" data-page="order">발주</button><!-- r267 -->', '  <button class="page-tab" data-page="order">발주</button><!-- r267 -->\n  <button class="page-tab" data-page="stmt">거래명세서</button><!-- r273 -->', 1, "TAB"],
    ['  <div id="pageOrder" class="page-section"></div><!-- r267 대성 발주 -->', '  <div id="pageOrder" class="page-section"></div><!-- r267 대성 발주 -->\n  <div id="pageStmt" class="page-section"></div><!-- r273 거래명세서 -->', 1, "PAGE"],
    ["rules:'pageRules', order:'pageOrder' };", "rules:'pageRules', order:'pageOrder', stmt:'pageStmt' };", 1, "MAP"],
    ["    if (page === 'order'){ try{ renderOrderPage(); }catch(_e){} }   // r267", "    if (page === 'order'){ try{ renderOrderPage(); }catch(_e){} }   // r267\n    if (page === 'stmt'){ try{ renderStmtPage(); }catch(_e){} }   // r273", 1, "SWITCH"],
    [ANCH, MOD+ANCH, 1, "JS"]
  ];
  if(isTest) OPS.push([marker[0], marker[1], 1, "MARKER"]);
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r273Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test';
  fs.writeFileSync(out, r273Apply(fs.readFileSync(src,'utf8'), isTest, ['<!-- test build r272 2026-11-17 -->','<!-- test build r273 2026-11-18 -->'])); console.log('ok →', out); }
