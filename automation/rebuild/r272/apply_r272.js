// r272 적용기 — 휴대폰 견적 화면(툴바 줄바꿈 수정 + 카드형 품목). live·test 공용.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r272_module.js'),'utf8');
var CSS=fs.readFileSync(path.join(__dirname,'r272_css.txt'),'utf8');
function r272Apply(s, isTest, marker){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R272 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var A="      #qResults, #qCart { overflow-x: auto; -webkit-overflow-scrolling: touch; }\n    }\n";
  var OPS=[[A, A+CSS, 1, "CSS"], ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"]];
  if(isTest) OPS.push([marker[0], marker[1], 1, "MARKER"]);
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r272Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test';
  fs.writeFileSync(out, r272Apply(fs.readFileSync(src,'utf8'), isTest, ['<!-- test build r271 2026-11-17 -->','<!-- test build r272 2026-11-17 -->'])); console.log('ok →', out); }
