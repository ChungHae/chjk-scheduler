// r257 적용기 — 업체·매입처 담당자 메일 바로 보내기(전산 발송 + 네이버 웍스에서 쓰기). r256 바탕 위에 적용.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r257_module.js'),'utf8');
function r257Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R257 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var MAILBTN='<button type="button" class="clx-mail-btn" onclick="clxMailOpen(event,this.closest(\\\'tr\\\').dataset.nm)" title="이 업체 담당자에게 메일" aria-label="메일"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16v12H4z"/><path d="m4 7 8 6 8-6"/></svg></button>';
  var OPS=[
    ["<th style=\"'+TH+'\">FAX</th>'", "<th style=\"'+TH+'\">FAX</th><th style=\"'+TH+'\">메일</th>'", 1, "CLX_TH"],
    ["<col style=\"width:130px\"><col style=\"width:130px\"></colgroup>'", "<col style=\"width:130px\"><col style=\"width:130px\"><col style=\"width:56px\"></colgroup>'", 1, "CLX_COL"],
    ["'+esc(inf.fax||'')+'</td>'", "'+esc(inf.fax||'')+'</td>'\n            + '<td style=\"'+TD+';text-align:center;padding:4px\">'+(_mailAddrBook(nm).length?'"+MAILBTN+"':'<span style=\"color:#d1d5db\" title=\"저장된 메일 주소 없음 — 펼쳐서 담당자 메일을 넣어 주세요\">"+MAILBTN.replace('class="clx-mail-btn"','class="clx-mail-btn" style="color:#d1d5db"')+"</span>')+'</td>'   // r257", 1, "CLX_TD"],
    ["colspan=\"7\" style=\"padding:0;border-bottom:2px solid #1B3A6B", "colspan=\"8\" style=\"padding:0;border-bottom:2px solid #1B3A6B", 1, "CLX_SPAN"],
    ["<a href=\"mailto:${esc(c.email)}\" style=\"color:#1a1a1a;", "<a href=\"mailto:${esc(c.email)}\" onclick=\"pvMailOpen(event,'${v.id}','${esc(c.email)}')\" title=\"메일 보내기\" style=\"color:#1B3A6B;", 1, "PV_MAILTO"],
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  (function(){ var st=document.createElement('style'); st.textContent='.clx-mail-btn{background:none;border:none;cursor:pointer;color:#1B3A6B;padding:2px 4px;display:inline-flex;align-items:center;border-radius:4px} .clx-mail-btn:hover{background:#eaf1fb}'; document.head.appendChild(st); })();\n  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r256 2026-11-09 -->", "<!-- test build r257 2026-11-09 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r257Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r257Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
