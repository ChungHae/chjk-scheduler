// r267 적용기 — 대성 발주를 견적 화면 버튼(r266)에서 '발주' 탭(페이지)으로 옮김. r266 바탕.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r267_module.js'),'utf8');
var R266=fs.readFileSync(path.join(__dirname,'..','r266','r266_module.js'),'utf8');
var BTN266='      <button class="qic" id="qDsBtn" onclick="qDsOpen()" data-tip="대성 발주 (WMIS)" aria-label="대성 발주" style="border-color:#c2410c;color:#c2410c"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7h11v9H3z"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/></svg></button>\n';
function r267Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R267 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    [R266, MOD, 1, "MODULE"],
    [BTN266, '', 1, "QBTN"],
    ['  <button class="page-tab" data-page="estimate">견적</button>\n', '  <button class="page-tab" data-page="estimate">견적</button>\n  <button class="page-tab" data-page="order">발주</button><!-- r267 -->\n', 1, "TAB"],
    ['  <div id="pagePurchase" class="page-section">', '  <div id="pageOrder" class="page-section"></div><!-- r267 대성 발주 -->\n  <div id="pagePurchase" class="page-section">', 1, "SECTION"],
    ["cardsales:'pageCardSales', rules:'pageRules' };", "cardsales:'pageCardSales', rules:'pageRules', order:'pageOrder' };", 1, "PAGEMAP"],
    ["    if (page === 'purchase'){\n      var _ps=document.getElementById('purchaseSearch');", "    if (page === 'order'){ try{ renderOrderPage(); }catch(_e){} }   // r267\n    if (page === 'purchase'){\n      var _ps=document.getElementById('purchaseSearch');", 1, "HOOK"],
    ["<!-- test build r266 2026-11-12 -->", "<!-- test build r267 2026-11-12 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r267Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r267Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
