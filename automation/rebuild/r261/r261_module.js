
  // ─── r261 ① 규격 칸에 한 품번을 붙여넣으면, 목록에 똑같은 규격이 있을 때 클릭 없이 바로 그 규격으로 채운다 ───
  function _qPasteRowIdx(el){ var m=String(el.getAttribute('oninput')||'').match(/qCartSpecInput\((\d+)/); return m?Number(m[1]):-1; }
  async function _qPasteSpecAuto(el, txt){
    var i=_qPasteRowIdx(el); if(i<0) return false;
    var s=el.selectionStart, e=el.selectionEnd, v=el.value||'';
    var nv=(s!=null&&e!=null&&!(s===0&&e===v.length)&&el.dataset.xed==='1')?(v.slice(0,s)+txt+v.slice(e)):txt;   // 편집 모드면 커서 자리에, 아니면 칸 전체를 바꿈
    nv=String(nv).trim(); el.value=nv;
    try{ if(!_qAllReady) await _qEnsureAllIdx(); }catch(_e){}
    qCartSpecInput(i, el);
    var qh=_qNormH(nv);
    var ix=(_qcsCur||[]).findIndex(function(vw){ return vw && vw.r && _qNormH(vw.r.spec)===qh; });
    if(ix>=0){ qCartSpecPick(i, ix, false); try{ _qcsHide(); }catch(_e2){} return true; }
    return false;   // 똑같은 규격이 없으면 지금처럼 목록만 보여 줌 (Enter = 입력한 그대로)
  }
  // ─── r261 ② 메일 발송·다운로드 뒤 자동 비우기 (저장된 견적만) + [다시 열기] ───
  function _qAfterOut(label){
    var id=_qLoadedId, no=_qQuoteNo;
    var saved=!!(id && (quoteSaved||[]).find(function(x){ return x.id===id; }));
    if(!saved){ showInfoModal(label, '견적이 저장되지 않아 목록을 그대로 두었습니다. 저장한 뒤 다시 시도해 주세요.'); return false; }
    _qResetQuoteScreen();
    var t=document.getElementById('qOutToast'); if(!t){ t=document.createElement('div'); t.id='qOutToast'; t.style.cssText='position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:100080;background:#14305c;color:#fff;border-radius:10px;padding:11px 14px 11px 18px;font-size:13px;box-shadow:0 10px 30px rgba(0,0,0,.25);display:flex;align-items:center;gap:12px;max-width:92vw'; document.body.appendChild(t); }
    t.innerHTML='<span>'+esc(label)+' 완료 · "'+esc(no||'')+'" 저장 — 새 견적을 쓸 수 있게 목록을 비웠습니다</span><button type="button" style="background:#fff;color:#14305c;border:none;border-radius:6px;padding:5px 10px;font-weight:700;cursor:pointer;font-family:inherit;font-size:12px" onclick="document.getElementById(\'qOutToast\').style.display=\'none\'; qLoadSaved(\''+esc(id)+'\')">다시 열기</button><a style="color:#cbd5e1;cursor:pointer;font-size:15px" onclick="this.parentNode.style.display=\'none\'">✕</a>';
    t.style.display='flex'; clearTimeout(t._h); t._h=setTimeout(function(){ t.style.display='none'; }, 12000);
    return true;
  }
