
  // ─── r260: 다른 거래처 원장에서 가져온 줄은 판매가·예상납기를 비운다 (이 거래처 이력 없음 → 일반품 판매가 없음이 정상) ───
  function _qOwnRow(r){ return !!r && (typeof _qRows!=='undefined') && (_qRows||[]).indexOf(r)>=0; }
  // ─── r260: 마진율 / DC율 일괄 적용 ───
  window.qBulkRateOpen=function(){
    if(typeof _guardW==='function' && !_guardW()) return;
    var rows=(_qCart||[]).filter(function(c){ return c && String(c.spec||'').trim(); });
    if(!rows.length){ showInfoModal('일괄 적용','견적 목록에 품번이 없습니다.'); return; }
    var nSmall=rows.filter(_qbIsSmall).length;
    var st=window._qbState||{mode:'margin', rate:'', scope:'empty', small:'exclude'};
    var R=function(name,val,label,cur){ return '<label style="display:flex;align-items:center;gap:5px;cursor:pointer"><input type="radio" name="'+name+'" value="'+val+'"'+(cur===val?' checked':'')+' onchange="_qbPrev()">'+label+'</label>'; };
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">마진율 · DC율 일괄 적용</span><button class="btn" onclick="document.getElementById(\'qBulkOverlay\').style.display=\'none\'" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:16px 20px;display:flex;flex-direction:column;gap:14px;font-size:13px;color:#374151">'
      +'<div><div style="'+_MLL+'">무엇을</div><div style="display:flex;gap:18px;flex-wrap:wrap">'+R('qbMode','margin','<b>마진율</b> → 판매가 = 구매가 ÷ (1 − 마진)',st.mode)+R('qbMode','dc','<b>DC율</b> → 구매가 = E가 × (1 − DC)',st.mode)+'</div></div>'
      +'<div style="display:flex;align-items:center;gap:8px"><div style="'+_MLL+';margin:0">비율</div><input id="qbRate" value="'+esc(st.rate)+'" inputmode="decimal" placeholder="예: 15" style="'+_MLI+';width:110px;text-align:right" oninput="_qbPrev()" onkeydown="if(event.key===\'Enter\'){ event.preventDefault(); qBulkRateApply(); }"><span style="font-weight:700">%</span>'
      +'<span style="display:flex;gap:4px;margin-left:8px">'+[5,10,15,20,25,30].map(function(p){ return '<button type="button" class="btn" onclick="document.getElementById(\'qbRate\').value=\''+p+'\'; _qbPrev()" style="padding:3px 8px;font-size:11.5px">'+p+'</button>'; }).join('')+'</span></div>'
      +'<div><div style="'+_MLL+'">어느 줄에</div><div style="display:flex;gap:18px;flex-wrap:wrap">'+R('qbScope','empty','비어 있는 칸만 채우기',st.scope)+R('qbScope','all','전체 줄 덮어쓰기',st.scope)+'</div></div>'
      +'<div><div style="'+_MLL+'">소물류 <span style="font-weight:400;color:#9ca3af">— 소물가가 있는 줄 '+nSmall+'건</span></div><div style="display:flex;gap:18px;flex-wrap:wrap">'+R('qbSmall','exclude','소물류 제외',st.small)+R('qbSmall','include','소물류 포함',st.small)+'</div></div>'
      +'<div id="qbPrev" style="background:#f4f8fe;border:1px solid #d6e0ec;border-radius:8px;padding:10px 12px;font-size:12.5px;line-height:1.6"></div>'
      +'<div style="display:flex;justify-content:flex-end;gap:8px;border-top:1px solid #eef1f4;padding-top:10px"><button class="btn" onclick="document.getElementById(\'qBulkOverlay\').style.display=\'none\'" style="padding:7px 14px">취소</button><button id="qbApply" class="btn" onclick="qBulkRateApply()" style="padding:7px 18px;background:#1B3A6B;color:#fff;border-color:#1B3A6B;font-weight:700">적용</button></div>'
      +'</div>';
    _mailOverlay('qBulkOverlay', h, 560);
    _qbPrev(); setTimeout(function(){ var r=document.getElementById('qbRate'); if(r){ r.focus(); r.select(); } },30);
  };
  function _qbIsSmall(c){ return c && c.small!=null && c.small!=='' && !isNaN(Number(c.small)); }
  function _qbRead(){ var g=function(n){ var e=document.querySelector('#qBulkOverlay input[name="'+n+'"]:checked'); return e?e.value:''; };
    var raw=String((document.getElementById('qbRate')||{}).value||'').replace(/[^\d.]/g,'');
    return { mode:g('qbMode')||'margin', rate:raw, scope:g('qbScope')||'empty', small:g('qbSmall')||'exclude' }; }
  function _qbPlan(st){   // 줄마다 바꿀지 / 왜 건너뛰는지
    var rate=Number(st.rate)/100; var out={ apply:[], skip:{small:0, disc:0, nobase:0, filled:0, locked:0} };
    (_qCart||[]).forEach(function(c,i){
      if(!c || !String(c.spec||'').trim()) return;
      if(c.disc && String(c.disc).trim()){ out.skip.disc++; return; }
      if(st.small==='exclude' && _qbIsSmall(c)){ out.skip.small++; return; }
      if(st.mode==='margin'){
        if(c.buy==null||c.buy===''){ out.skip.nobase++; return; }
        if(st.scope==='empty' && c.sell!=null && c.sell!==''){ out.skip.filled++; return; }
        out.apply.push({i:i, val:_qCalcSell(c.buy, rate)});
      } else {
        if(c.pl){ out.skip.locked++; return; }   // 가격표 확판/소물 잠금 줄은 구매가를 바꾸지 않는다
        if(c.e==null||c.e===''){ out.skip.nobase++; return; }
        if(st.scope==='empty' && c.buy!=null && c.buy!==''){ out.skip.filled++; return; }
        out.apply.push({i:i, val:_qCalcBuy(c.e, rate)});
      }
    });
    return out;
  }
  window._qbPrev=function(){ var el=document.getElementById('qbPrev'); if(!el) return; var st=_qbRead(); window._qbState=st;
    var r=Number(st.rate); var btn=document.getElementById('qbApply');
    if(st.rate===''||isNaN(r)){ el.innerHTML='<span style="color:#9ca3af">비율(%)을 넣으면 몇 줄에 적용되는지 미리 보여 드립니다.</span>'; if(btn) btn.disabled=true; return; }
    if(r<0 || r>=100){ el.innerHTML='<span style="color:#dc2626">0 이상 100 미만으로 넣어 주세요.</span>'; if(btn) btn.disabled=true; return; }
    var p=_qbPlan(st); var s=p.skip; var parts=[];
    if(s.filled) parts.push('이미 값 있음 '+s.filled); if(s.small) parts.push('소물류 '+s.small); if(s.nobase) parts.push((st.mode==='margin'?'구매가 없음 ':'E가 없음 ')+s.nobase); if(s.locked) parts.push('확판/소물 잠금 '+s.locked); if(s.disc) parts.push('단종/변경 '+s.disc);
    el.innerHTML='<b style="color:#14305c">'+p.apply.length+'줄</b>에 '+(st.mode==='margin'?'마진율 '+r+'% → 판매가':'DC율 '+r+'% → 구매가')+'를 넣습니다.'+(parts.length?'<br><span style="color:#6b7280">건너뜀: '+parts.join(' · ')+'</span>':'');
    if(btn) btn.disabled=!p.apply.length;
  };
  window.qBulkRateApply=function(){ var st=_qbRead(); var r=Number(st.rate); if(st.rate===''||isNaN(r)||r<0||r>=100) return;
    var p=_qbPlan(st); if(!p.apply.length) return;
    try{ _qPushUndo(); }catch(_e){}
    p.apply.forEach(function(a){ var c=_qCart[a.i]; if(!c) return; if(st.mode==='margin') c.sell=a.val; else c.buy=a.val; });
    _qCartSave(); renderQCart();
    document.getElementById('qBulkOverlay').style.display='none';
    try{ _mtToast((st.mode==='margin'?'마진율 ':'DC율 ')+r+'% 를 '+p.apply.length+'줄에 적용했습니다 (Ctrl+Z 로 되돌리기)'); }catch(_e2){}
  };
