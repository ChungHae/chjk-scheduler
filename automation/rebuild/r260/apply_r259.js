// r259 적용기 — 매입처 문의 메일은 매입처 탭에서 '업체(대리점) 카드 클릭 → 작성'. 툴바 [품번 문의] 제거. r258 바탕.
var fs=require('fs');
function r259Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R259 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    // 카드 전체 클릭 → 그 대리점으로 문의 작성 (링크·버튼 클릭은 제외)
    ["html += `<div style=\"position:relative;padding:10px 12px;${idx>0?'border-top:1px solid #eef2f7':''}\">",
     "html += `<div class=\"pv-card\" onclick=\"pvCardClick(event,'${v.id}')\" title=\"눌러서 이 대리점에 견적·납기 문의 메일 쓰기\" style=\"position:relative;padding:10px 12px;cursor:pointer;${idx>0?'border-top:1px solid #eef2f7':''}\">", 1, "CARD_CLICK"],
    // 툴바 [품번 문의] 제거 (업체를 먼저 고르고 작성)
    [/      <button class="btn" id="pvInqNewBtn"[^\n]*\n/, "", 1, "TOOLBAR_REMOVE"],
    ["매입처 툴바의 [품번 문의] 또는 매입처 카드의 ✉ 에서 보냅니다.", "매입처 탭에서 대리점(업체) 카드를 누르면 문의 메일을 쓸 수 있습니다.", 1, "BOX_HINT"],
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238",
     "  // r259: 매입처 카드 클릭 → 문의 작성 (전화·메일 링크, 수정·삭제 버튼은 그대로 동작)\n  window.pvCardClick=function(ev, vid){ var t=ev&&ev.target; if(t&&t.closest&&t.closest('a,button,input,label')) return; if(window.getSelection&&String(window.getSelection())) return; pvInqOpen({vendorId:vid}); };\n  (function(){ var st=document.createElement('style'); st.textContent='.pv-card:hover{background:#f4f8fe}'; document.head.appendChild(st); })();\n  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r258 2026-11-09 -->", "<!-- test build r259 2026-11-09 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue;
    if(o[0] instanceof RegExp){ var m=s.match(new RegExp(o[0].source,'g'))||[]; if(m.length!==o[2]) throw new Error('R259 FAIL '+o[3]+' count '+m.length); s=s.replace(o[0], o[1]); continue; }
    s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r259Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r259Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
