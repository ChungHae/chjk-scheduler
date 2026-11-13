  // ─── r268: SMC 가격 일괄 확인 — SMC 품번일괄조회(최대 200개)에 대기 품번을 한꺼번에 넣고, 결과를 붙여넣어 E가 일치분을 한 번에 등록 ───
  var _smcBk={ text:'', res:null, useSmc:false, busy:false, msg:'' };
  var _SMC_BULK_URL='https://www.smckorea.co.kr/ppis/source/admin/mdnm_split_list.asp';
  function _smcWaitList(){ return (smcQueue||[]).filter(function(q){ return q&&(q.status||'wait')==='wait'&&q.spec; }).sort(function(a,b){ return (b.at||0)-(a.at||0); }); }
  function _smcIsPn(s){ return /^[A-Za-z0-9][A-Za-z0-9\-\/\.\s#()+]*$/.test(String(s||'').trim()) && /[0-9]/.test(s); }   // 한글 품목명 등은 SMC 품번 조회에서 뺀다
  window.smcBulkOpen=function(){ _smcBk.res=null; _smcBk.msg=''; _smcBkRender(); };
  window.smcBulkCopy=function(k){
    var L=_smcWaitList().filter(function(q){ return _smcIsPn(q.spec); }); var part=L.slice(k*200, k*200+200).map(function(q){ return String(q.spec).trim().toUpperCase(); });
    var txt=part.join('\n');
    var done=function(ok){ _smcBk.msg=ok?('<span style="color:#15803d">'+(k*200+1)+'~'+(k*200+part.length)+'번 품번 '+part.length+'개를 복사했습니다. SMC 품번일괄조회 첫 칸에 붙여넣기(Ctrl+V) → [실행하기].</span>'):'<span style="color:#dc2626">복사하지 못했습니다. 아래 칸에서 직접 복사하세요.</span>'; if(!ok) _smcBk.show=txt; _smcBkRender(); };
    try{ navigator.clipboard.writeText(txt).then(function(){ done(true); }, function(){ done(false); }); }catch(_e){ done(false); }
  };
  // 붙여넣은 SMC 결과 해석: 줄마다 대기 품번을 찾고, 그 뒤 첫 숫자를 E가로 본다. '문의'·'공급불가'·'사양' 글자는 상태로.
  function _smcBkParse(text){
    var wait=_smcWaitList(), byK={}; wait.forEach(function(q){ var k=_qNorm(q.spec); if(k&&!byK[k]) byK[k]=q; });
    var out={}, lines=String(text||'').split(/\r?\n/);
    lines.forEach(function(line){
      if(!line.trim()) return;
      var cells=line.split('\t').map(function(c){ return c.trim(); });
      if(cells.length<2) cells=line.trim().split(/\s{2,}|\s+(?=[\d,]+(?:\s|$))/);
      var ix=-1, q=null;
      for(var i=0;i<cells.length;i++){ var k=_qNorm(cells[i]); if(k&&byK[k]){ ix=i; q=byK[k]; break; } }
      if(!q) return;
      var c1=String(cells[ix+1]||'').replace(/,/g,'').trim(), e=/^\d+(\.\d+)?$/.test(c1)?Number(c1):null;   // SMC 표: 품번 바로 다음 칸이 E가
      var st=/공급불가|품번아님|red/i.test(line)?'no':(/문의|yellow/i.test(line)?'ask':'');
      out[q.id]={ q:q, smcE:(e>0?e:null), st:st };
    });
    var r={ same:[], diff:[], none:[], miss:0 };
    Object.keys(out).forEach(function(id){ var o=out[id];
      if(!o.smcE || o.st==='no') r.none.push(o);
      else if(Number(o.q.e)===o.smcE && o.st!=='ask') r.same.push(o);
      else r.diff.push(o); });
    r.miss=wait.filter(function(q){ return _smcIsPn(q.spec) && !out[q.id]; }).length;
    return r;
  }
  window.smcBulkParse=function(){ var t=document.getElementById('smcBkText'); _smcBk.text=t?t.value:''; _smcBk.res=_smcBkParse(_smcBk.text); _smcBk.msg=''; _smcBkRender(); };
  window.smcBulkUseSmc=function(v){ _smcBk.useSmc=!!v; _smcBkRender(); };
  // 여러 건을 가격표 SMC blob 에 한 번에 넣는다 (smcRegister 와 같은 규칙)
  async function _smcRegisterMany(items){
    var m=(priceMakers||[]).find(function(x){ return String(x.name||'').toUpperCase().indexOf('SMC')>=0; });
    var mid=m?m.id:('pm'+Date.now().toString(36)+'s');
    var rows=[]; if(m){ try{ delete _priceBlobCache[mid]; }catch(_e){} var eb=await _priceBlobGet(mid); if(Array.isArray(eb)) rows=eb; else throw new Error('SMC 가격표를 읽지 못했습니다'); }
    var pk=function(z){ return String(z==null?'':z).toLowerCase().replace(/\s+/g,''); };
    var idx={}; rows.forEach(function(x,i){ if(!x.qr){ var k=pk(x.spec); if(!(k in idx)) idx[k]=i; } });
    items.forEach(function(it){ var q=it.q, k=pk(q.spec), r=(k in idx)?rows[idx[k]]:null;
      if(!r){ r={ spec:q.spec, name:q.name||'', unit:'EA' }; rows.push(r); idx[k]=rows.length-1; }
      r.ega=it.e; if(q.name && !r.name) r.name=q.name; });
    await _priceBlobPut(mid, rows);
    if(m) m.count=rows.length; else priceMakers.push({ id:mid, name:'SMC', count:rows.length });
    var who=_smcWho(), now=Date.now();
    items.forEach(function(it){ var q=it.q; q.status='ok'; q.okE=it.e; q.okHp=null; q.okSm=null; q.okBy=who; q.okAt=now; q.okSrc='SMC 일괄조회'; });
    saveAll();
    try{ _ensurePriceSyncMap(true); }catch(_e){}
    try{ _qInvalidateAllIdx(); }catch(_e){}
  }
  window.smcBulkRegister=async function(){
    if(typeof _guardW==='function' && !_guardW()) return;
    var r=_smcBk.res; if(!r||_smcBk.busy) return;
    var items=r.same.map(function(o){ return {q:o.q, e:o.smcE}; });
    if(_smcBk.useSmc) items=items.concat(r.diff.filter(function(o){ return o.smcE>0 && o.st!=='ask'; }).map(function(o){ return {q:o.q, e:o.smcE}; }));
    if(!items.length) return;
    if(!_fbDbUrl){ showInfoModal('동기화 필요','팀 동기화 연결이 필요합니다.'); return; }
    if(!confirm('SMC 가격표에 '+items.length+'건을 등록합니다 (E가'+(_smcBk.useSmc?' — 다른 것은 SMC 값으로':' 일치분만')+').\n진행할까요?')) return;
    _smcBk.busy=true; _smcBk.msg='등록 중…'; _smcBkRender();
    try{ await _smcRegisterMany(items); _smcBk.msg='<span style="color:#15803d;font-weight:700">'+items.length+'건 등록했습니다.</span>'; _smcBk.res=_smcBkParse(_smcBk.text); }
    catch(e){ _smcBk.msg='<span style="color:#dc2626">등록 실패: '+esc(e.message||String(e))+'</span>'; }
    _smcBk.busy=false; _smcBkRender(); try{ renderSmcPage(); }catch(_e){}
  };
  window.smcBulkSkipNone=function(){
    var r=_smcBk.res; if(!r) return; var L=r.none.filter(function(o){ return o.st==='no' || !o.smcE; });
    if(!L.length||!confirm('SMC 에 없는 품번 '+L.length+'건을 [제외]로 옮깁니다. 진행할까요?')) return;
    var who=_smcWho(), now=Date.now(); L.forEach(function(o){ o.q.status='skip'; o.q.okBy=who; o.q.okAt=now; o.q.okSrc='SMC 일괄조회: 없음'; });
    saveAll(); _smcBk.res=_smcBkParse(_smcBk.text); _smcBk.msg='<span style="color:#15803d">'+L.length+'건을 제외로 옮겼습니다.</span>'; _smcBkRender(); try{ renderSmcPage(); }catch(_e){}
  };
  function _smcBkRender(){
    var t0=document.getElementById('smcBkText'); if(t0) _smcBk.text=t0.value;
    var L=_smcWaitList(), P=L.filter(function(q){ return _smcIsPn(q.spec); }), n=Math.ceil(P.length/200);
    var btns=''; for(var k=0;k<n;k++) btns+='<button class="btn" onclick="smcBulkCopy('+k+')" style="margin:0 6px 6px 0">'+(k*200+1)+'~'+Math.min(P.length,k*200+200)+'번 복사</button>';
    var r=_smcBk.res, res='';
    if(r){
      var tb=function(arr, showSmc){ return '<div style="max-height:180px;overflow:auto;border:1px solid #eef2f7;border-radius:8px"><table style="width:100%;border-collapse:collapse;font-size:12px">'+arr.slice(0,300).map(function(o){ return '<tr style="border-top:1px solid #f1f5f9"><td style="padding:4px 8px;font-weight:700;color:#14305c">'+esc(o.q.spec)+'</td><td style="padding:4px 8px;text-align:right;color:#6b7280">우리 '+_qFmt(o.q.e)+'</td>'+(showSmc?'<td style="padding:4px 8px;text-align:right">SMC '+(o.smcE?_qFmt(o.smcE):'-')+(o.st==='ask'?' <span style="color:#b45309">문의요망</span>':'')+'</td>':'')+'<td style="padding:4px 8px;color:#6b7280">'+esc(o.q.vname||'')+'</td></tr>'; }).join('')+'</table></div>'; };
      res='<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:12px">'
        +'<div><div style="font-weight:700;color:#15803d;margin-bottom:4px">E가 일치 '+r.same.length+'건</div>'+tb(r.same,false)+'</div>'
        +'<div><div style="font-weight:700;color:#b45309;margin-bottom:4px">E가 다름·문의요망 '+r.diff.length+'건</div>'+tb(r.diff,true)+'</div>'
        +'<div><div style="font-weight:700;color:#dc2626;margin-bottom:4px">SMC 가격 없음·품번 아님 '+r.none.length+'건</div>'+tb(r.none,true)+'</div></div>'
        +(r.miss?'<div style="font-size:11.5px;color:#6b7280;margin-top:6px">붙여넣은 결과에 없는 대기 품번 '+r.miss+'건 (다음 200개 묶음으로 조회하세요)</div>':'')
        +'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px">'
        +'<label style="font-size:12.5px;display:flex;gap:5px;align-items:center"><input type="checkbox" '+(_smcBk.useSmc?'checked':'')+' onchange="smcBulkUseSmc(this.checked)"> E가가 다른 것도 SMC 값으로 등록 (문의요망 제외)</label>'
        +'<span style="flex:1"></span>'
        +(r.none.length?'<button class="btn" onclick="smcBulkSkipNone()">없는 품번 '+r.none.length+'건 제외로</button>':'')
        +'<button class="btn btn-primary" onclick="smcBulkRegister()" '+(_smcBk.busy?'disabled':'')+'>'+(r.same.length+(_smcBk.useSmc?r.diff.filter(function(o){ return o.smcE>0&&o.st!=='ask'; }).length:0))+'건 일괄 등록</button></div>';
    }
    _mailOverlay('smcBkOverlay',
      '<div style="padding:15px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">SMC 가격 일괄 확인 <span style="font-size:12px;font-weight:400;color:#6b7280">대기 '+L.length+'건 · SMC 품번 '+P.length+'건</span></span><button class="btn" onclick="document.getElementById(\'smcBkOverlay\').style.display=\'none\'">닫기</button></div>'
      +'<div style="padding:16px 20px;font-size:12.5px;color:#374151;line-height:1.7">'
      +'<div style="font-weight:700;color:#14305c;margin-bottom:4px">① 대기 품번 복사 <span style="font-weight:400;color:#6b7280">— 200개씩 (SMC 품번일괄조회 한 번에 200개)</span></div>'
      +'<div>'+(btns||'<span style="color:#9ca3af">대기 중인 SMC 품번이 없습니다.</span>')+'</div>'
      +(_smcBk.show?'<textarea readonly style="width:100%;height:70px;font-size:11px;box-sizing:border-box">'+esc(_smcBk.show)+'</textarea>':'')
      +'<div style="font-weight:700;color:#14305c;margin:10px 0 4px">② SMC 에서 조회</div>'
      +'<div>SMC UbiCom → <b>제품정보</b> → 위쪽 빨간 <b>[품번일괄조회]</b> (또는 <a href="'+_SMC_BULK_URL+'" target="_blank" rel="noopener">바로 열기</a> — UbiCom 로그인 후) → 첫 칸에 <b>Ctrl+V</b> → <b>[실행하기]</b></div>'
      +'<div style="font-weight:700;color:#14305c;margin:10px 0 4px">③ 결과 붙여넣기</div>'
      +'<div>조회 결과 표를 첫 줄부터 마지막 줄까지 드래그해 <b>Ctrl+C</b> → 아래 칸에 <b>Ctrl+V</b> → [결과 확인]</div>'
      +'<textarea id="smcBkText" placeholder="SMC 조회 결과를 여기에 붙여넣기" style="width:100%;height:110px;box-sizing:border-box;padding:8px;border:1.5px solid #d6e0ec;border-radius:8px;font-size:12px;font-family:inherit;margin-top:4px">'+esc(_smcBk.text||'')+'</textarea>'
      +'<div style="display:flex;gap:8px;margin-top:6px;align-items:center"><button class="btn" onclick="smcBulkParse()">결과 확인</button><span id="smcBkMsg">'+(_smcBk.msg||'')+'</span></div>'
      +res+'</div>', 980);
  }
