// r265 적용기 — 매입처 문의 메일 간단 디자인(받는 사람·참조·제목·본문만, 품번은 본문에). r264 바탕(live 는 r263 바탕에도 적용 가능).
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r265_module.js'),'utf8');
function r265Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R265 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r264 2026-11-10 -->", "<!-- test build r265 2026-11-11 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r265Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r265Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
