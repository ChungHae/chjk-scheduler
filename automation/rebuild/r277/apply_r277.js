// r277 적용기 — 업무 > [감사] 하위 탭: SMC 유저특가 엑셀 → 거래명세표(양식 용지에 글자만 인쇄). r276 바탕.
//  사용:  node apply_r277.js <src index.html> <out> [test]
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r277_module.js'),'utf8');

function r277Apply(s, isTest, marker){
  function rep(str, old, nw, exp, label){
    var n=str.split(old).length-1;
    if(n!==exp) throw new Error('R277 FAIL '+label+' count '+n+' (expect '+exp+')');
    return str.split(old).join(nw);
  }
  if(s.indexOf('renderAuditPage')>=0) throw new Error('R277 FAIL 이미 적용됨(renderAuditPage 있음)');
  var ANCH="  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238";
  var OPS=[
    ['  <button class="sub-tab" data-page="links">사이트</button><!-- r276: 이름 정리 -->',
     '  <button class="sub-tab" data-page="links">사이트</button><!-- r276: 이름 정리 -->\n  <button class="sub-tab" data-page="audit">감사</button><!-- r277 -->', 1, 'SUBTAB'],
    ['  <div id="pageLinks" class="page-section">',
     '  <div id="pageAudit" class="page-section"></div><!-- r277 감사 -->\n  <div id="pageLinks" class="page-section">', 1, 'PAGE'],
    ["links:'pageLinks',", "links:'pageLinks', audit:'pageAudit',", 1, 'MAP'],
    ["var _ETC=['links'];", "var _ETC=['links','audit'];   // r277", 1, 'ETC'],
    ["    if (page === 'links')     renderLinksPage();",
     "    if (page === 'links')     renderLinksPage();\n    if (page === 'audit'){ try{ renderAuditPage(); }catch(_e){} }   // r277", 1, 'SWITCH'],
    [ANCH, MOD+ANCH, 1, 'JS']
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; s=rep(s, o[0], o[1], o[2], o[3]); }
  if(isTest) s=rep(s, marker[0], marker[1], 1, 'MARKER');
  // NEED
  ['renderAuditPage','_asBuildDraft','_asAddBizDays','_asKoAmt','_asParseFile','window.asSavePrint',
   'sched_audit_usermap','sched_audit_cfg','date.nager.at','audit_stmt','- 이 하 여 백 -']
    .forEach(function(k){ if(s.indexOf(k)<0) throw new Error('R277 NEED missing: '+k); });
  // KEEP
  ['id="tabEtc"','id="etcSubNav"','data-page="links"','renderLinksPage()','function _qBlobGet','function _qBlobPut']
    .forEach(function(k){ if(s.indexOf(k)<0) throw new Error('R277 KEEP missing: '+k); });
  return s;
}
if(typeof module!=='undefined') module.exports=r277Apply;
if(require.main===module){
  var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test';
  fs.writeFileSync(out, r277Apply(fs.readFileSync(src,'utf8'), isTest,
    ['<!-- test build r276 2026-11-26 -->','<!-- test build r277 2026-11-26 -->']));
  console.log('ok →', out);
}
