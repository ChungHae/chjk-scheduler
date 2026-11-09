// r258 적용기 — 매입처 품번 문의를 견적(매출) 다운로드 메뉴에서 빼고 매입처 페이지 툴바로 옮김. r257 바탕.
var fs=require('fs');
function r258Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R258 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    // 견적 다운로드 메뉴의 '매입처 문의' 구역 제거 (r255 DL_MENU 되돌림)
    ["        +'<div><div style=\"font-size:12px;font-weight:700;color:#334155;margin-bottom:9px\">매입처 문의 <span style=\"font-weight:500;color:#9ca3af;font-size:11px\">· 목록의 품번을 브랜드 대리점 담당자에게 견적·납기 문의 · 회신은 내 메일로</span></div>'\n          +'<div style=\"display:flex;gap:8px\">'\n          +'<button onclick=\"document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; pvInqOpen({fromCart:true});\" style=\"'+_DLB+';border-color:#b45309;color:#b45309\" onmouseover=\"this.style.background=\\'#fff7ed\\'\" onmouseout=\"this.style.background=\\'#fff\\'\">매입처에 문의 메일</button>'\n          +'</div></div>'\n", "", 1, "DL_MENU_REMOVE"],
    // 매입처 툴바: [품번 문의] 버튼 (문의함 왼쪽)
    ["      <button class=\"btn\" id=\"pvInqBoxBtn\" onclick=\"pvInqBox()\"", "      <button class=\"btn\" id=\"pvInqNewBtn\" onclick=\"pvInqOpen({})\" title=\"브랜드 대리점 담당자에게 품번 견적·납기 문의 메일\" style=\"border-color:#1B3A6B;color:#1B3A6B;font-size:11.5px;padding:3px 10px;display:inline-flex;align-items:center;gap:4px;white-space:nowrap;height:28px;box-sizing:border-box\"><svg viewBox=\"0 0 24 24\" width=\"15\" height=\"15\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M4 6h16v12H4z\"/><path d=\"m4 7 8 6 8-6\"/><path d=\"M12 2v3\"/></svg><span style=\"font-size:11.5px;font-weight:700\">품번 문의</span></button>\n      <button class=\"btn\" id=\"pvInqBoxBtn\" onclick=\"pvInqBox()\"", 1, "PV_TOOLBAR"],
    // 문의함 빈 안내 문구
    ["견적 다운로드 > [매입처에 문의 메일] 또는 매입처 카드의 ✉ 에서 보냅니다.", "매입처 툴바의 [품번 문의] 또는 매입처 카드의 ✉ 에서 보냅니다.", 1, "BOX_HINT"],
    ["<!-- test build r257 2026-11-09 -->", "<!-- test build r258 2026-11-09 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; s=rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r258Apply;
if(require.main===module){ var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test'; fs.writeFileSync(out, r258Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out); }
