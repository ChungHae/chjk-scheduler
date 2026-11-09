
  // ─── r257: 업체·매입처 담당자에게 바로 메일 (전산 발송 / 네이버 웍스에서 쓰기) ───
  var _MQ_WORKS_WRITE='https://mail.worksmobile.com/w/write';   // 웍스 작성 화면 (to·subject 쿼리)
  window._mq=null;
  // o: { vname, book:[{email,name,tag}], to:[], subject, body, kind:'client'|'vendor' }
  window.mailQuickOpen=function(o){ o=o||{};
    var vname=String(o.vname||'').trim();
    var book=Array.isArray(o.book)?o.book:(vname?_mailAddrBook(vname):[]);
    var to=(o.to||[]).filter(function(e){ return _ML_RE.test(e); });
    if(!to.length && book.length===1) to=[book[0].email];
    var my=_pvMyEmail();
    window._mq={ vname:vname, book:book, to:to, cc:my, my:my, kind:o.kind||'client', subj:o.subject||'', body:o.body||'', subjEdited:!!o.subject, bodyEdited:!!o.body };
    _mqRender();
  };
  function _mqWho(){ var q=window._mq; var c=(q.to||[]).map(function(e){ return q.book.find(function(b){ return b.email.toLowerCase()===e.toLowerCase(); }); }).find(function(b){ return b&&b.name; }); return c?c.name:''; }
  function _mqDefaults(){ var q=window._mq; var m=_pvMe(); var SUP=_qSupplierInfo(m.branch); var who=_mqWho();
    if(!q.subjEdited) q.subj='[충해전기] '+(q.vname?q.vname+' ':'')+'안내';
    if(!q.bodyEdited) q.body=(q.vname?q.vname+' ':'')+(who?who+' 님':'담당자님')+', 안녕하세요.\n'+SUP.corp+' '+m.staff+'입니다.\n\n\n\n감사합니다.\n\n─────────────────\n'+m.staff+(m.phone?' · '+m.phone:'')+(q.my?' · '+q.my:'')+'\n'+SUP.corp+' · TEL '+SUP.tel+' · FAX '+SUP.fax+'\n'+SUP.addr.replace(/\n/g,' ');
  }
  function _mqWorksUrl(){ var q=window._mq; var to=_mlSplit((document.getElementById('mqTo')||{}).value||q.to.join(',')); var subj=(document.getElementById('mqSubj')||{}).value||q.subj; return _MQ_WORKS_WRITE+'?to='+encodeURIComponent(to.join(','))+(subj?'&subject='+encodeURIComponent(subj):''); }
  function _mqRender(){ var q=window._mq; if(!q) return; _mqDefaults();
    var toL=q.to.map(function(e){ return e.toLowerCase(); });
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">메일 보내기 <span style="font-size:12px;font-weight:500;color:#6b7280;margin-left:6px">'+esc(q.vname||'')+'</span></span><button class="btn" onclick="document.getElementById(\'mailQuickOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:14px 20px;display:flex;flex-direction:column;gap:11px">';
    h+='<div><div style="'+_MLL+'">받는 사람 <span style="font-weight:400;color:#9ca3af">— 여러 명은 쉼표 · 아래 담당자를 눌러 넣기/빼기</span></div><input id="mqTo" value="'+esc(q.to.join(', '))+'" placeholder="받는 사람 메일" style="'+_MLI+'" onchange="mqTo(this.value)">';
    h+='<div class="ml-book" style="margin-top:6px">'+(q.book.length?q.book.map(function(b,i){ var on=toL.indexOf(b.email.toLowerCase())>=0; return '<span class="ml-chip'+(on?' on':'')+'" onclick="mqChip('+i+')" title="'+esc(b.email)+'">'+(on?'✓ ':'')+(b.name?('<b>'+esc(b.name)+'</b> '):'')+(b.tag?('<i>'+esc(b.tag)+'</i> '):'')+esc(b.email)+'</span>'; }).join(''):'<span class="ml-book-empty">이 업체에 저장된 메일 주소가 없습니다. 받는 사람에 직접 적어 주세요 — 보내면 업체 담당자로 기억합니다.</span>')+'</div></div>';
    h+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div><div style="'+_MLL+'">참조(CC)</div><input id="mqCc" value="'+esc(q.cc||'')+'" style="'+_MLI+'" onchange="window._mq.cc=this.value"></div>'
      +'<div><div style="'+_MLL+'">회신 받을 내 메일 (Reply-To)</div><input id="mqMy" value="'+esc(q.my||'')+'" placeholder="이름@chjk.co.kr" style="'+_MLI+'" onchange="mqMy(this.value)"></div></div>';
    h+='<div><div style="'+_MLL+'">제목</div><input id="mqSubj" value="'+esc(q.subj)+'" style="'+_MLI+'" oninput="window._mq.subj=this.value; window._mq.subjEdited=true"></div>';
    h+='<div><div style="'+_MLL+';display:flex;align-items:center">본문<a onclick="window._mq.subjEdited=false; window._mq.bodyEdited=false; _mqRender()" style="margin-left:auto;font-weight:500;color:#1B3A6B;text-decoration:underline;cursor:pointer;font-size:11px">기본 문구로 되돌리기</a></div><textarea id="mqBody" style="'+_MLI+';min-height:220px;resize:vertical;line-height:1.55" oninput="window._mq.body=this.value; window._mq.bodyEdited=true">'+esc(q.body)+'</textarea></div>';
    h+='<div style="display:flex;align-items:center;gap:10px;padding-top:4px;border-top:1px solid #eef1f4;flex-wrap:wrap"><span id="mqSt" style="font-size:12px;color:#6b7280;flex:1;min-width:120px"></span>'
      +'<button class="btn" onclick="mqOpenWorks()" title="네이버 웍스 메일 작성 화면을 새 탭에 엽니다 (받는 사람·제목 채워짐). 웍스에 로그인돼 있어야 합니다." style="padding:7px 12px;border-color:#03c75a;color:#03843d;font-weight:700">네이버 웍스에서 쓰기 ↗</button>'
      +'<button id="mqSend" class="btn" onclick="mailQuickSend()" style="padding:7px 18px;background:#1B3A6B;color:#fff;border-color:#1B3A6B;font-weight:700">전산에서 바로 보내기</button></div>';
    h+='<div style="font-size:11px;color:#9ca3af;margin-top:-4px">전산 발송은 지점 공용 계정(chjk@ / 화성)으로 나가고, 답장은 "회신 받을 내 메일"로 옵니다. 첨부가 필요하면 [네이버 웍스에서 쓰기]를 쓰세요.</div>';
    h+='</div>';
    _mailOverlay('mailQuickOverlay', h, 720);
  }
  window.mqTo=function(v){ var q=window._mq; if(!q) return; q.to=_mlSplit(v); _mqRender(); };
  window.mqChip=function(i){ var q=window._mq; if(!q) return; var b=q.book[i]; if(!b) return; var k=b.email.toLowerCase(); var idx=q.to.findIndex(function(a){ return a.toLowerCase()===k; }); if(idx>=0) q.to.splice(idx,1); else q.to.push(b.email); _mqRender(); };
  window.mqMy=function(v){ var q=window._mq; if(!q) return; q.my=String(v||'').trim(); var cc=_mlSplit(q.cc); if(q.my&&!cc.some(function(a){ return a.toLowerCase()===q.my.toLowerCase(); })) cc.push(q.my); q.cc=cc.join(', '); _mqRender(); };
  window.mqOpenWorks=function(){ var q=window._mq; if(!q) return; q.to=_mlSplit((document.getElementById('mqTo')||{}).value); if(!q.to.length){ document.getElementById('mqSt').innerHTML='<span style="color:#dc2626">받는 사람을 먼저 넣어 주세요.</span>'; return; } var u=_mqWorksUrl(); var w=window.open(u,'_blank','noopener'); if(!w){ document.getElementById('mqSt').innerHTML='<span style="color:#b45309">팝업이 막혔습니다 — 주소창 오른쪽 팝업 허용 후 다시 누르세요.</span>'; return; } try{ if(q.vname && q.kind==='client') _mailRemember(q.vname, _mqWho(), q.to.join(', ')); }catch(_e){} document.getElementById('mqSt').textContent='웍스 작성 화면을 새 탭에 열었습니다.'; };
  window.mailQuickSend=async function(){ var q=window._mq; if(!q) return; var st=document.getElementById('mqSt'), btn=document.getElementById('mqSend');
    var to=_mlSplit((document.getElementById('mqTo')||{}).value); q.to=to; if(!to.length){ st.innerHTML='<span style="color:#dc2626">받는 사람을 넣어 주세요.</span>'; return; }
    q.cc=(document.getElementById('mqCc')||{}).value||''; var bad=to.concat(_mlSplit(q.cc)).find(function(a){ return !_ML_RE.test(a); }); if(bad){ st.innerHTML='<span style="color:#dc2626">주소 형식이 이상합니다: '+esc(bad)+'</span>'; return; }
    q.my=String((document.getElementById('mqMy')||{}).value||'').trim(); if(q.my&&!_ML_RE.test(q.my)){ st.innerHTML='<span style="color:#dc2626">회신 받을 내 메일 주소 형식이 이상합니다.</span>'; return; }
    var subj=(document.getElementById('mqSubj')||{}).value||q.subj, body=(document.getElementById('mqBody')||{}).value||q.body;
    if(!String(body).replace(/\s/g,'')){ st.innerHTML='<span style="color:#dc2626">본문이 비어 있습니다.</span>'; return; }
    var cfg=await _mailLoadCfg(true); if(cfg._loadErr){ st.innerHTML='<span style="color:#dc2626">메일 설정을 불러오지 못했습니다. 잠시 후 다시 눌러 주세요.</span>'; return; }
    if(!cfg.url||!cfg.key){ st.innerHTML='<span style="color:#dc2626">메일 발송 설정이 아직 없습니다 (관리자 · 견적 다운로드 > 메일 설정).</span>'; return; }
    var m=_pvMe(); var SUP=_qSupplierInfo(m.branch); var cc=_mlSplit(q.cc).filter(function(a){ return to.map(function(t){ return t.toLowerCase(); }).indexOf(a.toLowerCase())<0; }).join(', ');
    btn.disabled=true; btn.textContent='보내는 중…'; st.textContent='발송 중…';
    try{
      var html='<div style="font-family:\'Malgun Gothic\',\'맑은 고딕\',sans-serif;font-size:14px;line-height:1.7;color:#1f2937;white-space:pre-wrap">'+esc(body)+'</div>';
      var r=await fetch(_mailUrl(cfg,'/send'), {method:'POST', headers:{'Content-Type':'application/json','X-Mail-Key':cfg.key}, body:JSON.stringify({account:_mailAcctOf(m.branch), to:to.join(', '), cc:cc, replyTo:q.my||'', subject:subj, text:body, html:html, fromName:SUP.corp+' '+m.staff, attachments:[]})});
      var j=null; try{ j=await r.json(); }catch(_j){}
      if(!r.ok||!j||!j.ok) throw new Error((j&&j.error)||('HTTP '+r.status));
      var rem=0; try{ if(q.vname && q.kind==='client') rem=_mailRemember(q.vname, _mqWho(), to.join(', ')); }catch(_e){}
      _pvSaveMyEmail(q.my);
      document.getElementById('mailQuickOverlay').style.display='none';
      showInfoModal('메일 발송 완료', (q.vname?esc(q.vname)+' 에 ':'')+'메일을 보냈습니다.\n\n받는 사람: '+esc(to.join(', '))+(cc?('\n참조: '+esc(cc)):'')+(q.my?('\n회신 받을 곳: '+esc(q.my)):'')+(rem?('\n\n새 주소 '+rem+'건을 업체 담당자로 기억했습니다.'):''));
    }catch(e){ st.innerHTML='<span style="color:#dc2626">발송 실패: '+esc(e&&e.message||String(e))+'</span>'; }
    finally{ btn.disabled=false; btn.textContent='전산에서 바로 보내기'; }
  };
  // 업체 관리 목록의 ✉
  window.clxMailOpen=function(ev, nm){ try{ ev.stopPropagation(); }catch(_e){} mailQuickOpen({ vname:nm, kind:'client' }); };
  // 매입처 카드의 담당자 메일 → 바로 쓰기
  window.pvMailOpen=function(ev, vid, email){ try{ ev.preventDefault(); ev.stopPropagation(); }catch(_e){} var v=_pvVendors().find(function(x){ return x.id===vid; }); if(!v) return;
    var book=[]; (v.contacts||[]).forEach(function(c){ if(c&&c.email&&_ML_RE.test(c.email)) book.push({ email:c.email, name:c.name||'', tag:c.role||'' }); });
    mailQuickOpen({ vname:String(v.distributor||v.brand||''), kind:'vendor', book:book, to:email?[email]:[] }); };
