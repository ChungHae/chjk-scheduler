// r268 적용기 — SMC 확인: 표 오른쪽 '처리' 칸 잘림 수정 + SMC 품번일괄조회 결과로 일괄 등록. live(r265)·test(r267) 공용.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r268_module.js'),'utf8');
var CSS="    #qSubSmc #smcResult .smc-st { font-size:11px; color:#6b7280; }\n"
 +"    /* r268: 처리(등록·제외) 칸이 화면 밖으로 밀려 잘리지 않게 — 오른쪽에 붙이고, 긴 품목명·거래처는 줄임 */\n"
 +"    #qSubSmc #smcResult table tr > *:last-child { position:sticky; right:0; background:#fff; z-index:3; box-shadow:-3px 0 6px rgba(15,23,42,.06); border-right:none; }\n"
 +"    #qSubSmc #smcResult table thead tr > *:last-child { position:sticky !important; right:0; background:#f8fafc; z-index:6; }\n"
 +"    #qSubSmc #smcResult td:nth-child(3), #qSubSmc #smcResult td:nth-child(8), #qSubSmc #smcResult td:nth-child(11) { max-width:170px; overflow:hidden; text-overflow:ellipsis; }\n"
 +"    #qSubSmc #smcResult input.smc-in { width:76px; }\n";
function r268Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R268 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    ["    #qSubSmc #smcResult .smc-st { font-size:11px; color:#6b7280; }\n", CSS, 1, "CSS"],
    ["+'<a href=\"http://www.smckorea.net/main/main.jsp\" target=\"_blank\" rel=\"noopener\" class=\"smc-f\">SMC 사이트 열기</a>'   // r182",
     "+'<a href=\"http://www.smckorea.net/main/main.jsp\" target=\"_blank\" rel=\"noopener\" class=\"smc-f\">SMC 사이트 열기</a>'   // r182\n      +'<button class=\"smc-f\" onclick=\"smcBulkOpen()\" style=\"background:#1d4ed8;color:#fff;border-color:#1d4ed8;font-weight:700\">SMC 일괄 확인</button>'   // r268", 1, "BTN"],
    ["  window.smcSkip = function(id){", MOD+"  window.smcSkip = function(id){", 1, "JS"],
    ["<!-- test build r267 2026-11-12 -->", "<!-- test build r268 2026-11-13 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r268Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r268Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
