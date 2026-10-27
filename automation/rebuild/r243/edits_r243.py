# -*- coding: utf-8 -*-
# r243 (사용자 요청 2026-10-20): 영업 자료(제안서 PDF) — 일정에서 각 영업 담당자 이름·직급·전화로 바꿔 내려받기
#  - 자료실 분류에 '영업자료(제안서)' 추가. 이 분류의 PDF 는 다운로드할 때 담당자 칸을 치환해 준다(pdf-lib + fontkit, CDN 지연 로드).
#  - 일정(메모장) 툴바 [영업 자료] 버튼 → 목록 창: 직원 선택(기본 = 나) + 자료마다 [PDF 받기]. 관리자는 [원본]·[치환 위치] 도.
#  - 치환 위치는 자료마다 `pcfg`(slots: 바탕 사각형 + 오른쪽 정렬 글자)로 저장, 없으면 기본값(충해 제안서 양식: 머리글 '담당 …', 꼬리글 '상담 · 견적 문의 …', 큰 전화번호).
#  - 글꼴: Pretendard Bold 부분집합(직원 이름·직급·숫자, 24KB) 을 내장. 없는 글자가 있으면 전체 글꼴(jsdelivr) 을 받아 쓴다.
import io, sys, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_B64 = io.open(os.path.join(HERE, 'r243_font.b64'), encoding='utf-8').read().strip()

