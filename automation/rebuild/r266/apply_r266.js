// r266 적용기 — 견적 → 대성산업 WMIS 발주 (Worker 중계). r265 바탕.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r266_module.js'),'utf8');
var BTN='<button class="qic" id="qDsBtn" onclick="qDsOpen()" data-tip="대성 발주 (WMIS)" aria-label="대성 발주" style="border-color:#c2410c;color:#c2410c"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7h11v9H3z"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/></svg></button>';
function r266Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R266 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var bulk=s.match(/      <button class="qic" id="qBulkBtn"[^\n]*\n/);
  if(!bulk) throw new Error('R266 FAIL qBulkBtn line');
  var OPS=[
    [bulk[0], bulk[0]+'      '+BTN+'\n', 1, "BTN"],
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r265 2026-11-11 -->", "<!-- test build r266 2026-11-12 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r266Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r266Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
