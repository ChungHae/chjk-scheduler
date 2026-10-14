# -*- coding: utf-8 -*-
# r235 (사용자 요청 2026-10-14): 견적서를 사내전산에서 바로 메일로 발송 (chjk@chjk.co.kr, 네이버 웍스 SMTP).
#   사내전산은 서버가 없으므로 발송은 Cloudflare Worker(mail/worker.js) 가 맡는다:
#     사내전산 [메일 보내기] → POST {worker}/send (헤더 X-Mail-Key) → Worker 가 SMTP 로 발송.
#   Worker 주소·열쇠는 Firebase `sched_mail_cfg` {url,key,cc,sign} 에 저장(관리자가 메일 설정 창에서 입력, 로그인해야 읽힘).
#   견적 다운로드 창 네 번째 묶음 [메일 보내기]: 받는 사람(업체 담당자 메일 자동) · 참조 · 제목 · 본문(기본 문안) · 첨부(PDF ✓ · HTML ✓)
#   → 견적 자동 저장 → PDF(pdfmake blob)·HTML(r233) 만들어 base64 로 첨부 → 발송 → 저장 견적에 mail 기록(불러오기 목록 ✉ N회).
#   받은 메일 열람은 다음(사용자 10-14 "견적서 발송을 중점으로").
import io, sys, json

MENU_OLD = """          +'<button onclick="document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; qExportHtml();" style="\'+_DLB+\'" onmouseover="this.style.background=\\'#f6f8fa\\'" onmouseout="this.style.background=\\'#fff\\'">HTML 견적서</button>'
          +'</div></div>'
      +'</div></div>';"""
MENU_NEW = """          +'<button onclick="document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; qExportHtml();" style="\'+_DLB+\'" onmouseover="this.style.background=\\'#f6f8fa\\'" onmouseout="this.style.background=\\'#fff\\'">HTML 견적서</button>'
          +'</div></div>'
        +'<div><div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:9px">메일 발송 <span style="font-weight:500;color:#9ca3af;font-size:11px">· chjk@chjk.co.kr 에서 고객에게 바로</span>'+(_isAdmin()?'<a onclick="document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; mailOpenCfg();" style="float:right;font-weight:500;color:#1B3A6B;text-decoration:underline;cursor:pointer;font-size:11px">메일 설정</a>':'')+'</div>'
          +'<div style="display:flex;gap:8px">'
          +'<button onclick="document.getElementById(\\'qDlMenuOverlay\\').style.display=\\'none\\'; qOpenMailSend();" style="\'+_DLB+\';background:#1B3A6B;color:#fff;border-color:#1B3A6B" onmouseover="this.style.background=\\'#14305c\\'" onmouseout="this.style.background=\\'#1B3A6B\\'">메일 보내기 (PDF·HTML 첨부)</button>'
          +'</div></div>'
      +'</div></div>';"""

LIST_OLD = "+esc(qq.savedBy||'')+(ds?(' · '+ds):'')+'</div></div>'"
LIST_NEW = "+esc(qq.savedBy||'')+(ds?(' · '+ds):'')+((qq.mail&&qq.mail.length)?' · <span style=\"color:#1B3A6B;font-weight:700\" title=\"'+esc(qq.mail.map(function(m){ return (m.at?new Date(m.at).toLocaleDateString():'')+' → '+(m.to||''); }).join('\\n'))+'\">✉ '+qq.mail.length+'회</span>':'')+'</div></div>'"

