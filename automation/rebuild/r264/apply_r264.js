// r264 적용기 — 견적 메일 참조 아래 [사업자등록증][통장사본] 클릭 첨부 (지점별, Firebase 저장). r263 바탕(다른 대화창 r263 구매링크 포함).
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r264_module.js'),'utf8');
function r264Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R264 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    ["+'<div><div style=\"'+_MLL+'\">참조(CC)</div><input id=\"mlCc\" value=\"'+esc(cfg.cc||'')+'\" style=\"'+_MLI+'\"></div>'",
     "+'<div><div style=\"'+_MLL+'\">참조(CC) <span style=\"font-weight:400;color:#9ca3af\">— 아래 서류를 누르면 메일에 같이 첨부됩니다</span></div><input id=\"mlCc\" value=\"'+esc(cfg.cc||'')+'\" style=\"'+_MLI+'\"><div id=\"mlDocs\" class=\"ml-docs\"></div></div>'   // r264", 1, "CC_DOCS"],
    ["    window._mlDraft=d;\n    window._mlDraftBody=d.body;", "    window._mlDraft=d;\n    window._mlDraftBody=d.body;\n    window._mlDocSel={biz:false, bank:false}; try{ _mlDocsRender(); }catch(_e){}   // r264", 1, "OPEN_DOCS"],
    ["  window.mlAcctChanged=function(){   // r238", "  window.mlAcctChanged=function(){ setTimeout(function(){ try{ _mlDocsRender(); }catch(_e){} },0);   // r238 · r264", 1, "ACCT_DOCS"],
    ["      st.textContent='발송 중…';\n      var html='<div style=\"font-family", "      if(window._mlDocSel && (window._mlDocSel.biz||window._mlDocSel.bank)){ st.textContent='서류 첨부 중…'; atts=atts.concat(await _mlDocAtts()); }   // r264\n      st.textContent='발송 중…';\n      var html='<div style=\"font-family", 1, "SEND_DOCS"],
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r263 2026-11-10 -->", "<!-- test build r264 2026-11-10 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r264Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r264Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
