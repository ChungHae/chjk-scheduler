
  // ─── r265: 매입처 문의 메일 간단하게 — 받는 사람 · 참조 · 제목 · 본문만 (품번·수량은 본문에 자유롭게) ───
  window.pvInqOpen=function(o){ if(typeof _guardW==='function' && !_guardW()) return; o=o||{};
    var vendor=o.vendorId?_pvVendors().find(function(v){ return v.id===o.vendorId; }):null;
    var brand=String(o.brand||(vendor&&vendor.brand)||'').trim();
    var vlist=vendor?[vendor]:_pvBrandVendors(brand);
    var book=[]; vlist.forEach(function(v){ (v.contacts||[]).forEach(function(c){ var e=String((c&&c.email)||'').trim(); if(!_ML_RE.test(e)) return; if(book.some(function(b){ return b.email.toLowerCase()===e.toLowerCase(); })) return; book.push({ email:e, name:String(c.name||'').trim(), tag:String(c.role||'').trim(), vname:String(v.distributor||v.brand||'').trim() }); }); });
    var to=[]; if(o.to) to=o.to.slice(); else if(book.length) to=[book[0].email];
    var vname=vendor?String(vendor.distributor||vendor.brand||''):(vlist.length===1?String(vlist[0].distributor||vlist[0].brand||''):'');
    var my=_pvMyEmail();
    window._pvq={ vendorId:vendor?vendor.id:'', vname:vname, brand:brand, book:book, to:to, cc:my, my:my, items:(o.items||[]), subj:'', body:'', bodyEdited:false };
    _pvq2Render(true); };
  function _pvq2Who(){ var q=window._pvq; var c=(q.to||[]).map(function(e){ return q.book.find(function(b){ return b.email.toLowerCase()===e.toLowerCase(); }); }).find(function(b){ return b&&b.name; }); return c?c.name:''; }
  function _pvq2Body(){ var q=window._pvq; var m=_pvMe(); var SUP=_qSupplierInfo(m.branch); var who=_pvq2Who();
    var lines=(q.items||[]).filter(function(it){ return it&&String(it.spec||'').trim(); }).map(function(it){ return '- '+it.spec+(it.name?(' ('+it.name+')'):'')+' × '+(Number(it.qty)||1); });
    return (q.vname?q.vname+' ':'')+(who?who+' 님':'담당자님')+', 안녕하세요.\n'+SUP.corp+' '+m.staff+'입니다.\n\n아래 품목 견적 및 납기 문의드립니다.\n\n'+(lines.length?lines.join('\n')+'\n':'\n')+'\n감사합니다.\n\n─────────────────\n'+m.staff+(m.phone?' · '+m.phone:'')+(q.my?' · '+q.my:'')+'\n'+SUP.corp+' · TEL '+SUP.tel+' · FAX '+SUP.fax+'\n'+SUP.addr.replace(/\n/g,' '); }
  function _pvq2Render(first){ var q=window._pvq; if(!q) return;
    if(!q.subj) q.subj='[충해전기] 견적 문의드립니다';
    if(!q.bodyEdited) q.body=_pvq2Body();
    var toL=(q.to||[]).map(function(e){ return e.toLowerCase(); });
    var chips=q.book.length?q.book.map(function(b,i){ var on=toL.indexOf(b.email.toLowerCase())>=0; return '<span class="ml-chip'+(on?' on':'')+'" onclick="pvq2Chip('+i+')" title="'+esc(b.email)+'">'+(on?'✓ ':'')+(b.name?('<b>'+esc(b.name)+'</b> '):'')+(b.tag?('<i>'+esc(b.tag)+'</i> '):'')+esc(b.email)+'</span>'; }).join('')
      :'<span class="ml-book-empty">저장된 담당자 메일이 없습니다. 받는 사람에 적어 보내면 다음부터 여기 나옵니다.</span>';
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">문의 메일 <span style="font-size:13px;font-weight:600;color:#334155;margin-left:6px">'+esc(q.vname||q.brand||'')+(q.brand&&q.vname?' <span style="font-weight:400;color:#9ca3af">· '+esc(q.brand)+'</span>':'')+'</span></span><button class="btn" onclick="document.getElementById(\'pvInqOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:14px 20px;display:flex;flex-direction:column;gap:10px">'
      +'<div><div style="'+_MLL+'">받는 사람</div><input id="pvqTo" value="'+esc((q.to||[]).join(', '))+'" placeholder="담당자 메일 (여러 명은 쉼표)" style="'+_MLI+'" onchange="pvq2To(this.value)"><div class="ml-book" style="margin-top:6px">'+chips+'</div></div>'
      +'<div><div style="'+_MLL+'">참조</div><input id="pvqCc" value="'+esc(q.cc||'')+'" style="'+_MLI+'" onchange="window._pvq.cc=this.value"></div>'
      +'<div><div style="'+_MLL+'">제목</div><input id="pvqSubj" value="'+esc(q.subj)+'" style="'+_MLI+'" oninput="window._pvq.subj=this.value"></div>'
      +'<div><div style="'+_MLL+'">본문 <span style="font-weight:400;color:#9ca3af">— 품번·수량·납기를 그대로 적어 주세요</span></div><textarea id="pvqBody" style="'+_MLI+';min-height:300px;resize:vertical;line-height:1.6" oninput="window._pvq.body=this.value; window._pvq.bodyEdited=true">'+esc(q.body)+'</textarea></div>'
      +'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding-top:6px;border-top:1px solid #eef1f4"><span style="font-size:12px;color:#6b7280">답장 받을 메일</span><input id="pvqMy" value="'+esc(q.my||'')+'" placeholder="이름@chjk.co.kr" style="'+_MLI+';width:210px;padding:5px 8px;font-size:12px" onchange="pvq2My(this.value)"><span id="pvqSt" style="font-size:12px;color:#6b7280;flex:1;min-width:80px"></span><button class="btn" onclick="pvInqBox()" style="padding:7px 12px">문의함</button><button id="pvqSend" class="btn" onclick="pvInqSend()" style="padding:7px 20px;background:#1B3A6B;color:#fff;border-color:#1B3A6B;font-weight:700">보내기</button></div>'
      +'</div>';
    _mailOverlay('pvInqOverlay', h, 720);
    if(first) setTimeout(function(){ var ta=document.getElementById('pvqBody'); if(!ta) return; var k=ta.value.indexOf('문의드립니다.\n\n'); if(k>=0){ var p=k+'문의드립니다.\n\n'.length; ta.focus(); ta.setSelectionRange(p,p); ta.scrollTop=0; } }, 40);
  }
  window.pvq2Chip=function(i){ var q=window._pvq; if(!q) return; var b=q.book[i]; if(!b) return; q.to=_mlSplit((document.getElementById('pvqTo')||{}).value); var k=b.email.toLowerCase(); var ix=q.to.findIndex(function(a){ return a.toLowerCase()===k; }); if(ix>=0) q.to.splice(ix,1); else q.to.push(b.email); _pvq2Keep(); _pvq2Render(); };
  window.pvq2To=function(v){ var q=window._pvq; if(!q) return; q.to=_mlSplit(v); _pvq2Keep(); _pvq2Render(); };
  window.pvq2My=function(v){ var q=window._pvq; if(!q) return; var old=q.my; q.my=String(v||'').trim(); var cc=_mlSplit((document.getElementById('pvqCc')||{}).value).filter(function(a){ return !old || a.toLowerCase()!==old.toLowerCase(); }); if(q.my && !cc.some(function(a){ return a.toLowerCase()===q.my.toLowerCase(); })) cc.push(q.my); q.cc=cc.join(', '); _pvq2Keep(); _pvq2Render(); };
  function _pvq2Keep(){ var q=window._pvq; var s=document.getElementById('pvqSubj'), b=document.getElementById('pvqBody'), c=document.getElementById('pvqCc'); if(s) q.subj=s.value; if(b && q.bodyEdited) q.body=b.value; if(c && document.activeElement!==document.getElementById('pvqMy')) q.cc=c.value; }
  window.pvInqSend=async function(){ var q=window._pvq; if(!q) return; var st=document.getElementById('pvqSt'), btn=document.getElementById('pvqSend');
    var to=_mlSplit((document.getElementById('pvqTo')||{}).value); if(!to.length){ st.innerHTML='<span style="color:#dc2626">받는 사람을 넣어 주세요.</span>'; return; }
    var ccRaw=(document.getElementById('pvqCc')||{}).value||''; var bad=to.concat(_mlSplit(ccRaw)).find(function(a){ return !_ML_RE.test(a); }); if(bad){ st.innerHTML='<span style="color:#dc2626">주소 형식 확인: '+esc(bad)+'</span>'; return; }
    var my=String((document.getElementById('pvqMy')||{}).value||'').trim(); if(my && !_ML_RE.test(my)){ st.innerHTML='<span style="color:#dc2626">답장 받을 메일 형식 확인</span>'; return; }
    var subj=String((document.getElementById('pvqSubj')||{}).value||'').trim()||'[충해전기] 견적 문의드립니다'; var body=(document.getElementById('pvqBody')||{}).value||'';
    var cfg=await _mailLoadCfg(true); if(cfg._loadErr){ st.innerHTML='<span style="color:#dc2626">메일 설정을 불러오지 못했습니다. 잠시 후 다시.</span>'; return; }
    if(!cfg.url||!cfg.key){ st.innerHTML='<span style="color:#dc2626">메일 발송 설정이 없습니다 (관리자).</span>'; return; }
    var m=_pvMe(); var SUP=_qSupplierInfo(m.branch); var cc=_mlSplit(ccRaw).filter(function(a){ return to.map(function(t){ return t.toLowerCase(); }).indexOf(a.toLowerCase())<0; }).join(', ');
    btn.disabled=true; btn.textContent='보내는 중…'; st.textContent='';
    try{
      var html='<div style="font-family:\'Malgun Gothic\',\'맑은 고딕\',sans-serif;font-size:14px;line-height:1.7;color:#1f2937;white-space:pre-wrap">'+esc(body)+'</div>';
      var r=await fetch(_mailUrl(cfg,'/send'), {method:'POST', headers:{'Content-Type':'application/json','X-Mail-Key':cfg.key}, body:JSON.stringify({account:_mailAcctOf(m.branch), to:to.join(', '), cc:cc, replyTo:my||'', subject:subj, text:body, html:html, fromName:SUP.corp+' '+m.staff, attachments:[]})});
      var j=null; try{ j=await r.json(); }catch(_j){}
      if(!r.ok||!j||!j.ok) throw new Error((j&&j.error)||('HTTP '+r.status));
      if(typeof pvInq==='undefined') window.pvInq=[];
      pvInq.push({ id:uid(), no:_pvInqNo(), at:Date.now(), by:m.staff, brand:q.brand, vendors:q.vname?[q.vname]:[], to:to, cc:cc, replyTo:my, subject:subj, body:body, items:[], status:'wait' });
      // 새 주소는 그 매입처 담당자로 기억
      try{ var v=q.vendorId?_pvVendors().find(function(x){ return x.id===q.vendorId; }):null; if(v){ v.contacts=Array.isArray(v.contacts)?v.contacts:[]; to.forEach(function(e){ if(!v.contacts.some(function(c){ return String((c&&c.email)||'').toLowerCase()===e.toLowerCase(); })) v.contacts.push({role:'',name:'',phone:'',email:e}); }); } }catch(_e){}
      _pvSaveMyEmail(my); saveAll();
      document.getElementById('pvInqOverlay').style.display='none';
      try{ _mtToast('문의 메일을 보냈습니다 — 문의함에 기록'); }catch(_e2){}
      try{ renderPurchasePage(); }catch(_e3){}
    }catch(e){ st.innerHTML='<span style="color:#dc2626">발송 실패: '+esc(e&&e.message||String(e))+'</span>'; }
    finally{ btn.disabled=false; btn.textContent='보내기'; } };
  window.pvInqAgain=function(id){ var q0=(typeof pvInq!=='undefined'?pvInq:[]).find(function(x){ return x&&x.id===id; }); if(!q0) return; document.getElementById('pvInqBoxOverlay').style.display='none';
    var v=_pvVendors().find(function(x){ return q0.vendors && q0.vendors[0] && String(x.distributor||x.brand||'')===q0.vendors[0]; });
    pvInqOpen({ vendorId:v?v.id:'', brand:q0.brand, to:(q0.to||[]).slice() }); var q=window._pvq; q.subj=q0.subject||q.subj; if(q0.body){ q.body=q0.body; q.bodyEdited=true; } _pvq2Render(); };
