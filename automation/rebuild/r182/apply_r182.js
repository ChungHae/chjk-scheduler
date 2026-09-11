// r182 브라우저 적용기 — edits_r182.py 의 ops_r182 에서 생성. r181(live d7e81e80 / test 65b6c0c9) 에 적용.
function r182Apply(s, isTest){
  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R182 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }
  var OPS = [["      +'<a href=\"https://www.smckorea.co.kr/\" target=\"_blank\" rel=\"noopener\" class=\"smc-f\">SMC 사이트 열기</a>'", "      +'<a href=\"http://www.smckorea.net/main/main.jsp\" target=\"_blank\" rel=\"noopener\" class=\"smc-f\">SMC 사이트 열기</a>'   // r182", 1, "LINK"], ["매주 금요일 17시 이후 SMC 사이트에서 가격을 확인하고 맞으면 [등록]')+'</span>'", "매주 금요일 17시 이후 SMC 사이트에서 E가를 확인하고 맞으면 [등록] · 확판가·소물가도 확인되면 같이 등록')+'</span>'", 1, "NOTE"], ["            +'<td><input class=\"smc-in\" data-f=\"hp\" value=\"'+(q.buy!=null?q.buy:'')+'\" title=\"견적에 넣은 구매가가 미리 들어 있습니다. 확판가가 아니면 지우세요\"></td>'\n            +'<td><input class=\"smc-in\" data-f=\"sm\" value=\"\"></td>';", "            +'<td><input class=\"smc-in\" data-f=\"hp\" value=\"\" placeholder=\"'+(q.buy!=null?('견적 '+_qFmt(q.buy)):'')+'\" title=\"SMC 사이트에서 확인한 확판가 (회색 값은 견적에 넣었던 구매가 — 참고용)\"></td>'   // r182\n            +'<td><input class=\"smc-in\" data-f=\"sm\" value=\"\" title=\"SMC 사이트에서 확인한 소물가\"></td>';", 1, "HP"], ["<!-- test build r181 2026-09-11 -->", "<!-- test build r182 2026-09-11 -->", 1, "MARKER"]];
  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }
  return s;
}
if(typeof module!=='undefined') module.exports = r182Apply;
