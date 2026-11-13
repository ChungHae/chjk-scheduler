// r269 적용기 — SMC 확인: SMC 품번조회에 안 나오는 품번을 '타사' 칸으로 따로 관리. r268 바탕.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r269_module.js'),'utf8');
function r269Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R269 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    ["없는 품번 '+r.none.length+'건 제외로", "SMC 에 없음 '+r.none.length+'건 → 타사로", 1, "LABEL"],
    ["  window.smcSkip = function(id){", MOD+"  window.smcSkip = function(id){", 1, "JS"],
    ["<!-- test build r268 2026-11-13 -->", "<!-- test build r269 2026-11-13 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r269Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r269Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
