// r255 적용기 — 매입처 품번 문의 메일(브랜드 → 대리점 담당자 메일 연동) · 문의함 · 엑셀 업로드 합치기. r254 바탕 위에 적용.
var fs=require('fs'), path=require('path');
var MOD=fs.readFileSync(path.join(__dirname,'r255_module.js'),'utf8');
function r255Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R255 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS=[
    // 상태 키 sched_pv_inq
    ["  let clientPend = load('sched_client_pend') ?? [];", "  let clientPend = load('sched_client_pend') ?? [];\n  let pvInq = load('sched_pv_inq') ?? [];   // r255 매입처 문의함 [{id,no,at,by,brand,vendors,to,cc,replyTo,subject,body,items,status:wait|reply|done,memo}]", 1, "KEY_DECL"],
    ["    save('sched_client_pend', clientPend);   // r217", "    save('sched_client_pend', clientPend);   // r217\n    save('sched_pv_inq', pvInq);   // r255", 1, "KEY_SAVE"],
    ["sched_client_pend: clientPend,   // r217", "sched_client_pend: clientPend, sched_pv_inq: pvInq,   // r217 · r255", 2, "KEY_PAYLOAD"],
    ["    clientPend       = load('sched_client_pend') ?? [];   // r217", "    clientPend       = load('sched_client_pend') ?? [];   // r217\n    pvInq            = load('sched_pv_inq') ?? [];   // r255", 1, "KEY_RELOAD"],
    ["'sched_smc_queue','sched_client_pend',", "'sched_smc_queue','sched_client_pend','sched_pv_inq',", -1, "KEY_LISTS"],
    // 매입처 툴바: 문의함 버튼
    ["      <button class=\"qic\" id=\"purchaseAddBtn\" data-tip=\"매입처 추가\"", "      <button class=\"btn\" id=\"pvInqBoxBtn\" onclick=\"pvInqBox()\" title=\"보낸 품번 문의 · 회신 여부\" aria-label=\"문의함\" style=\"border-color:#b45309;color:#b45309;font-size:11.5px;padding:3px 10px;display:inline-flex;align-items:center;gap:4px;white-space:nowrap;height:28px;box-sizing:border-box\"><svg viewBox=\"0 0 24 24\" width=\"15\" height=\"15\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M4 6h16v12H4z\"/><path d=\"m4 7 8 6 8-6\"/></svg><span style=\"font-size:11.5px;font-weight:700\">문의함</span></button>\n      <span class=\"qic-div\" style=\"width:1px;align-self:stretch;background:#d3dae4;margin:2px 4px\"></span>\n      <button class=\"qic\" id=\"purchaseAddBtn\" data-tip=\"매입처 추가\"", 1, "TOOLBAR"],
    // 매입처 카드: ✉ 문의 버튼
    ["          <div style=\"position:absolute;top:8px;right:8px;display:flex;gap:4px\">\n            <button type=\"button\" onclick=\"openPurchaseModal('${v.id}')\"", "          <div style=\"position:absolute;top:8px;right:8px;display:flex;gap:4px\">\n            <button type=\"button\" class=\"pv-mail-btn\" onclick=\"pvInqOpen({vendorId:'${v.id}'})\" title=\"이 대리점 담당자에게 품번 문의 메일\" aria-label=\"문의 메일\"><svg viewBox=\"0 0 24 24\" width=\"15\" height=\"15\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M4 6h16v12H4z\"/><path d=\"m4 7 8 6 8-6\"/></svg></button>\n            <button type=\"button\" onclick=\"openPurchaseModal('${v.id}')\"", 1, "CARD_BTN"],
    ["    listEl.innerHTML = html;\n  }\n\n  function ensurePurchaseOverlay() {", "    listEl.innerHTML = html;\n    try{ _pvInqBadge(); }catch(_e){}   // r255\n  }\n\n  function ensurePurchaseOverlay() {", 1, "RENDER_BADGE"],
    // 견적 다운로드 메뉴: 매입처 문의
    [">메일 보내기 (PDF·HTML 첨부)</button>'\n          +'</div></div>'\n", ">메일 보내기 (PDF·HTML 첨부)</button>'\n          +'</div></div>'\n        +'<div><div style=\"font-size:12px;font-weight:700;color:#334155;margin-bottom:9px\">매입처 문의 <span style=\"font-weight:500;color:#9ca3af;font-size:11px\">· 목록의 품번을 브랜드 대리점 담당자에게 견적·납기 문의 · 회신은 내 메일로</span></div>'\n          +'<div style=\"display:flex;gap:8px\">'\n          +'<button onclick=\"document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; pvInqOpen({fromCart:true});\" style=\"'+_DLB+';border-color:#b45309;color:#b45309\" onmouseover=\"this.style.background=\\'#fff7ed\\'\" onmouseout=\"this.style.background=\\'#fff\\'\">매입처에 문의 메일</button>'\n          +'</div></div>'\n", 1, "DL_MENU"],
    // 엑셀 업로드: 담당자 줄의 이메일은 그 담당자 메일로, 같은 브랜드·대리점은 합치기
    ["          if (email) { curEmail = email; }", "          if (email && !person && !phoneRaw) { curEmail = email; }   // r255: 담당자 줄의 메일은 담당자 메일", 1, "XLS_EMAIL"],
    ["            ent.contacts.push({ role, name, phone });", "            ent.contacts.push({ role, name, phone, email });   // r255", 1, "XLS_CONTACT"],
    ["        showConfirmModal('매입처 추가', `엑셀에서 ${entries.length}개 매입처를 읽었습니다.\\n\\n기존 목록에 추가할까요?`, function(){\n          entries.forEach(e => purchaseVendors.push({\n            id: uid(),\n            brand: e.brand, distributor: e.distributor, email: e.email,\n            contacts: e.contacts, memo: '', createdAt: Date.now()\n          }));\n          saveAll();\n          renderPurchasePage();\n          showInfoModal('알림', `${entries.length}개 매입처 추가됨`);\n        }, '추가', '#1B3A6B');",
     "        showConfirmModal('매입처 추가', `엑셀에서 ${entries.length}개 매입처를 읽었습니다.\\n\\n같은 브랜드·대리점이 이미 있으면 담당자만 합치고, 없으면 새로 추가합니다. 진행할까요?`, function(){\n          var _r = _pvMergeEntries(entries);   // r255\n          saveAll();\n          renderPurchasePage();\n          showInfoModal('알림', `매입처 ${_r.added}개 추가 · ${_r.merged}개 합침 · 담당자 ${_r.contacts}명 등록`);\n        }, '추가', '#1B3A6B');", 1, "XLS_MERGE"],
    ["<td style=\"padding:8px 10px;font-weight:700\">이메일</td><td style=\"padding:8px 10px\">대표 이메일</td>", "<td style=\"padding:8px 10px;font-weight:700\">이메일</td><td style=\"padding:8px 10px\">담당자가 같은 줄에 있으면 그 담당자 메일, 없으면 대표 메일</td>", 1, "XLS_GUIDE"],
    // JS 모듈
    ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", MOD+"  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "JS"],
    ["<!-- test build r254 2026-11-03 -->", "<!-- test build r255 2026-11-06 -->", 1, "MARKER"]
  ];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(o[3]==='MARKER'&&!isTest) continue; var exp=o[2]; if(o[3]==='KEY_LISTS') exp=isTest?3:2; s=rep(s, o[0], o[1], exp, o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports=r255Apply;
if(require.main===module){
  var src=process.argv[2], out=process.argv[3], isTest=process.argv[4]==='test';
  fs.writeFileSync(out, r255Apply(fs.readFileSync(src,'utf8'), isTest)); console.log('ok →', out);
}
