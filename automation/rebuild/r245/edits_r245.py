# -*- coding: utf-8 -*-
# r245 (사용자 요청 2026-10-20):
#  ① 메일 보내기에서 입력한 받는 사람 주소를 업체 상세(clientInfo)에 저장 → 다음부터 자동으로 채워진다.
#     (담당자 이름이 있으면 그 담당자 연락처의 메일로, 없으면 업체 대표 메일(email) 또는 이름 없는 연락처로)
#     + 받는 사람 자동 채움이 clientInfo 를 옛 키(업체명)로만 찾아 실제로는 거의 비어 있던 문제 → _clxInfoKey(업체명|지점) 로 조회.
#  ② 첨부에 '견적서 엑셀(일반 엑셀 양식)' 추가 — _qBuildQuoteSheetWb() 를 xlsx 바이트로 만들어 첨부. 기본 해제.
import io, sys, json

OPS = [
  ["    var ci=(typeof clientInfo==='object'&&clientInfo&&clientInfo[vname])||{}; var out=[];\n    var cs=Array.isArray(ci.contacts)?ci.contacts:[];",
   "    var ci=_mailClientInfo(vname); var out=[];   // r245: 업체명|지점 키로 조회\n    var cs=Array.isArray(ci.contacts)?ci.contacts:[];", 1, "CI_KEY"],
  ["  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238",
   "  function _mailClientInfo(vname){   // r245\n"
   "    if(typeof clientInfo!=='object'||!clientInfo) return {};\n"
   "    var k=null; try{ k=_clxInfoKey(vname); }catch(_e){}\n"
   "    return (k&&clientInfo[k])||clientInfo[vname]||{};\n"
   "  }\n"
   "  function _mailRemember(vname, mgr, toStr){   // r245: 보낸 주소를 업체 상세에 저장 → 다음부터 자동 채움\n"
   "    try{\n"
   "      if(!vname || typeof clientInfo!=='object' || !clientInfo) return 0;\n"
   "      if(typeof _isViewer==='function' && _isViewer()) return 0;\n"
   "      var addrs=String(toStr||'').split(/[,;\\s]+/).map(function(a){ return a.trim(); }).filter(function(a){ return /^[^\\s@<>]+@[^\\s@<>]+\\.[^\\s@<>]+$/.test(a); });\n"
   "      if(!addrs.length) return 0;\n"
   "      var known=_mailClientEmails(vname, mgr).map(function(e){ return String(e).toLowerCase(); });\n"
   "      var fresh=addrs.filter(function(a,i){ return known.indexOf(a.toLowerCase())<0 && addrs.findIndex(function(b){ return b.toLowerCase()===a.toLowerCase(); })===i; });\n"
   "      if(!fresh.length) return 0;\n"
   "      var key=_clxInfoKey(vname); var info=clientInfo[key]||clientInfo[vname]||{}; info.contacts=Array.isArray(info.contacts)?info.contacts:[];\n"
   "      var n=0, m=String(mgr||'').replace(/\\s+/g,'');\n"
   "      fresh.forEach(function(a){\n"
   "        if(m){ var c=info.contacts.find(function(x){ return x && String(x.name||'').replace(/\\s+/g,'')===m; });\n"
   "          if(c){ if(!c.email){ c.email=a; n++; return; } }\n"
   "          else { info.contacts.push({ dept:'', rank:'', name:mgr, phone:'', phone2:'', email:a }); n++; return; } }\n"
   "        if(!info.email){ info.email=a; n++; return; }\n"
   "        info.contacts.push({ dept:'', rank:'', name:'', phone:'', phone2:'', email:a }); n++;\n"
   "      });\n"
   "      if(!n) return 0;\n"
   "      clientInfo[key]=info;\n"
   "      try{ if(typeof _cliFind==='function' && typeof _cliMake==='function' && typeof clientList!=='undefined' && !_cliFind(vname)) clientList.push(_cliMake(vname,'')); }catch(_e){}\n"
   "      _clxPersist();\n"
   "      return n;\n"
   "    }catch(_e){ return 0; }\n"
   "  }\n"
   "  function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238", 1, "REMEMBER_FN"],
  ['<label style="display:flex;align-items:center;gap:5px;cursor:pointer"><input type="checkbox" id="mlAttHtml"> 견적서 HTML (카탈로그·도면 링크)</label>',
   '<label style="display:flex;align-items:center;gap:5px;cursor:pointer"><input type="checkbox" id="mlAttHtml"> 견적서 HTML (카탈로그·도면 링크)</label><label style="display:flex;align-items:center;gap:5px;cursor:pointer"><input type="checkbox" id="mlAttXlsx"> 견적서 엑셀</label>', 1, "XLSX_CHK"],
  ["    var wantPdf=document.getElementById('mlAttPdf').checked, wantHtml=document.getElementById('mlAttHtml').checked;",
   "    var wantPdf=document.getElementById('mlAttPdf').checked, wantHtml=document.getElementById('mlAttHtml').checked, wantXlsx=!!(document.getElementById('mlAttXlsx')&&document.getElementById('mlAttXlsx').checked);   // r245", 1, "WANT_XLSX"],
  ["      if(wantHtml){ st.textContent='HTML 만드는 중…'; var h=await _qBuildQuoteHtml(); atts.push({name:fn+'.html', type:'text/html', b64:await _blobToB64(new Blob([h],{type:'text/html;charset=utf-8'}))}); }",
   "      if(wantHtml){ st.textContent='HTML 만드는 중…'; var h=await _qBuildQuoteHtml(); atts.push({name:fn+'.html', type:'text/html', b64:await _blobToB64(new Blob([h],{type:'text/html;charset=utf-8'}))}); }\n"
   "      if(wantXlsx){ st.textContent='엑셀 만드는 중…'; await _ensureXlsxLib(); var xwb=_qBuildQuoteSheetWb(); var xarr=XLSX.write(xwb, {type:'array', bookType:'xlsx'}); atts.push({name:fn+'.xlsx', type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', b64:await _blobToB64(new Blob([xarr]))}); }   // r245", 1, "XLSX_ATT"],
  ["      _qMailLog(d.no, to, atts.map(function(a){return a.name;}));\n      document.getElementById('mailSendOverlay').style.display='none';",
   "      _qMailLog(d.no, to, atts.map(function(a){return a.name;}));\n      var _remembered=0; try{ _remembered=_mailRemember(d.vname, d.mgr, to); }catch(_e){}   // r245\n      document.getElementById('mailSendOverlay').style.display='none';", 1, "SEND_REMEMBER"],
  ["\\n\\n이 견적은 \"'+esc(d.no)+'\" 번호로 자동 저장되었고, 불러오기 목록에 ✉ 표시가 붙습니다.');",
   "\\n\\n이 견적은 \"'+esc(d.no)+'\" 번호로 자동 저장되었고, 불러오기 목록에 ✉ 표시가 붙습니다.'+(_remembered?('\\n받는 사람 주소 '+_remembered+'건을 업체 상세에 저장했습니다 — 다음부터 자동으로 채워집니다.'):''));", 1, "DONE_MSG"],
  ["<!-- test build r244 2026-10-20 -->", "<!-- test build r245 2026-10-20 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R245 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r245(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r245 브라우저 적용기 — edits_r245.py 의 OPS. r244 적용본 위에 적용.",
             "function r245Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R245 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r245Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r245(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r245 applied:', path)
