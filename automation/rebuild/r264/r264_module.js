
  // ─── r264: 견적 메일에 사업자등록증·통장사본 첨부 (지점별 · 파일은 서버(Firebase)에만 · 저장소에는 없음) ───
  var _DOC_KINDS=[{k:'biz', label:'사업자등록증'},{k:'bank', label:'통장사본'}];
  function _docDate(t){ var d=new Date(t||0); return (d.getMonth()+1)+'/'+d.getDate(); }
  var _docMeta=null;   // {seoul:{biz:{name,type,size,at,by}, bank:{..}}, hs:{..}}
  function _docUrl(p){ return _fbDbUrl+'/'+_AUTH_BASE+'/'+p+'.json'; }
  async function _docLoadMeta(force){ if(_docMeta && !force) return _docMeta; try{ var r=await _fbFetch(_docUrl('sched_doc_files_meta')); _docMeta=(r&&r.ok?(await r.json()):null)||{}; }catch(_e){ _docMeta={}; } return _docMeta; }
  async function _docGetFile(acct, k){ var r=await _fbFetch(_docUrl('sched_doc_files/'+acct+'_'+k)); if(!r||!r.ok) throw new Error('첨부 서류를 불러오지 못했습니다 (HTTP '+(r?r.status:'네트워크')+')'); var j=await r.json(); if(!j||!j.b64) throw new Error('첨부 서류 파일이 서버에 없습니다 — 메일 설정 > 첨부 서류에서 다시 등록해 주세요'); return j; }
  function _docAcct(){ var s=document.getElementById('mlAcct'); var v=s?s.value:((window._mlDraft&&window._mlDraft.account)||'seoul'); return v==='hs'?'hs':'seoul'; }
  function _docAcctLabel(a){ return a==='hs'?'화성':'서울'; }
  window._mlDocSel={biz:false, bank:false};
  window._mlDocsRender=async function(){ var el=document.getElementById('mlDocs'); if(!el) return; var a=_docAcct(); var m=await _docLoadMeta(); var am=(m&&m[a])||{};
    var h='<span class="ml-docs-l">서류 첨부</span>';
    _DOC_KINDS.forEach(function(d){ var f=am[d.k]; var on=!!(f && window._mlDocSel[d.k]);
      if(f) h+='<span class="ml-chip'+(on?' on':'')+'" onclick="mlDocToggle(\''+d.k+'\')" title="'+esc(f.name||'')+' · '+Math.round((f.size||0)/1024)+'KB">'+(on?'✓ ':'+ ')+'<b>'+d.label+'</b> <i>'+_docAcctLabel(a)+'</i></span>';
      else h+='<span class="ml-chip" style="color:#9ca3af;border-style:dashed;cursor:default" title="'+_docAcctLabel(a)+' '+d.label+' 파일이 아직 등록되지 않았습니다">'+d.label+' <i>미등록</i></span>'; });
    if(_isAdmin()) h+='<a class="ml-docs-a" onclick="docFilesOpen()">서류 등록·변경</a>';
    el.innerHTML=h; };
  window.mlDocToggle=function(k){ window._mlDocSel[k]=!window._mlDocSel[k]; _mlDocsRender(); };
  async function _mlDocAtts(){ var a=_docAcct(); var m=await _docLoadMeta(); var am=(m&&m[a])||{}; var out=[];
    for(var i=0;i<_DOC_KINDS.length;i++){ var d=_DOC_KINDS[i]; if(!window._mlDocSel[d.k] || !am[d.k]) continue; var f=await _docGetFile(a, d.k);
      var ext=(String(f.name||'').match(/\.[A-Za-z0-9]{2,5}$/)||['.pdf'])[0]; out.push({ name:d.label+' - 충해전기(주)'+(a==='hs'?' 화성영업소':'')+ext, type:f.type||'application/pdf', b64:f.b64 }); }
    return out; }
  // ─ 관리자: 서류 등록 ─
  window.docFilesOpen=async function(){ if(!_isAdmin()){ showInfoModal('첨부 서류','관리자만 등록할 수 있습니다.'); return; } var m=await _docLoadMeta(true);
    var row=function(a){ return _DOC_KINDS.map(function(d){ var f=(m[a]||{})[d.k];
      return '<tr><td style="white-space:nowrap;font-weight:700;color:#14305c">'+_docAcctLabel(a)+'</td><td style="white-space:nowrap">'+d.label+'</td><td>'+(f?('<span style="color:#15803d">'+esc(f.name||'')+'</span> <span style="color:#9ca3af">'+Math.round((f.size||0)/1024)+'KB · '+_docDate(f.at)+' '+esc(f.by||'')+'</span>'):'<span style="color:#9ca3af">미등록</span>')+'</td>'
        +'<td style="white-space:nowrap"><label class="btn" style="padding:3px 9px;font-size:11.5px;cursor:pointer;margin:0">'+(f?'바꾸기':'올리기')+'<input type="file" accept=".pdf,.jpg,.jpeg,.png" style="display:none" onchange="docFileUpload(\''+a+'\',\''+d.k+'\',this)"></label>'+(f?' <button class="btn" onclick="docFileView(\''+a+'\',\''+d.k+'\')" style="padding:3px 9px;font-size:11.5px">보기</button> <button class="btn" onclick="docFileDel(\''+a+'\',\''+d.k+'\')" style="padding:3px 9px;font-size:11.5px;color:#dc2626">삭제</button>':'')+'</td></tr>'; }).join(''); };
    var h='<div style="padding:14px 20px;border-bottom:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center"><span style="font-size:16px;font-weight:700;color:#1B3A6B">견적 메일 첨부 서류</span><button class="btn" onclick="document.getElementById(\'docFilesOverlay\').style.display=\'none\'; try{ _mlDocsRender(); }catch(_e){}" style="padding:4px 10px">닫기</button></div>'
      +'<div style="padding:14px 20px;font-size:13px;display:flex;flex-direction:column;gap:10px"><div style="font-size:12px;color:#6b7280;line-height:1.6">보내는 계정(서울 chjk@ / 화성 hs-chjk@)에 맞는 지점 서류가 붙습니다. PDF·JPG·PNG, 한 파일 3MB 까지. 파일은 팀 서버(Firebase)에만 저장되고 공개 저장소(GitHub)에는 올라가지 않습니다.</div>'
      +'<table class="qov-tbl doc-tbl"><tbody>'+row('seoul')+row('hs')+'</tbody></table><div id="docFilesMsg" style="font-size:12px;color:#6b7280"></div></div>';
    _mailOverlay('docFilesOverlay', h, 680); };
  window.docFileUpload=function(a, k, inp){ var f=inp.files&&inp.files[0]; if(!f) return; var msg=function(t){ var e=document.getElementById('docFilesMsg'); if(e) e.innerHTML=t; };
    if(f.size>3*1024*1024){ msg('<span style="color:#dc2626">3MB 가 넘습니다 ('+Math.round(f.size/1024)+'KB). 스캔 해상도를 낮춰 다시 올려 주세요.</span>'); return; }
    msg('올리는 중…'); _blobToB64(f).then(async function(b64){ var who=(_authUser&&_authUser.name)||'';
      var r=await _fbFetch(_docUrl('sched_doc_files/'+a+'_'+k), {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:f.name, type:f.type||'application/pdf', b64:b64})});
      if(!r||!r.ok) throw new Error('HTTP '+(r?r.status:'네트워크'));
      var meta={}; meta[k]={name:f.name, type:f.type||'application/pdf', size:f.size, at:Date.now(), by:who};
      var r2=await _fbFetch(_docUrl('sched_doc_files_meta/'+a), {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(meta)});
      if(!r2||!r2.ok) throw new Error('HTTP '+(r2?r2.status:'네트워크'));
      await docFilesOpen(); var e=document.getElementById('docFilesMsg'); if(e) e.innerHTML='<span style="color:#15803d">'+_docAcctLabel(a)+' '+(k==='biz'?'사업자등록증':'통장사본')+' 등록 완료</span>';
    }).catch(function(e){ msg('<span style="color:#dc2626">올리기 실패: '+esc(e&&e.message||String(e))+'</span>'); }); };
  window.docFileView=async function(a, k){ try{ var f=await _docGetFile(a,k); var u8=_nyB64ToU8(f.b64); var url=URL.createObjectURL(new Blob([u8],{type:f.type||'application/pdf'})); window.open(url,'_blank','noopener'); setTimeout(function(){ URL.revokeObjectURL(url); },60000); }catch(e){ showInfoModal('첨부 서류', esc(e&&e.message||String(e))); } };
  window.docFileDel=function(a, k){ showConfirmModal('첨부 서류 삭제', _docAcctLabel(a)+' '+(k==='biz'?'사업자등록증':'통장사본')+' 파일을 지울까요?', async function(){ try{ await _fbFetch(_docUrl('sched_doc_files/'+a+'_'+k), {method:'DELETE'}); await _fbFetch(_docUrl('sched_doc_files_meta/'+a+'/'+k), {method:'DELETE'}); }catch(_e){} await docFilesOpen(); }, '삭제', '#dc2626'); };
  (function(){ var st=document.createElement('style'); st.textContent='.ml-docs{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:6px} .ml-docs-l{font-size:11.5px;font-weight:700;color:#14305c;margin-right:2px} .ml-docs-a{font-size:11px;color:#1B3A6B;text-decoration:underline;cursor:pointer;margin-left:4px} .doc-tbl{width:100%;border-collapse:collapse} .doc-tbl td{padding:6px 6px;border-bottom:1px solid #f1f5f9;vertical-align:middle;font-size:12.5px}'; document.head.appendChild(st); })();
