// r260 적용기 — ① 타 거래처 원장에서 가져온 일반품 줄은 판매가·예상납기 비움 ② 마진율/DC율 일괄 적용(소물류 포함/제외). r259 바탕.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r260_module.js'),'utf8');
function r260Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R260 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    ["    c.disc=r.disc||''; c.eta=r.eta||'';\n    _qMarkPriceSrc(c);   // r200\n    return true;",
     "    c.disc=r.disc||''; c.eta=r.eta||'';\n    if(!_qOwnRow(r)){ c.sell=null; c.eta=''; }   // r260: 이 거래처 이력이 아니면 판매가 없음\n    _qMarkPriceSrc(c);   // r200\n    return true;", 1, "FILL_LEDGER"],
    ["    c.disc=r.disc||''; c.eta=r.eta||'';\n    _qMarkPriceSrc(c);   // r200\n    try{ _qCartCopyAbove(i); }catch(_e){}",
     "    c.disc=r.disc||''; c.eta=r.eta||'';\n    if(!_qOwnRow(r)){ c.sell=null; c.eta=''; }   // r260\n    _qMarkPriceSrc(c);   // r200\n    try{ _qCartCopyAbove(i); }catch(_e){}", 1, "SPEC_PICK"],
    ["pl:r.pl?true:false, sell:r.sell, disc:r.disc||'', eta:r.eta||'', qty:1, psrc:_qNorm(r.spec||'')});   // r200",
     "pl:r.pl?true:false, sell:(_qOwnRow(r)?r.sell:null), disc:r.disc||'', eta:(_qOwnRow(r)?(r.eta||''):''), qty:1, psrc:_qNorm(r.spec||'')});   // r200 · r260", 1, "PUSH_NEW"],
    ["      <span class=\"qic-div\" style=\"width:1px;align-self:stretch;background:#d3dae4;margin:2px 4px\"></span>\n      <button class=\"qic\" onclick=\"qCartClear()\"",
     "      <button class=\"qic\" id=\"qBulkBtn\" onclick=\"qBulkRateOpen()\" data-tip=\"마진율·DC율 일괄 적용\" aria-label=\"마진율·DC율 일괄 적용\" style=\"border-color:#0d9488;color:#0d9488\"><svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M19 5 5 19\"/><circle cx=\"7\" cy=\"7\" r=\"2.5\"/><circle cx=\"17\" cy=\"17\" r=\"2.5\"/></svg></button>\n      <span class=\"qic-div\" style=\"width:1px;align-self:stretch;background:#d3dae4;margin:2px 4px\"></span>\n      <button class=\"qic\" onclick=\"qCartClear()\"", 1, "TOOLBAR"],
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r259 2026-11-09 -->", "<!-- test build r260 2026-11-09 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r260Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r260Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