JS = r"""
  // ─── r243 영업 자료(제안서) 담당자 치환 ─────────────────────────────
  var _SD_CAT='영업자료(제안서)';
  var _SD_FONT_B64='%%FONT%%';
  var _SD_FONT_FULL='https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/public/static/alternative/Pretendard-Bold.ttf';
  var _SD_CFG_DEFAULT={ slots:[
    { template:'담당 {name} {position} {phone}', top:33, h:16, rightMargin:33.66, baseline:44.6, size:11, color:[13,42,85], bg:[255,255,255] },
    { template:'상담 · 견적 문의 {name} {position}', top:779, h:16, rightMargin:33.66, baseline:791.7, size:11, color:[255,255,255], bg:[13,41,84] },
    { template:'{phone}', top:795, h:27, rightMargin:34.5, baseline:816.3, size:22, color:[255,210,63], bg:[13,41,84] }
  ] };
  var _sdLibP=null;
  function _sdScript(src){ return new Promise(function(res,rej){ var s=document.createElement('script'); s.src=src; s.onload=res; s.onerror=function(){ rej(new Error('라이브러리 로드 실패: '+src)); }; document.head.appendChild(s); }); }
  function _sdLibs(){
    if(window.PDFLib && window.fontkit) return Promise.resolve();
    if(_sdLibP) return _sdLibP;
    _sdLibP=(async function(){
      if(!window.PDFLib) await _sdScript('https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js');
      if(!window.fontkit) await _sdScript('https://cdn.jsdelivr.net/npm/@pdf-lib/fontkit@1.1.1/dist/fontkit.umd.min.js');
    })();
    _sdLibP.catch(function(){ _sdLibP=null; });
    return _sdLibP;
  }
  function _sdB64Bytes(b64){ var bin=atob(b64), u=new Uint8Array(bin.length); for(var i=0;i<bin.length;i++) u[i]=bin.charCodeAt(i); return u; }
  var _sdFullFont=null;
  async function _sdFontFor(text){
    var sub=_sdB64Bytes(_SD_FONT_B64);
    try{
      var fk=window.fontkit.create(sub), okAll=true;
      for(var i=0;i<text.length;i++){ var cp=text.codePointAt(i); if(cp>0xffff) i++; if(cp===32) continue; if(!fk.hasGlyphForCodePoint(cp)){ okAll=false; break; } }
      if(okAll) return sub;
    }catch(_e){}
    if(!_sdFullFont){ var r=await fetch(_SD_FONT_FULL,{mode:'cors'}); if(!r.ok) throw new Error('글꼴 다운로드 실패 ('+r.status+')'); _sdFullFont=new Uint8Array(await r.arrayBuffer()); }
    return _sdFullFont;
  }
  function _sdFill(t, who){ return String(t||'').replace(/\{name\}/g, who.name||'').replace(/\{position\}/g, who.position||'').replace(/\{phone\}/g, who.phone||'').replace(/\s+/g,' ').trim(); }
  async function _sdPersonalize(pdfBytes, cfg, who){
    await _sdLibs();
    var PL=window.PDFLib, slots=(cfg&&cfg.slots)||_SD_CFG_DEFAULT.slots;
    var allText=slots.map(function(s){ return _sdFill(s.template, who); }).join('');
    var fontBytes=await _sdFontFor(allText);
    var doc=await PL.PDFDocument.load(pdfBytes, { ignoreEncryption:true });
    doc.registerFontkit(window.fontkit);
    var font=await doc.embedFont(fontBytes, { subset:false, features:{ kern:false, liga:false, calt:false, clig:false, rlig:false, ccmp:false, locl:false, mark:false, mkmk:false } });
    var pages=doc.getPages();
    slots.forEach(function(s){
      var text=_sdFill(s.template, who); if(!text) return;
      var size=s.size||11, tw=font.widthOfTextAtSize(text, size);
      pages.forEach(function(pg, i){
        if(s.pages && s.pages.indexOf(i)<0) return;
        var H=pg.getHeight(), W=pg.getWidth();
        var right=W-(s.rightMargin!=null?s.rightMargin:33.66);
        var bw=Math.max(s.w||0, tw+8);
        if(s.bg) pg.drawRectangle({ x:right-bw, y:H-s.top-s.h, width:bw+2, height:s.h, color:PL.rgb(s.bg[0]/255, s.bg[1]/255, s.bg[2]/255) });
        pg.drawText(text, { x:right-tw, y:H-s.baseline, size:size, font:font, color:PL.rgb((s.color||[0,0,0])[0]/255, (s.color||[0,0,0])[1]/255, (s.color||[0,0,0])[2]/255) });
      });
    });
    return await doc.save();
  }
  function _sdWho(name){
    var nm=String(name||'').trim();
    var m=(members||[]).find(function(x){ return String(x.name||'').trim()===nm; })||{};
    return { name:nm, position:m.position||'', phone:m.phone||'' };
  }
  function _sdIsDoc(f){ return !!f && f.category===_SD_CAT && /\.pdf$/i.test(String(f.name||'')); }
  function _sdDocs(){ return (filesList||[]).filter(_sdIsDoc).sort(function(a,b){ return (b.ts||0)-(a.ts||0); }); }
  function _sdPeople(){ return (members||[]).filter(function(m){ return m && m.name; }).map(function(m){ return m.name; }); }
  var _sdPick='';
  window.sdPickSet=function(v){ _sdPick=String(v||''); };
  window.sdOpenList = function(){
    var me=(_authUser&&_authUser.name)||'';
    if(!_sdPick || _sdPeople().indexOf(_sdPick)<0) _sdPick=me;
    var ov=_coOverlay('sdOverlay', 640);
    var docs=_sdDocs(), adm=_isAdmin();
    var opts=_sdPeople().map(function(n){ var w=_sdWho(n); return '<option value="'+esc(n)+'"'+(n===_sdPick?' selected':'')+'>'+esc(n+(w.position?' '+w.position:'')+(w.phone?' · '+w.phone:''))+'</option>'; }).join('');
    var rows=docs.length?docs.map(function(f){
      return '<div class="sd-row"><span class="sd-nm" title="'+esc(f.name)+'">'+esc(f.name)+'</span><span class="sd-meta">'+_fmtSize(f.size||0)+(f.byName?' · '+esc(f.byName):'')+'</span>'
        +'<button type="button" class="btn sd-get" onclick="sdDownload(\''+f.id+'\')">PDF 받기</button>'
        +(adm?'<button type="button" class="btn" onclick="downloadFile(\''+f.id+'\', true)" title="치환 없이 원본 그대로">원본</button><button type="button" class="btn" onclick="sdCfgEdit(\''+f.id+'\')" title="담당자 칸 위치·글자 설정">치환 위치</button>':'')
        +'</div>';
    }).join(''):'<div style="padding:26px;text-align:center;color:#9ca3af;font-size:12.5px">등록된 영업 자료가 없습니다.'+(adm?'<br>자료실 › 충해전기 › 분류 <b>'+esc(_SD_CAT)+'</b> 로 PDF 를 올리면 여기에 보입니다.':'')+'</div>';
    ov.innerHTML='<div class="co-ovbox"><div class="co-ovhd"><span>영업 자료 (제안서)</span><span style="flex:1"></span><button class="btn" onclick="document.getElementById(\'sdOverlay\').style.display=\'none\'" style="padding:3px 10px">닫기</button></div>'
      +'<div class="co-ovbd" style="padding:10px 14px 14px">'
      +'<div style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:#334155;margin-bottom:10px"><span style="white-space:nowrap;font-weight:600">담당자</span><select id="sdWho" onchange="sdPickSet(this.value)" style="padding:5px 8px;border:1px solid #c8d2de;font-size:12.5px;font-family:inherit;min-width:220px">'+opts+'</select><span style="color:#64748b;font-size:11.5px">— 선택한 직원의 이름·직급·전화로 바뀐 PDF 를 내려받습니다 (직원 정보의 직급·전화 사용)</span></div>'
      +'<div id="sdRows">'+rows+'</div>'
      +(adm?'<div style="margin-top:10px;font-size:11.5px;color:#64748b">자료 추가: 자료실 › 충해전기 › 업로드 › 분류 <b>'+esc(_SD_CAT)+'</b>. 담당자 칸이 비어 있는(또는 기준 담당자가 적힌) 원본 PDF 를 올리면 됩니다.</div>':'')
      +'</div></div>';
    ov.style.display='flex';
  };
  window.sdDownload = async function(id){
    var meta=(filesList||[]).find(function(f){ return f.id===id; }); if(!meta) return;
    var who=_sdWho(_sdPick||(_authUser&&_authUser.name)||'');
    if(!who.name){ showInfoModal('영업 자료','담당자를 선택하세요.'); return; }
    var btns=document.querySelectorAll('#sdOverlay .sd-get'); btns.forEach(function(b){ b.disabled=true; });
    try{
      var dataUrl=await _fbFileGet(id); if(!dataUrl) throw new Error('파일 데이터를 찾을 수 없습니다.');
      var src=new Uint8Array(await (await fetch(dataUrl)).arrayBuffer());
      var out=await _sdPersonalize(src, meta.pcfg||_SD_CFG_DEFAULT, who);
      var base=_splitExt(meta.name||'제안서').base;
      var blob=new Blob([out],{type:'application/pdf'}); var url=URL.createObjectURL(blob);
      var a=document.createElement('a'); a.href=url; a.download=base+' ('+who.name+').pdf'; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function(){ URL.revokeObjectURL(url); }, 30000);
      window._sdLastOut=out;
    }catch(e){ showInfoModal('영업 자료', '만들지 못했습니다: '+((e&&e.message)||e)); }
    finally{ btns.forEach(function(b){ b.disabled=false; }); }
  };
  window.sdCfgEdit = function(id){
    if(!_isAdmin()) return;
    var meta=(filesList||[]).find(function(f){ return f.id===id; }); if(!meta) return;
    var ov=_coOverlay('sdCfgOverlay', 560);
    ov.innerHTML='<div class="co-ovbox"><div class="co-ovhd"><span>치환 위치 · '+esc(meta.name)+'</span><span style="flex:1"></span><button class="btn" onclick="document.getElementById(\'sdCfgOverlay\').style.display=\'none\'" style="padding:3px 10px">닫기</button></div>'
      +'<div class="co-ovbd" style="padding:12px 14px">'
      +'<div style="font-size:11.5px;color:#64748b;line-height:1.5;margin-bottom:8px">slots 마다 바탕 사각형(bg, 위 top·높이 h, 오른쪽 여백 rightMargin) 위에 오른쪽 정렬 글자(template, baseline, size, color) 를 그립니다. 단위 pt, 위에서부터. {name} {position} {phone} 치환. 비우면 기본값.</div>'
      +'<textarea id="sdCfgTa" style="width:100%;box-sizing:border-box;height:220px;font-family:ui-monospace,monospace;font-size:11.5px;padding:8px;border:1px solid #c8d2de">'+esc(JSON.stringify(meta.pcfg||_SD_CFG_DEFAULT, null, 1))+'</textarea>'
      +'<div style="display:flex;gap:8px;margin-top:8px;justify-content:flex-end"><button class="btn" onclick="document.getElementById(\'sdCfgTa\').value=JSON.stringify(_SD_CFG_DEFAULT,null,1)">기본값</button><button class="btn btn-primary" onclick="sdCfgSave(\''+id+'\')">저장</button></div>'
      +'</div></div>';
    ov.style.display='flex';
  };
  window.sdCfgSave = function(id){
    if(!_isAdmin()) return;
    var meta=(filesList||[]).find(function(f){ return f.id===id; }); if(!meta) return;
    var ta=document.getElementById('sdCfgTa'); var txt=(ta&&ta.value||'').trim();
    try{
      if(!txt){ delete meta.pcfg; }
      else { var o=JSON.parse(txt); if(!o||!Array.isArray(o.slots)) throw new Error('slots 배열이 필요합니다.'); meta.pcfg=o; }
      saveAll(); document.getElementById('sdCfgOverlay').style.display='none'; showInfoModal('영업 자료','치환 위치를 저장했습니다.');
    }catch(e){ showInfoModal('영업 자료','JSON 오류: '+e.message); }
  };
  (function(){ var st=document.createElement('style'); st.textContent='#sdOverlay .sd-row{display:flex;align-items:center;gap:8px;padding:8px 6px;border-bottom:1px solid #eef0f3;font-size:12.5px} #sdOverlay .sd-nm{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600;color:#1a1a1a} #sdOverlay .sd-meta{color:#9ca3af;font-size:11px;white-space:nowrap} #sdOverlay .btn{padding:3px 9px;font-size:12px} #sdOverlay .sd-get{background:#1B3A6B;color:#fff;border:none}'; document.head.appendChild(st); })();
"""