JS = r"""  // ─── r235: 견적서 메일 보내기 (Cloudflare Worker → 네이버 웍스 SMTP) ───
  var _mailCfg=null;
  async function _mailLoadCfg(force){
    if(_mailCfg && !force) return _mailCfg;
    try{ var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_mail_cfg.json'); _mailCfg=(r&&r.ok?(await r.json()):null)||{}; }catch(_e){ _mailCfg={}; }
    return _mailCfg;
  }
  async function _mailSaveCfg(obj){
    var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_mail_cfg.json', {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(obj)});
    if(!r||!r.ok) throw new Error('저장 실패 (HTTP '+(r?r.status:'네트워크')+')');
    _mailCfg=Object.assign(_mailCfg||{}, obj);
  }
  function _mailUrl(cfg, path){ return String(cfg.url||'').replace(/\/+$/,'')+path; }
  function _mailOverlay(id, html, maxW){
    var ov=document.getElementById(id);
    if(!ov){ ov=document.createElement('div'); ov.id=id; ov.style.cssText='position:fixed;inset:0;z-index:100060;background:rgba(15,23,42,.45);display:none;align-items:center;justify-content:center;padding:16px'; document.body.appendChild(ov); }
    ov.innerHTML='<div style="width:100%;max-width:'+(maxW||640)+'px;max-height:92vh;overflow:auto;background:#fff;border-radius:14px;box-shadow:0 14px 44px rgba(27,58,107,.22)">'+html+'</div>';
    ov.style.display='flex'; return ov;
  }
  var _MLI='width:100%;box-sizing:border-box;padding:8px 10px;border:1.5px solid #d6e0ec;border-radius:8px;font-size:13px;font-family:inherit';
  var _MLL='font-size:12px;font-weight:700;color:#14305c;margin:0 0 4px';
  window.mailOpenCfg=async function(){
    if(!_isAdmin()){ showInfoModal('권한','메일 설정은 관리자만 할 수 있습니다.'); return; }
    var cfg=await _mailLoadCfg(true);
    _mailOverlay('mailCfgOverlay',
      '<div style="padding:16px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">메일 설정</span><button class="btn" onclick="document.getElementById(\'mailCfgOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:18px 20px;display:flex;flex-direction:column;gap:12px">'
      +'<div style="background:#f4f8fe;border:1px solid #d6e4f5;border-radius:9px;padding:10px 13px;font-size:11.5px;color:#374151;line-height:1.8">발송은 <b>Cloudflare Worker</b>(mail/worker.js) 가 chjk@chjk.co.kr 로 보냅니다. Worker 에 넣은 <b>MAIL_KEY</b> 와 같은 값을 아래 열쇠에 넣으세요. 이 값은 로그인한 직원만 읽을 수 있는 자리에 저장됩니다(비밀번호는 Worker 에만 있음).</div>'
      +'<div><div style="'+_MLL+'">Worker 주소</div><input id="mlCfgUrl" placeholder="https://chjk-mail.xxxx.workers.dev" value="'+esc(cfg.url||'')+'" style="'+_MLI+'"></div>'
      +'<div><div style="'+_MLL+'">열쇠 (MAIL_KEY)</div><input id="mlCfgKey" type="password" placeholder="Worker 의 MAIL_KEY 와 동일" value="'+esc(cfg.key||'')+'" style="'+_MLI+'"></div>'
      +'<div><div style="'+_MLL+'">기본 참조(CC) <span style="font-weight:400;color:#9ca3af">— 보낸 견적을 같이 받아 둘 사내 주소, 쉼표 구분 (선택)</span></div><input id="mlCfgCc" placeholder="chjk@chjk.co.kr" value="'+esc(cfg.cc||'')+'" style="'+_MLI+'"></div>'
      +'<div id="mlCfgMsg" style="font-size:12px;color:#6b7280;min-height:18px"></div>'
      +'<div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn" onclick="mailCfgPing()">연결 확인</button><button class="btn btn-primary" onclick="mailCfgSave()">저장</button></div>'
      +'</div>');
  };
  window.mailCfgPing=async function(){
    var m=document.getElementById('mlCfgMsg'); var url=(document.getElementById('mlCfgUrl').value||'').trim();
    if(!url){ m.textContent='Worker 주소를 입력하세요.'; return; }
    m.textContent='확인 중…';
    try{ var r=await fetch(_mailUrl({url:url},'/ping')); var j=await r.json(); m.innerHTML=j.ok?('<span style="color:#15803d">연결됨 · 발신 계정 '+esc(j.user||'(미설정)')+'</span>'):('<span style="color:#dc2626">응답 이상: '+esc(JSON.stringify(j))+'</span>'); }
    catch(e){ m.innerHTML='<span style="color:#dc2626">연결 실패: '+esc(e.message||String(e))+'</span>'; }
  };
  window.mailCfgSave=async function(){
    var m=document.getElementById('mlCfgMsg');
    var obj={ url:(document.getElementById('mlCfgUrl').value||'').trim(), key:(document.getElementById('mlCfgKey').value||'').trim(), cc:(document.getElementById('mlCfgCc').value||'').trim() };
    if(!/^https:\/\//.test(obj.url)){ m.textContent='Worker 주소는 https:// 로 시작해야 합니다.'; return; }
    try{ await _mailSaveCfg(obj); m.innerHTML='<span style="color:#15803d">저장했습니다.</span>'; }catch(e){ m.innerHTML='<span style="color:#dc2626">'+esc(e.message||String(e))+'</span>'; }
  };
  function _blobToB64(blob){ return new Promise(function(res,rej){ var fr=new FileReader(); fr.onload=function(){ res(String(fr.result).replace(/^data:[^,]*,/,'')); }; fr.onerror=function(){ rej(new Error('파일 변환 실패')); }; fr.readAsDataURL(blob); }); }
  async function _qMakePdfBlob(){
    var pm=await _ensurePdfMake(); var FONT=await _qPdfFontLoad(pm);
    var dd=_qBuildPdfDoc({ orient:(window._qPdfOrient==='l')?'l':'p', font:FONT });
    return new Promise(function(res){ pm.createPdf(dd).getBlob(res); });
  }
  function _mailClientEmails(vname, mgr){
    var ci=(typeof clientInfo==='object'&&clientInfo&&clientInfo[vname])||{}; var out=[];
    var cs=Array.isArray(ci.contacts)?ci.contacts:[];
    var hit=mgr?cs.find(function(c){ return c&&c.email&&String(c.name||'').replace(/\s+/g,'')===String(mgr).replace(/\s+/g,''); }):null;
    if(hit) out.push(hit.email);
    cs.forEach(function(c){ if(c&&c.email&&out.indexOf(c.email)<0) out.push(c.email); });
    if(ci.email&&out.indexOf(ci.email)<0) out.push(ci.email);
    if(ci.taxEmail&&out.indexOf(ci.taxEmail)<0) out.push(ci.taxEmail);
    return out;
  }
  function _mailQuoteDraft(){
    var vname=_qCart[0].vname||''; var no=_qQuoteNo||'';
    var _mgEl=document.getElementById('qManager'); var mgr=(_mgEl&&!_mgEl.disabled&&_mgEl.value)?String(_mgEl.value).trim():'';
    var staff=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)?_authUser.name:'';
    var _me=(typeof members!=='undefined'&&members)?members.find(function(x){return (x.name||'').trim()===staff;}):null;
    var branch=(_me&&_me.group)?_me.group:'서울'; var SUP=_qSupplierInfo(branch);
    var phone=(_me&&_me.phone)?_me.phone:'';
    var supply=0; _qCart.forEach(function(c){ var q=Number(c.qty)||1; if(c.sell!=null&&c.sell!=='') supply+=Number(c.sell)*q; }); supply-=((typeof _qNego!=='undefined'&&_qNego)?Number(_qNego):0);
    var body=vname+' '+(mgr?mgr+' 님':'담당자님')+', 안녕하세요.\n'+SUP.corp+' '+staff+'입니다.\n\n'
      +'요청하신 견적서를 보내드립니다. (견적번호 '+no+')\n'
      +'· 품목 '+_qCart.length+'건 · 공급가액 '+Math.round(supply).toLocaleString()+'원 (부가세 별도)\n'
      +'· 첨부: 견적서 PDF, 견적서 HTML(품목별 카탈로그·도면 링크 포함 — 클릭해서 열어 보세요)\n\n'
      +'검토 후 궁금한 점이 있으시면 언제든 연락 주십시오.\n감사합니다.\n\n'
      +'─────────────────\n'+staff+(phone?' · '+phone:'')+' · '+SUP.mail+'\n'+SUP.corp+' · TEL '+SUP.tel+' · FAX '+SUP.fax+'\n'+SUP.addr.replace(/\n/g,' ')+'\n온라인몰 airmall24.co.kr';
    return { vname:vname, no:no, mgr:mgr, staff:staff, to:_mailClientEmails(vname, mgr), subject:'[충해전기] 견적서 '+no+' — '+vname, body:body, fromName:SUP.corp+' '+staff };
  }
  window.qOpenMailSend=async function(){
    if(!_qCart.length || !_qCartHasContent()){ showInfoModal('견적 목록','견적 목록이 비어 있습니다.'); return; }
    var cfg=await _mailLoadCfg();
    if(!cfg.url||!cfg.key){ if(_isAdmin()){ showInfoModal('메일 설정 필요','아직 발송 서버(Worker) 주소와 열쇠가 등록되지 않았습니다.\n\n견적 다운로드 창의 [메일 설정] 에서 입력해 주세요.'); } else { showInfoModal('메일 설정 필요','관리자가 메일 발송 설정을 아직 하지 않았습니다.'); } return; }
    _qEnsureQuoteNo();
    var d=_mailQuoteDraft();
    _mailOverlay('mailSendOverlay',
      '<div style="padding:16px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">견적서 메일 보내기 <span style="font-size:12px;font-weight:500;color:#6b7280;margin-left:6px">'+esc(d.no)+' · '+esc(d.vname)+'</span></span><button class="btn" onclick="document.getElementById(\'mailSendOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:16px 20px;display:flex;flex-direction:column;gap:11px">'
      +'<div><div style="'+_MLL+'">받는 사람 <span style="font-weight:400;color:#9ca3af">— 여러 명은 쉼표</span></div><input id="mlTo" value="'+esc(d.to.join(', '))+'" placeholder="고객 메일 주소" style="'+_MLI+'">'+(d.to.length?'':'<div style="font-size:11px;color:#b45309;margin-top:3px">업체 상세에 담당자 메일이 없어 비워 두었습니다. 직접 입력해 주세요 (업체 관리에 등록해 두면 다음부터 자동).</div>')+'</div>'
      +'<div><div style="'+_MLL+'">참조(CC)</div><input id="mlCc" value="'+esc(cfg.cc||'')+'" style="'+_MLI+'"></div>'
      +'<div><div style="'+_MLL+'">제목</div><input id="mlSubj" value="'+esc(d.subject)+'" style="'+_MLI+'"></div>'
      +'<div><div style="'+_MLL+'">본문</div><textarea id="mlBody" rows="11" style="'+_MLI+';line-height:1.55;resize:vertical">'+esc(d.body)+'</textarea></div>'
      +'<div style="display:flex;gap:16px;align-items:center;font-size:12.5px;color:#374151;flex-wrap:wrap"><span style="font-weight:700;color:#14305c">첨부</span><label style="display:flex;align-items:center;gap:5px;cursor:pointer"><input type="checkbox" id="mlAttPdf" checked> 견적서 PDF</label><label style="display:flex;align-items:center;gap:5px;cursor:pointer"><input type="checkbox" id="mlAttHtml" checked> 견적서 HTML (카탈로그·도면 링크)</label><span style="color:#9ca3af">보낸이 '+esc(d.fromName)+' &lt;chjk@chjk.co.kr&gt;</span></div>'
      +'<div id="mlStatus" style="font-size:12.5px;color:#6b7280;min-height:18px"></div>'
      +'<div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn" onclick="document.getElementById(\'mailSendOverlay\').style.display=\'none\'">닫기</button><button class="btn btn-primary" id="mlSendBtn" onclick="qMailSendNow()">보내기</button></div>'
      +'</div>', 720);
    window._mlDraft=d;
  };
  window.qMailSendNow=async function(){
    var st=document.getElementById('mlStatus'), btn=document.getElementById('mlSendBtn');
    var to=(document.getElementById('mlTo').value||'').trim(), cc=(document.getElementById('mlCc').value||'').trim(), subj=(document.getElementById('mlSubj').value||'').trim(), body=document.getElementById('mlBody').value||'';
    var wantPdf=document.getElementById('mlAttPdf').checked, wantHtml=document.getElementById('mlAttHtml').checked;
    if(!to){ st.innerHTML='<span style="color:#dc2626">받는 사람을 입력하세요.</span>'; return; }
    var badAddr=to.split(/[,;\s]+/).filter(Boolean).find(function(a){ return !/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(a); });
    if(badAddr){ st.innerHTML='<span style="color:#dc2626">주소 형식이 이상합니다: '+esc(badAddr)+'</span>'; return; }
    var cfg=await _mailLoadCfg(); var d=window._mlDraft||_mailQuoteDraft();
    btn.disabled=true; btn.textContent='보내는 중…';
    try{
      st.textContent='견적 저장 중…';
      try{ await _qPersistQuote(); }catch(_pe){ st.textContent='견적 저장 실패 — 메일은 계속 보냅니다'; }
      var atts=[]; var fn=('견적서 '+(d.no||d.vname||'견적')).replace(/[<>:"/\\|?*]/g,' ').replace(/\s+/g,' ').trim();
      if(wantPdf){ st.textContent='PDF 만드는 중…'; var pb=await _qMakePdfBlob(); atts.push({name:fn+'.pdf', type:'application/pdf', b64:await _blobToB64(pb)}); }
      if(wantHtml){ st.textContent='HTML 만드는 중…'; var h=await _qBuildQuoteHtml(); atts.push({name:fn+'.html', type:'text/html', b64:await _blobToB64(new Blob([h],{type:'text/html;charset=utf-8'}))}); }
      st.textContent='발송 중…';
      var html='<div style="font-family:\'Malgun Gothic\',\'맑은 고딕\',sans-serif;font-size:14px;line-height:1.7;color:#1f2937;white-space:pre-wrap">'+esc(body)+'</div>';
      var r=await fetch(_mailUrl(cfg,'/send'), {method:'POST', headers:{'Content-Type':'application/json','X-Mail-Key':cfg.key}, body:JSON.stringify({to:to, cc:cc, subject:subj, text:body, html:html, fromName:d.fromName, attachments:atts})});
      var j=null; try{ j=await r.json(); }catch(_j){}
      if(!r.ok||!j||!j.ok) throw new Error((j&&j.error)||('HTTP '+r.status));
      _qMailLog(d.no, to, atts.map(function(a){return a.name;}));
      document.getElementById('mailSendOverlay').style.display='none';
      showInfoModal('메일 발송 완료', '"'+esc(d.no)+'" 견적서를 보냈습니다.\n\n받는 사람: '+esc(to)+(cc?('\n참조: '+esc(cc)):'')+'\n첨부: '+(atts.length?atts.map(function(a){return a.name;}).join(', '):'없음')+'\n\n이 견적은 "'+esc(d.no)+'" 번호로 자동 저장되었고, 불러오기 목록에 ✉ 표시가 붙습니다.');
    }catch(e){ st.innerHTML='<span style="color:#dc2626">발송 실패: '+esc(e&&e.message||String(e))+'</span>'; }
    finally{ btn.disabled=false; btn.textContent='보내기'; }
  };
  function _qMailLog(no, to, files){
    var who=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)||'';
    var q=(_qLoadedId?quoteSaved.find(function(x){ return x.id===_qLoadedId; }):null)||quoteSaved.find(function(x){ return x.title===no; });
    if(!q) return;
    q.mail=(q.mail||[]).concat([{at:Date.now(), to:to, by:who, files:files||[]}]);
    saveAll();
  }
"""

OPS = [
  [MENU_OLD, MENU_NEW, 1, "MENU"],
  [LIST_OLD, LIST_NEW, 1, "LIST_BADGE"],
  ["  // ─── r227: 신규 영업 응원 배너 · 업무회의 2주 주기 ───", JS + "  // ─── r227: 신규 영업 응원 배너 · 업무회의 2주 주기 ───", 1, "JS"],
  ["<!-- test build r234 2026-10-14 -->", "<!-- test build r235 2026-10-14 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R235 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r235(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r235 브라우저 적용기 — edits_r235.py 의 OPS. r234(live 49525ec2 / test 9825f11c) 위에 적용.",
             "function r235Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R235 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r235Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r235(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r235 applied:', path)
