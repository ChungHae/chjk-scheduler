// r270 적용기 — 발주 탭: 견적 E가·구매가·판매가·견적 DC·대성가 표시, DC율 이상만 선택, 줄 삭제, 수량 그대로, 기타요청사항 비움,
//  대성 연결을 메일 서버(mail/worker.js v3 /wmis/*)로 합쳐 [대성 설정]에 아이디·비밀번호만. r269 바탕(r267 모듈 교체).
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r270_module.js'),'utf8');
var R267=fs.readFileSync(path.join(__dirname,'..','r267','r267_module.js'),'utf8');
function r270Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R270 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    [R267, MOD, 1, "MODULE"],
    ["<!-- test build r269 2026-11-13 -->", "<!-- test build r270 2026-11-13 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r270Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r270Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
