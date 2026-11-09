// r262 적용기 — 규격 옵션 설명(툴팁·우클릭 옵션 보기·팀 공용 사전) + 변경 제안(대체 품번 줄·이력·여러 줄 등록). r261 바탕.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r262_module.js'),'utf8');
function r262Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R262 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    ["  let pvInq = load('sched_pv_inq') ?? [];", "  let pvInq = load('sched_pv_inq') ?? [];\n  let optDict = load('sched_opt_dict') ?? {series:{},tok:{}};   // r262 규격 옵션 설명 {series:{PF2M7:'..'}, tok:{'PF2M7|DW':'..','*|25A':'..'}}\n  let altSugg = load('sched_alt_sugg') ?? {};   // r262 변경 제안 이력 {normSpec:[{orig,alt,reason,by,at}]}", 1, "KEY_DECL"],
    ["    save('sched_pv_inq', pvInq);   // r255", "    save('sched_pv_inq', pvInq);   // r255\n    save('sched_opt_dict', optDict); save('sched_alt_sugg', altSugg);   // r262", 1, "KEY_SAVE"],
    ["sched_pv_inq: pvInq,", "sched_pv_inq: pvInq, sched_opt_dict: optDict, sched_alt_sugg: altSugg,", 2, "KEY_PAYLOAD"],
    ["    pvInq            = load('sched_pv_inq') ?? [];   // r255", "    pvInq            = load('sched_pv_inq') ?? [];   // r255\n    optDict          = load('sched_opt_dict') ?? {series:{},tok:{}}; altSugg = load('sched_alt_sugg') ?? {};   // r262", 1, "KEY_RELOAD"],
    ["'sched_client_pend','sched_pv_inq',", "'sched_client_pend','sched_pv_inq','sched_opt_dict','sched_alt_sugg',", -1, "KEY_LISTS"],
    ["data-mf=\"spec\" autocomplete=\"off\" placeholder=\"", "data-mf=\"spec\" '+_qSpecAttrs(c,i)+' autocomplete=\"off\" placeholder=\"", 1, "SPEC_ATTRS"],
    ["      if(c.disc!=null&&String(c.disc).trim()!=='') row.disc=c.disc; else delete row.disc;   // 단종/변경 동기화 (숫자 판매가로 바꾸면 해제)",
     "      if(!c.altOff){ if(c.disc!=null&&String(c.disc).trim()!=='') row.disc=c.disc; else delete row.disc; }   // 단종/변경 동기화 (숫자 판매가로 바꾸면 해제) · r262: 변경 제안 표시는 이 견적에만", 1, "FLUSH_DISC"],
    ["      row.eta =c.eta||'';", "      if(!c.altOf) row.eta =c.eta||'';   // r262: '변경 제안 · 사유' 는 원장 납기에 남기지 않음", 1, "FLUSH_ETA"],
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r261 2026-11-09 -->", "<!-- test build r262 2026-11-09 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; var exp=o[2]; if(o[3]==='KEY_LISTS') exp=isTest?3:2; s=rep(s, o[0], o[1], exp, o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r262Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r262Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
