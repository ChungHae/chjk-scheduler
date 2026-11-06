
  // ─── r255: 매입처(브랜드 대리점) 품번 문의 메일 · 담당자 연동 · 문의함 ───
  // 품번 접두로 브랜드를 "추천"만 한다(틀리면 사람이 고름). 규칙은 아래 표에 추가.
  var _PV_BRAND_RULES=[
    [/^(4G|4F|4K|3G|AB\d|AG\d|AP\d|ADK|SSD|SCS|SCA|CMK|STG|STS|STK|STR|W\d{4}|F\d{4}|R\d{4}|FCS|CAC|GAB|NAB|USB\d|AMD|AMG|HNB|HMB|HPS|M\d{4})/i,'CKD'],
    [/^(DSNU|DSBC|DSBG|ADN|ADVU|ADVC|DGC|DNC|ESNU|VUVG|VUVS|VUWG|VUVB|MFH|MEBH|JMFH|CPE|QS[LTMF]?\b|QS-|PUN|PAN|PLN|MS[2469]|LFR|LR-|HE-|HEE|SMT|SME|SMBR|DFM|DGPL|EGC|ELGR|DSL|DRRD|DFPB|DHPS|HGPL|DHDS|VABM|VMPA|CPV|EB-|ESS)/i,'FESTO'],
    [/^(PC\d|PL\d|PCF|PLF|PLL|PV\d|PU\d|PB\d|PY\d|PE\d|PM\d|PD\d|PG\d|PLG|PSE|VKL|VRL|CPS|JSC|JSS|JSU|PSC|VLC|VB\d|VC\d|VK\d|PGU|PQ\d|PK\d|PKF|PKG|PF\d)/i,'PISCO'],
    [/^(SC\d|SI\d|SU\d|MAL|MA\d|MI\d|TN\d|TR\d|4V\d|3V\d|4A\d|4M\d|AFR|AFC|BFR|BFC|GFR|GFC|GC\d|GAR|GAW|GAC|HLQ|HLH|TCL|TCM|ACQ|ACE|ACP|STA|HFZ|HFY|HFK|SDA|SDAD|CQ2)/i,'AirTAC'],
    [/^(MC\d|CV\d|VBB|VBM|VPB|VPL|ML\d|MVA|PH\d|PJG|PFG|PBG|PAG|NAP|CB\d|CVN|MVB|NC\d|PCG|PJT|PFT|PBT|SPG|SSG)/i,'CONVUM'],
    [/^(N\d-|NT\d|NMP|NMF|NU-|NA-|NB-|NC-|PV-|UB-|UA-)/i,'NITTA'],
    [/^(YPC|YMV|YSV|YCP|YMC|YPA|YSF|YHS|YPD)/i,'YPC'],
    [/^(TPC|TGC|TFR|TFC|TAF|TAR|TAL|TRM|TMI|TDA|TCC|TCD|TCQ|TRS)/i,'TPC'],
    [/^(GPC|GPL|GPT|GPY|GPH|GPX|GPU|GPG|GPD|GPV|GPK|GPMF|GPFF|SPC|SPL|SPY|SPH|SPT|SAPC|SAPL)/i,'상아'],
    [/^(KH-|KA-|KBB|KS-|KT-|KPB|KPL|KL-|KM-|KHM|KPS)/i,'KOINO'],
    [/^(CDC|CDQ-?C|CS\d|CSL|CSD|CGL|CGS|CDS)/i,'CDC']
  ];
  function _pvGuessBrand(spec){ var s=String(spec||'').trim(); if(!s) return ''; for(var i=0;i<_PV_BRAND_RULES.length;i++){ if(_PV_BRAND_RULES[i][0].test(s)) return _PV_BRAND_RULES[i][1]; } return ''; }
  function _pvBk(s){ return String(s||'').trim().toLowerCase().replace(/[\s\-_.()㈜주식회사]/g,''); }
  function _pvVendors(){ return (typeof purchaseVendors!=='undefined'&&purchaseVendors)?purchaseVendors:[]; }
  function _pvBrandList(){ var seen={}, out=[]; _pvVendors().forEach(function(v){ var b=String(v.brand||'').trim(); if(!b) return; var k=_pvBk(b); if(seen[k]) return; seen[k]=1; out.push(b); }); return out.sort(function(a,b){ return a.localeCompare(b); }); }
  function _pvBrandVendors(brand){ var k=_pvBk(brand); if(!k) return []; return _pvVendors().filter(function(v){ if(_pvBk(v.brand)===k) return true; var kw=String(v.keywords||'').split(/[,;/\s]+/).map(_pvBk).filter(Boolean); return kw.indexOf(k)>=0; }); }
  function _pvResolveBrand(guess){ if(!guess) return ''; var k=_pvBk(guess); var hit=_pvBrandList().find(function(b){ return _pvBk(b)===k; }); if(hit) return hit; var v=_pvVendors().find(function(x){ return String(x.keywords||'').split(/[,;/\s]+/).map(_pvBk).indexOf(k)>=0; }); return v?String(v.brand||'').trim():guess; }
  function _pvContacts(brand){   // [{vid, vname, role, name, phone, email}]
    var out=[], seen={};
    _pvBrandVendors(brand).forEach(function(v){ (v.contacts||[]).forEach(function(c){ var e=String((c&&c.email)||'').trim(); if(!e||!_ML_RE.test(e)) return; var k=e.toLowerCase(); if(seen[k]) return; seen[k]=1; out.push({ vid:v.id, vname:String(v.distributor||v.brand||'').trim(), role:String(c.role||'').trim(), name:String(c.name||'').trim(), phone:String(c.phone||'').trim(), email:e }); }); });
    return out;
  }
  function _pvMe(){ var staff=(typeof _authUser!=='undefined'&&_authUser&&_authUser.name)?_authUser.name:''; var me=(typeof members!=='undefined'&&members)?members.find(function(x){ return (x.name||'').trim()===staff; }):null; return { staff:staff, me:me, branch:(me&&me.group)?me.group:'서울', phone:(me&&me.phone)?me.phone:'' }; }
  function _pvMyEmail(){ var m=_pvMe(); if(m.me&&m.me.email&&_ML_RE.test(m.me.email)) return m.me.email; try{ return localStorage.getItem('pv_my_email_'+(m.staff||''))||''; }catch(_e){ return ''; } }
  function _pvSaveMyEmail(v){ v=String(v||'').trim(); var m=_pvMe(); try{ localStorage.setItem('pv_my_email_'+(m.staff||''), v); }catch(_e){} if(m.me && _ML_RE.test(v) && m.me.email!==v){ m.me.email=v; try{ saveAll(); }catch(_e2){} } }
  function _pvInqNo(){ var d=new Date(); var ymd=String(d.getFullYear()).slice(2)+('0'+(d.getMonth()+1)).slice(-2)+('0'+d.getDate()).slice(-2); var n=1; (typeof pvInq!=='undefined'?pvInq:[]).forEach(function(q){ var m=String(q.no||'').match(/^CHJK-Q(\d{6})-(\d+)$/); if(m&&m[1]===ymd&&Number(m[2])>=n) n=Number(m[2])+1; }); return 'CHJK-Q'+ymd+'-'+('0'+n).slice(-2); }
  function _pvItemsFromCart(){ var out=[]; (typeof _qCart!=='undefined'?_qCart:[]).forEach(function(c){ var s=String((c&&c.spec)||'').trim(); if(!s) return; out.push({ spec:s, name:String(c.name||'').trim(), qty:Number(c.qty)||1, on:true }); }); return out; }
  window._pvq=null;
  window.pvInqOpen=function(o){ if(typeof _guardW==='function' && !_guardW()) return; o=o||{};
    var items=o.fromCart?_pvItemsFromCart():[]; if(o.items) items=o.items.map(function(x){ return { spec:x.spec||'', name:x.name||'', qty:Number(x.qty)||1, on:true }; });
    if(o.fromCart && !items.length){ showInfoModal('매입처 문의','견적 목록에 품번이 없습니다.\n품번을 먼저 적어 주세요.'); return; }
    if(!items.length) items.push({ spec:'', name:'', qty:1, on:true });
    var brand=o.brand||''; var vendor=o.vendorId?_pvVendors().find(function(v){ return v.id===o.vendorId; }):null; if(vendor&&!brand) brand=String(vendor.brand||'').trim();
    var guess=''; if(!brand){ var cnt={}; items.forEach(function(it){ var g=_pvGuessBrand(it.spec); if(g) cnt[g]=(cnt[g]||0)+1; }); var best=Object.keys(cnt).sort(function(a,b){ return cnt[b]-cnt[a]; })[0]; if(best){ guess=best; brand=_pvResolveBrand(best); } }
    var to=[]; if(o.email&&_ML_RE.test(o.email)) to.push(o.email); else if(vendor){ (vendor.contacts||[]).forEach(function(c){ if(c&&c.email&&_ML_RE.test(c.email)) to.push(c.email); }); }
    if(!to.length){ var bv1=_pvBrandVendors(brand); if(bv1.length===1){ (bv1[0].contacts||[]).forEach(function(c){ if(c&&c.email&&_ML_RE.test(c.email)) to.push(c.email); }); } }   // 대리점이 하나면 담당자 자동
    var my=_pvMyEmail();
    window._pvq={ items:items, brand:brand, guess:guess, to:to, cc:my, my:my, due:'', kinds:{quote:true, lead:true, stock:false, alt:false}, note:'', quoteNo:(o.fromCart&&typeof _qQuoteNo!=='undefined')?(_qQuoteNo||''):'', vname:(o.fromCart&&typeof _qCart!=='undefined'&&_qCart[0])?String(_qCart[0].vname||''):'', subjEdited:false, bodyEdited:false, subj:'', body:'' };
    _pvqRender();
  };
  function _pvqKindLabel(k){ var lab=[]; if(k.quote) lab.push('견적'); if(k.lead) lab.push('납기'); if(k.stock) lab.push('재고'); if(k.alt) lab.push('대체품'); return lab.length?lab.join(' · '):'견적'; }
  function _pvqActive(){ return (window._pvq?window._pvq.items:[]).filter(function(it){ return it.on && String(it.spec||'').trim(); }); }
  function _pvqSubject(){ var q=window._pvq; var act=_pvqActive(); var first=act.length?act[0].spec:''; return '[충해전기] '+(q.brand?q.brand+' ':'')+_pvqKindLabel(q.kinds)+' 문의 — '+first+(act.length>1?(' 외 '+(act.length-1)+'건'):'')+' ['+q.no+']'; }
  function _pvqBodyText(){ var q=window._pvq; var m=_pvMe(); var SUP=_qSupplierInfo(m.branch); var act=_pvqActive();
    var cs=_pvContacts(q.brand); var vn=''; (q.to||[]).forEach(function(e){ var c=cs.find(function(x){ return x.email.toLowerCase()===e.toLowerCase(); }); if(c&&c.vname&&!vn) vn=c.vname; }); if(!vn){ var bv=_pvBrandVendors(q.brand); if(bv.length===1) vn=String(bv[0].distributor||bv[0].brand||''); }
    var who=''; (q.to||[]).forEach(function(e){ var c=cs.find(function(x){ return x.email.toLowerCase()===e.toLowerCase(); }); if(c&&c.name&&!who) who=c.name; });
    var t=(vn?vn+' ':'')+(who?who+' 님':'담당자님')+', 안녕하세요.\n'+SUP.corp+' '+m.staff+'입니다.\n\n'
      +'아래 '+(q.brand?q.brand+' ':'')+'품목의 '+_pvqKindLabel(q.kinds)+' 확인을 부탁드립니다. (문의번호 '+q.no+')\n';
    act.forEach(function(it,i){ t+=(i+1)+'. '+it.spec+(it.name?' — '+it.name:'')+'  × '+(Number(it.qty)||1).toLocaleString()+'\n'; });
    if(q.due) t+='\n희망 납기: '+q.due+'\n';
    if(q.note) t+='\n'+q.note+'\n';
    t+='\n회신은 이 메일에 답장해 주시면 담당자('+m.staff+')에게 바로 전달됩니다.\n감사합니다.\n\n'
      +'─────────────────\n'+m.staff+(m.phone?' · '+m.phone:'')+(q.my?' · '+q.my:'')+'\n'+SUP.corp+' · TEL '+SUP.tel+' · FAX '+SUP.fax+'\n'+SUP.addr.replace(/\n/g,' ');
    return t;
  }
  function _pvqBodyHtml(text){ var q=window._pvq; var act=_pvqActive();
    var rows=act.map(function(it,i){ return '<tr><td style="padding:5px 8px;border:1px solid #d6e0ec;text-align:center">'+(i+1)+'</td><td style="padding:5px 8px;border:1px solid #d6e0ec;font-weight:700">'+esc(it.spec)+'</td><td style="padding:5px 8px;border:1px solid #d6e0ec">'+esc(it.name||'')+'</td><td style="padding:5px 8px;border:1px solid #d6e0ec;text-align:right">'+(Number(it.qty)||1).toLocaleString()+'</td></tr>'; }).join('');
    var tbl='<table style="border-collapse:collapse;font-size:13px;margin:8px 0"><thead><tr style="background:#eaf1fb"><th style="padding:5px 8px;border:1px solid #d6e0ec">No</th><th style="padding:5px 8px;border:1px solid #d6e0ec">품번</th><th style="padding:5px 8px;border:1px solid #d6e0ec">품명</th><th style="padding:5px 8px;border:1px solid #d6e0ec">수량</th></tr></thead><tbody>'+rows+'</tbody></table>';
    // 본문에서 번호 목록 줄은 표로 바꾼다 (사용자가 본문을 고쳤어도 품번 줄만 치환)
    var lines=String(text||'').split('\n'); var out=[], put=false;
    lines.forEach(function(l){ if(/^\d+\.\s.+×\s*[\d,]+\s*$/.test(l)){ if(!put){ out.push('%%TBL%%'); put=true; } return; } out.push(esc(l)); });
    var h=out.join('\n').replace('%%TBL%%', '</div>'+tbl+'<div style="white-space:pre-wrap">');
    return '<div style="font-family:\'Malgun Gothic\',\'맑은 고딕\',sans-serif;font-size:14px;line-height:1.7;color:#1f2937"><div style="white-space:pre-wrap">'+h+'</div></div>';
  }
  function _pvqRefresh(){ var q=window._pvq; if(!q) return; if(!q.no) q.no=_pvInqNo(); if(!q.subjEdited) q.subj=_pvqSubject(); if(!q.bodyEdited) q.body=_pvqBodyText(); }
  function _pvqRender(){ var q=window._pvq; if(!q) return; _pvqRefresh();
    var brands=_pvBrandList(); var bk=_pvBk(q.brand); var inList=brands.some(function(b){ return _pvBk(b)===bk; });
    var cs=_pvContacts(q.brand); var toL=(q.to||[]).map(function(e){ return e.toLowerCase(); });
    var bv=_pvBrandVendors(q.brand);
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">매입처 문의 메일 <span style="font-size:12px;font-weight:500;color:#6b7280;margin-left:6px">'+esc(q.no)+(q.quoteNo?' · 견적 '+esc(q.quoteNo):'')+'</span></span><button class="btn" onclick="document.getElementById(\'pvInqOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:14px 20px;display:flex;flex-direction:column;gap:11px">';
    // 1) 품목
    h+='<div><div style="'+_MLL+'">문의 품목 <span style="font-weight:400;color:#9ca3af">— 체크된 줄만 보냅니다 · 수량은 고칠 수 있습니다</span></div><table class="pvq-tbl"><thead><tr><th style="width:28px"></th><th>품번</th><th>품명</th><th style="width:70px">수량</th><th style="width:60px">브랜드</th><th style="width:28px"></th></tr></thead><tbody>';
    q.items.forEach(function(it,i){ var g=_pvGuessBrand(it.spec); h+='<tr><td><input type="checkbox" '+(it.on?'checked':'')+' onchange="pvqItem('+i+',\'on\',this.checked)"></td><td><input value="'+esc(it.spec)+'" placeholder="품번" onchange="pvqItem('+i+',\'spec\',this.value)"></td><td><input value="'+esc(it.name||'')+'" placeholder="품명(선택)" onchange="pvqItem('+i+',\'name\',this.value)"></td><td><input type="number" min="1" value="'+(Number(it.qty)||1)+'" onchange="pvqItem('+i+',\'qty\',this.value)" style="text-align:right"></td><td style="font-size:11px;color:'+(g?'#1B3A6B':'#9ca3af')+'">'+esc(g||'-')+'</td><td><a onclick="pvqItemDel('+i+')" style="color:#cbd5e1;cursor:pointer" title="줄 빼기">✕</a></td></tr>'; });
    h+='</tbody></table><a onclick="pvqItemAdd()" style="font-size:11.5px;color:#1B3A6B;cursor:pointer;text-decoration:underline">+ 품번 줄 추가</a></div>';
    // 2) 브랜드 · 담당자 칩
    h+='<div><div style="'+_MLL+'">브랜드(매입처) <span style="font-weight:400;color:#9ca3af">— 품번으로 추천한 값입니다. 틀리면 골라 주세요</span></div><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">'
      +'<select id="pvqBrand" onchange="pvqBrand(this.value)" style="'+_MLI+';width:auto;min-width:160px"><option value="">(브랜드 선택)</option>'+brands.map(function(b){ return '<option value="'+esc(b)+'"'+(_pvBk(b)===bk?' selected':'')+'>'+esc(b)+'</option>'; }).join('')+(q.brand&&!inList?'<option value="'+esc(q.brand)+'" selected>'+esc(q.brand)+' (매입처 미등록)</option>':'')+'</select>'
      +(q.guess?'<span style="font-size:11.5px;color:#6b7280">품번 추천: <b>'+esc(q.guess)+'</b></span>':'')
      +(bv.length?'<a onclick="openPurchaseModal(\''+esc(bv[0].id)+'\')" style="font-size:11.5px;color:#1B3A6B;cursor:pointer;text-decoration:underline">담당자 등록/수정</a>':(q.brand?'<a onclick="pvqNewVendor()" style="font-size:11.5px;color:#b45309;cursor:pointer;text-decoration:underline">이 브랜드를 매입처에 등록</a>':''))
      +'</div>';
    h+='<div class="ml-book-h" style="margin-top:8px">대리점 담당자 <span>— 눌러서 받는 사람에 넣기/빼기</span></div><div class="ml-book">';
    if(!cs.length) h+='<span class="ml-book-empty">'+(q.brand?('"'+esc(q.brand)+'" 매입처에 메일 주소가 있는 담당자가 없습니다. [담당자 등록/수정] 에서 메일을 넣어 두면 다음부터 골라 쓸 수 있습니다.'):'브랜드를 고르면 그 대리점 담당자가 여기에 나옵니다.')+'</span>';
    var lastV=''; cs.forEach(function(c,i){ var on=toL.indexOf(c.email.toLowerCase())>=0; if(c.vname!==lastV){ h+=(lastV?'<span style="flex-basis:100%;height:0"></span>':'')+'<span style="font-size:11px;font-weight:700;color:#14305c;align-self:center">'+esc(c.vname)+'</span>'; lastV=c.vname; }
      h+='<span class="ml-chip'+(on?' on':'')+'" onclick="pvqChip('+i+')" title="'+esc(c.email)+(c.phone?' · '+esc(c.phone):'')+'">'+(on?'✓ ':'')+(c.name?('<b>'+esc(c.name)+'</b> '):'')+(c.role?('<i>'+esc(c.role)+'</i> '):'')+esc(c.email)+'</span>'; });
    h+='</div></div>';
    // 3) 받는 사람 / 참조 / 회신
    h+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div><div style="'+_MLL+'">받는 사람 <span style="font-weight:400;color:#9ca3af">— 여러 명은 쉼표</span></div><input id="pvqTo" value="'+esc((q.to||[]).join(', '))+'" placeholder="대리점 담당자 메일" style="'+_MLI+'" onchange="pvqTo(this.value)"></div>'
      +'<div><div style="'+_MLL+'">참조(CC)</div><input id="pvqCc" value="'+esc(q.cc||'')+'" placeholder="본인 메일 등" style="'+_MLI+'" onchange="window._pvq.cc=this.value"></div></div>';
    h+='<div><div style="'+_MLL+'">회신 받을 내 메일 (Reply-To) <span style="font-weight:400;color:#9ca3af">— 대리점이 답장을 누르면 이 주소로 옵니다 · 한 번 적으면 기억합니다</span></div><input id="pvqMy" value="'+esc(q.my||'')+'" placeholder="이름@chjk.co.kr" style="'+_MLI+'" onchange="pvqMy(this.value)"></div>';
    // 4) 문의 종류 · 희망 납기 · 추가 요청
    h+='<div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap;font-size:12.5px;color:#374151"><span style="'+_MLL+';margin:0">문의 종류</span>'
      +['quote','lead','stock','alt'].map(function(k){ var lab={quote:'견적',lead:'납기',stock:'재고',alt:'대체품'}[k]; return '<label style="display:flex;align-items:center;gap:4px;cursor:pointer"><input type="checkbox" '+(q.kinds[k]?'checked':'')+' onchange="pvqKind(\''+k+'\',this.checked)">'+lab+'</label>'; }).join('')
      +'<span style="margin-left:auto;display:flex;align-items:center;gap:6px"><span style="'+_MLL+';margin:0">희망 납기</span><input id="pvqDue" value="'+esc(q.due||'')+'" placeholder="예: 11/20 까지" style="'+_MLI+';width:140px" onchange="window._pvq.due=this.value; pvqRegen()"></span></div>';
    h+='<div><div style="'+_MLL+'">추가 요청 <span style="font-weight:400;color:#9ca3af">— 본문에 그대로 들어갑니다 (선택)</span></div><input id="pvqNote" value="'+esc(q.note||'')+'" placeholder="예: 대체 가능한 형번이 있으면 함께 알려 주세요" style="'+_MLI+'" onchange="window._pvq.note=this.value; pvqRegen()"></div>';
    // 5) 제목 · 본문
    h+='<div><div style="'+_MLL+'">제목</div><input id="pvqSubj" value="'+esc(q.subj)+'" style="'+_MLI+'" oninput="window._pvq.subj=this.value; window._pvq.subjEdited=true"></div>';
    h+='<div><div style="'+_MLL+';display:flex;align-items:center">본문 <span style="font-weight:400;color:#9ca3af;margin-left:6px">— 고쳐도 됩니다 · 품번 줄은 메일에서 표로 들어갑니다</span><a onclick="window._pvq.subjEdited=false; window._pvq.bodyEdited=false; pvqRegen(true)" style="margin-left:auto;font-weight:500;color:#1B3A6B;text-decoration:underline;cursor:pointer;font-size:11px">자동 문구로 되돌리기</a></div><textarea id="pvqBody" style="'+_MLI+';min-height:230px;resize:vertical;line-height:1.55" oninput="window._pvq.body=this.value; window._pvq.bodyEdited=true">'+esc(q.body)+'</textarea></div>';
    h+='<div style="display:flex;align-items:center;gap:10px;padding-top:4px;border-top:1px solid #eef1f4"><span id="pvqSt" style="font-size:12px;color:#6b7280;flex:1"></span><button class="btn" onclick="pvInqBox()" style="padding:7px 12px">문의함</button><button id="pvqSend" class="btn" onclick="pvInqSend()" style="padding:7px 18px;background:#1B3A6B;color:#fff;border-color:#1B3A6B;font-weight:700">문의 보내기</button></div>';
    h+='</div>';
    _mailOverlay('pvInqOverlay', h, 820);
  }
  window.pvqItem=function(i,k,v){ var q=window._pvq; if(!q||!q.items[i]) return; if(k==='qty') v=Math.max(1,Number(v)||1); if(k==='spec') v=String(v||'').trim(); q.items[i][k]=v; if(k==='spec'&&!q.brand){ var g=_pvGuessBrand(v); if(g){ q.guess=g; q.brand=_pvResolveBrand(g); } } _pvqRender(); };
  window.pvqItemAdd=function(){ var q=window._pvq; if(!q) return; q.items.push({ spec:'', name:'', qty:1, on:true }); _pvqRender(); setTimeout(function(){ var ins=document.querySelectorAll('#pvInqOverlay .pvq-tbl tbody tr:last-child input'); if(ins[1]) ins[1].focus(); },30); };
  window.pvqItemDel=function(i){ var q=window._pvq; if(!q) return; q.items.splice(i,1); if(!q.items.length) q.items.push({ spec:'', name:'', qty:1, on:true }); _pvqRender(); };
  window.pvqBrand=function(b){ var q=window._pvq; if(!q) return; q.brand=String(b||'').trim(); q.to=[]; var bv=_pvBrandVendors(q.brand); if(bv.length===1){ (bv[0].contacts||[]).forEach(function(c){ if(c&&c.email&&_ML_RE.test(c.email)) q.to.push(c.email); }); } _pvqRender(); };
  window.pvqChip=function(i){ var q=window._pvq; if(!q) return; var c=_pvContacts(q.brand)[i]; if(!c) return; var k=c.email.toLowerCase(); var idx=q.to.findIndex(function(a){ return a.toLowerCase()===k; }); if(idx>=0) q.to.splice(idx,1); else q.to.push(c.email); _pvqRender(); };
  window.pvqTo=function(v){ var q=window._pvq; if(!q) return; q.to=_mlSplit(v); _pvqRender(); };
  window.pvqMy=function(v){ var q=window._pvq; if(!q) return; q.my=String(v||'').trim(); var cc=_mlSplit(q.cc); if(q.my&&!cc.some(function(a){ return a.toLowerCase()===q.my.toLowerCase(); })) cc.push(q.my); q.cc=cc.join(', '); _pvqRender(); };
  window.pvqKind=function(k,on){ var q=window._pvq; if(!q) return; q.kinds[k]=!!on; _pvqRender(); };
  window.pvqRegen=function(force){ var q=window._pvq; if(!q) return; if(force){ q.subjEdited=false; q.bodyEdited=false; } _pvqRender(); };
  window.pvqNewVendor=function(){ var q=window._pvq; if(!q||!q.brand) return; openPurchaseModal(); setTimeout(function(){ var b=document.getElementById('pvBrand'); if(b){ b.value=q.brand; } },50); };
  window.pvInqSend=async function(){ var q=window._pvq; if(!q) return; var st=document.getElementById('pvqSt'), btn=document.getElementById('pvqSend');
    var act=_pvqActive(); if(!act.length){ st.innerHTML='<span style="color:#dc2626">보낼 품번이 없습니다 (체크된 줄).</span>'; return; }
    var to=_mlSplit((document.getElementById('pvqTo')||{}).value); q.to=to; if(!to.length){ st.innerHTML='<span style="color:#dc2626">받는 사람(대리점 담당자 메일)을 넣어 주세요.</span>'; return; }
    var bad=to.concat(_mlSplit(q.cc)).find(function(a){ return !_ML_RE.test(a); }); if(bad){ st.innerHTML='<span style="color:#dc2626">주소 형식이 이상합니다: '+esc(bad)+'</span>'; return; }
    q.my=String((document.getElementById('pvqMy')||{}).value||q.my||'').trim(); if(q.my&&!_ML_RE.test(q.my)){ st.innerHTML='<span style="color:#dc2626">회신 받을 내 메일 주소 형식이 이상합니다.</span>'; return; }
    var cfg=await _mailLoadCfg(true); if(cfg._loadErr){ st.innerHTML='<span style="color:#dc2626">메일 설정을 불러오지 못했습니다. 잠시 후 다시 눌러 주세요.</span>'; return; }
    if(!cfg.url||!cfg.key){ st.innerHTML='<span style="color:#dc2626">메일 발송 설정이 아직 없습니다 (관리자 · 견적 다운로드 > 메일 설정).</span>'; return; }
    var m=_pvMe(); var SUP=_qSupplierInfo(m.branch); var subj=(document.getElementById('pvqSubj')||{}).value||q.subj; var body=(document.getElementById('pvqBody')||{}).value||q.body; var cc=_mlSplit(q.cc).filter(function(a){ return to.map(function(t){ return t.toLowerCase(); }).indexOf(a.toLowerCase())<0; }).join(', ');
    btn.disabled=true; btn.textContent='보내는 중…'; st.textContent='발송 중…';
    try{
      var r=await fetch(_mailUrl(cfg,'/send'), {method:'POST', headers:{'Content-Type':'application/json','X-Mail-Key':cfg.key}, body:JSON.stringify({account:_mailAcctOf(m.branch), to:to.join(', '), cc:cc, replyTo:q.my||'', subject:subj, text:body, html:_pvqBodyHtml(body), fromName:SUP.corp+' '+m.staff, attachments:[]})});
      var j=null; try{ j=await r.json(); }catch(_j){}
      if(!r.ok||!j||!j.ok) throw new Error((j&&j.error)||('HTTP '+r.status));
      var cs=_pvContacts(q.brand); var vnames=[]; to.forEach(function(e){ var c=cs.find(function(x){ return x.email.toLowerCase()===e.toLowerCase(); }); if(c&&c.vname&&vnames.indexOf(c.vname)<0) vnames.push(c.vname); });
      if(typeof pvInq==='undefined') window.pvInq=[];
      pvInq.push({ id:uid(), no:q.no, at:Date.now(), by:m.staff, brand:q.brand, vendors:vnames, to:to, cc:cc, replyTo:q.my||'', subject:subj, body:body, items:act.map(function(it){ return { spec:it.spec, name:it.name||'', qty:Number(it.qty)||1 }; }), kinds:_pvqKindLabel(q.kinds), due:q.due||'', quoteNo:q.quoteNo||'', vname:q.vname||'', status:'wait' });
      _pvSaveMyEmail(q.my); saveAll();
      document.getElementById('pvInqOverlay').style.display='none';
      showInfoModal('문의 발송 완료', (q.brand?esc(q.brand)+' ':'')+'품번 '+act.length+'건 문의를 보냈습니다.\n\n받는 사람: '+esc(to.join(', '))+(cc?('\n참조: '+esc(cc)):'')+(q.my?('\n회신 받을 곳: '+esc(q.my)):'')+'\n\n문의번호 '+esc(q.no)+' — 매입처 > 문의함에서 회신 여부를 적어 두면 됩니다.');
      try{ _mtToast('문의함에 '+q.no+' 기록'); }catch(_e){}
      try{ if(document.getElementById('pagePurchase')&&document.getElementById('pagePurchase').classList.contains('active')) renderPurchasePage(); }catch(_e2){}
    }catch(e){ st.innerHTML='<span style="color:#dc2626">발송 실패: '+esc(e&&e.message||String(e))+'</span>'; }
    finally{ btn.disabled=false; btn.textContent='문의 보내기'; }
  };
  // ─── 문의함 ───
  function _pvInqWait(){ return (typeof pvInq!=='undefined'?pvInq:[]).filter(function(q){ return q&&q.status==='wait'; }).length; }
  window._pvInqFilter='wait';
  window.pvInqBox=function(f){ if(f) window._pvInqFilter=f; var all=(typeof pvInq!=='undefined'?pvInq:[]).slice().sort(function(a,b){ return (b.at||0)-(a.at||0); }); var fl=window._pvInqFilter; var list=all.filter(function(q){ return fl==='all'||q.status===fl; });
    var tab=function(k,l){ return '<button class="btn" onclick="pvInqBox(\''+k+'\')" style="padding:4px 10px;'+(fl===k?'background:#1B3A6B;color:#fff;border-color:#1B3A6B':'')+'">'+l+'</button>'; };
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center;gap:8px"><span style="font-size:16px;font-weight:700;color:#1B3A6B">매입처 문의함 <span style="font-size:12px;font-weight:500;color:#6b7280;margin-left:6px">회신 대기 '+_pvInqWait()+'건</span></span><span style="display:flex;gap:4px;margin-left:auto">'+tab('wait','대기')+tab('reply','회신 받음')+tab('done','완료')+tab('all','전체')+'</span><button class="btn" onclick="document.getElementById(\'pvInqBoxOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div><div style="padding:12px 20px;display:flex;flex-direction:column;gap:8px">';
    if(!list.length) h+='<div style="padding:30px;text-align:center;color:#9ca3af;font-size:13px">'+(all.length?'이 상태의 문의가 없습니다.':'아직 보낸 문의가 없습니다. 견적 다운로드 > [매입처에 문의 메일] 또는 매입처 카드의 ✉ 에서 보냅니다.')+'</div>';
    list.forEach(function(q){ var d=new Date(q.at||0); var ds=d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2)+' '+('0'+d.getHours()).slice(-2)+':'+('0'+d.getMinutes()).slice(-2); var age=Math.floor((Date.now()-(q.at||0))/86400000);
      var pill={wait:'<span style="background:#fef3c7;color:#b45309">회신 대기'+(age>=3?' · '+age+'일':'')+'</span>', reply:'<span style="background:#dcfce7;color:#15803d">회신 받음</span>', done:'<span style="background:#e5e7eb;color:#374151">완료</span>'}[q.status]||'';
      h+='<div class="pvi-row"><div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><b style="color:#1B3A6B">'+esc(q.no||'')+'</b><span style="font-weight:700">'+esc(q.brand||'')+'</span><span style="color:#6b7280">'+esc((q.vendors||[]).join(', '))+'</span><span class="pvi-pill">'+pill+'</span><span style="margin-left:auto;font-size:11.5px;color:#9ca3af">'+esc(ds)+' · '+esc(q.by||'')+(q.quoteNo?' · 견적 '+esc(q.quoteNo):'')+'</span></div>'
        +'<div style="font-size:12px;color:#374151;margin-top:4px">'+(q.items||[]).map(function(it){ return '<span style="display:inline-block;margin:2px 6px 2px 0;padding:1px 7px;border:1px solid #d6e0ec;border-radius:10px">'+esc(it.spec)+' ×'+(Number(it.qty)||1)+'</span>'; }).join('')+'</div>'
        +'<div style="font-size:11.5px;color:#6b7280;margin-top:3px">받는 사람 '+esc((q.to||[]).join(', '))+(q.replyTo?' · 회신 → '+esc(q.replyTo):'')+(q.due?' · 희망 납기 '+esc(q.due):'')+(q.memo?' · <i>'+esc(q.memo)+'</i>':'')+'</div>'
        +'<div style="display:flex;gap:6px;margin-top:6px;flex-wrap:wrap">'+(q.status!=='reply'?'<button class="btn" onclick="pvInqSet(\''+q.id+'\',\'reply\')" style="padding:3px 9px;font-size:11.5px">회신 받음</button>':'')+(q.status!=='done'?'<button class="btn" onclick="pvInqSet(\''+q.id+'\',\'done\')" style="padding:3px 9px;font-size:11.5px">완료</button>':'')+(q.status!=='wait'?'<button class="btn" onclick="pvInqSet(\''+q.id+'\',\'wait\')" style="padding:3px 9px;font-size:11.5px">다시 대기</button>':'')+'<button class="btn" onclick="pvInqMemo(\''+q.id+'\')" style="padding:3px 9px;font-size:11.5px">메모</button><button class="btn" onclick="pvInqAgain(\''+q.id+'\')" style="padding:3px 9px;font-size:11.5px">같은 내용으로 다시 문의</button><button class="btn" onclick="pvInqView(\''+q.id+'\')" style="padding:3px 9px;font-size:11.5px">보낸 내용</button>'+(_isAdmin()?'<button class="btn" onclick="pvInqDel(\''+q.id+'\')" style="padding:3px 9px;font-size:11.5px;color:#dc2626;margin-left:auto">지우기</button>':'')+'</div></div>'; });
    h+='</div>'; _mailOverlay('pvInqBoxOverlay', h, 860);
  }
  function _pvInqFind(id){ return (typeof pvInq!=='undefined'?pvInq:[]).find(function(q){ return q&&q.id===id; }); }
  window.pvInqSet=function(id,st){ if(typeof _guardW==='function' && !_guardW()) return; var q=_pvInqFind(id); if(!q) return; q.status=st; q.stAt=Date.now(); q.stBy=_pvMe().staff; saveAll(); pvInqBox(); try{ renderPurchasePage(); }catch(_e){} };
  window.pvInqMemo=function(id){ var q=_pvInqFind(id); if(!q) return; showPromptModal('문의 메모', '회신 내용·단가·납기 등을 적어 두세요', q.memo||'', function(v){ q.memo=String(v||'').trim(); saveAll(); pvInqBox(); }, '저장'); };
  window.pvInqView=function(id){ var q=_pvInqFind(id); if(!q) return; showInfoModal('보낸 내용 · '+(q.no||''), '제목: '+esc(q.subject||'')+'\n\n'+esc(q.body||'')); };
  window.pvInqAgain=function(id){ var q=_pvInqFind(id); if(!q) return; document.getElementById('pvInqBoxOverlay').style.display='none'; pvInqOpen({ brand:q.brand, items:q.items }); window._pvq.to=(q.to||[]).slice(); window._pvq.note=q.memo?'':window._pvq.note; _pvqRender(); };
  window.pvInqDel=function(id){ if(!_isAdmin()) return; showConfirmModal('문의 기록 지우기', '이 문의 기록을 지울까요? (메일은 이미 보낸 상태 그대로입니다)', function(){ pvInq=pvInq.filter(function(q){ return q.id!==id; }); saveAll(); pvInqBox(); }, '지우기', '#dc2626'); };
  // 매입처 툴바 문의함 버튼 뱃지
  function _pvInqBadge(){ var b=document.getElementById('pvInqBoxBtn'); if(!b) return; var n=_pvInqWait(); var bd=b.querySelector('.pvi-badge'); if(!bd){ bd=document.createElement('span'); bd.className='pvi-badge'; b.appendChild(bd); } bd.textContent=n?String(n):''; bd.style.display=n?'inline-block':'none'; }
  // 엑셀 업로드 → 같은 브랜드·대리점이 있으면 합치고, 담당자는 메일 주소로 중복 제거
  function _pvMergeEntries(entries){ var added=0, merged=0, nc=0;
    entries.forEach(function(e){ var bk=_pvBk(e.brand), dk=_pvBk(e.distributor);
      var ex=_pvVendors().find(function(v){ return _pvBk(v.brand)===bk && _pvBk(v.distributor)===dk; });
      var cs=(e.contacts||[]).map(function(c){ return { role:String(c.role||'').trim(), name:String(c.name||'').trim(), phone:String(c.phone||'').trim(), email:String(c.email||'').trim() }; }).filter(function(c){ return c.role||c.name||c.phone||c.email; });
      if(e.email && !cs.some(function(c){ return c.email.toLowerCase()===String(e.email).toLowerCase(); })) cs.push({ role:'', name:'', phone:'', email:String(e.email).trim() });
      if(ex){ if(!Array.isArray(ex.contacts)) ex.contacts=[];
        cs.forEach(function(c){ var hit=ex.contacts.find(function(o){ return o && ((c.email && String(o.email||'').toLowerCase()===c.email.toLowerCase()) || (!c.email && c.name && String(o.name||'').trim()===c.name)); });
          if(hit){ if(!hit.name&&c.name) hit.name=c.name; if(!hit.role&&c.role) hit.role=c.role; if(!hit.phone&&c.phone) hit.phone=c.phone; if(!hit.email&&c.email) hit.email=c.email; }
          else { ex.contacts.push(c); nc++; } });
        merged++;
      } else { purchaseVendors.push({ id:uid(), brand:e.brand, distributor:e.distributor, contacts:cs, memo:'', createdAt:Date.now() }); added++; nc+=cs.length; }
    });
    return { added:added, merged:merged, contacts:nc };
  }
  (function(){ var st=document.createElement('style'); st.textContent='.pvq-tbl{width:100%;border-collapse:collapse;font-size:12.5px} .pvq-tbl th{font-size:11px;color:#6b7280;font-weight:600;text-align:left;padding:2px 4px;border-bottom:1px solid #e5e7eb} .pvq-tbl td{padding:2px 4px} .pvq-tbl input:not([type=checkbox]){width:100%;box-sizing:border-box;padding:5px 7px;border:1px solid #d6e0ec;border-radius:6px;font-size:12.5px;font-family:inherit} .pvi-row{border:1px solid #e5e9f0;border-radius:8px;padding:9px 12px;background:#fff} .pvi-pill span{display:inline-block;font-size:11px;font-weight:700;padding:1px 8px;border-radius:10px} .pvi-badge{display:none;margin-left:3px;min-width:16px;height:16px;line-height:16px;border-radius:8px;background:#dc2626;color:#fff;font-size:10px;font-weight:700;text-align:center;padding:0 4px} .pv-mail-btn{background:none;border:none;cursor:pointer;color:#1B3A6B;padding:0 3px;display:inline-flex;align-items:center}'; document.head.appendChild(st); })();