OPS = [
  ["  const FILE_CATS = ['사업자등록증','통장사본','법인인감증명서','법인등기부등본','기타'];",
   "  const FILE_CATS = ['사업자등록증','통장사본','법인인감증명서','법인등기부등본','영업자료(제안서)','기타'];   // r243", 1, "CATS"],
  ["  window.deleteFile = function(id){",
   JS.replace('%%FONT%%', FONT_B64) + "  window.deleteFile = function(id){", 1, "SD_JS"],
  ["  window.downloadFile = async function(id){\n    const meta = filesList.find(f=>f.id===id);\n    if(!meta) return;\n    try{",
   "  window.downloadFile = async function(id, raw){\n    const meta = filesList.find(f=>f.id===id);\n    if(!meta) return;\n    if(!raw && _sdIsDoc(meta)){ _sdPick=(_authUser&&_authUser.name)||''; return sdDownload(id); }   // r243: 영업 자료는 내 이름으로 치환해서\n    try{", 1, "DL_HOOK"],
  ['<button class="qic" onclick="coOpenMine()"',
   '<button class="qic" onclick="sdOpenList()" data-tip="영업 자료 (제안서)" aria-label="영업 자료" style="border-color:#7c3aed;color:#7c3aed"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="M8 13h8M8 17h5"/></svg></button><!-- r243 --><button class="qic" onclick="coOpenMine()"', 1, "MEMO_BTN"],
  ["<!-- test build r242 2026-10-20 -->", "<!-- test build r243 2026-10-20 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R243 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r243(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r243 브라우저 적용기 — edits_r243.py 의 OPS. r242 적용본 위에 적용.",
             "function r243Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R243 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r243Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r243(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r243 applied:', path)
