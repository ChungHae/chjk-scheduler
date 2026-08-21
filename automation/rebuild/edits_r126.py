# -*- coding: utf-8 -*-
# r126: [매입매출 5단계] 자료 업로드 파서.
#  - 홈택스 세금계산서 목록(.xls BIFF): 사업장(등록번호)·매출/매입 자동 판별,
#    승인번호 중복 제거 + 누적본(legacy) 경계 중복 제거(사업장|사업자|작성일|공급가).
#  - 은행 거래내역 6종(국민/기업/농협/신한/우리/하나): 헤더 키워드 자동 판별,
#    입금액>0 행만 수금 반영. 사업장은 업로드 시 선택(신한 등 계좌번호 없음).
#  - 전자어음 3종(신한어음/기업어음/하나채권): 수취 = 수금(어음)으로 반영, 취소 제외.
#  - 입금자명 → 거래처: 별칭표(fxAlias)·기존 거래처명 자동 매칭. 미매칭은
#    "미배정 입금" 패널에서 지정(같은 입금자명 자동 학습) 또는 제외(복원 가능).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R126 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

# ── (1) 자료 업로드 탭 화면: 카드 3종 활성화 + 미배정 패널 호스트 ──
UPLOAD_OLD = """    // 자료 업로드 탭
    body.innerHTML =
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;max-width:980px">'
      + [['기존 앱 누적본 가져오기','legacy','입출금 앱 누적자료 zip (거래처 파일·설정표 자동 인식, 재업로드 안전)', true],
         ['홈택스 매출 계산서','sales','매출 세금계산서 목록 엑셀 (다음 단계 연결)', false],
         ['홈택스 매입 계산서','purch','매입 세금계산서 목록 엑셀 (다음 단계 연결)', false],
         ['은행 입금·어음 내역','bank','은행 거래내역·어음 엑셀 (다음 단계 연결)', false]]
        .map(function(x){
          var btn = x[3]
            ? '<label class="btn" style="display:inline-block;font-size:12px;padding:5px 14px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B;cursor:pointer">파일 선택…<input type="file" accept=".zip" style="display:none" onchange="fxImportLegacy(this)"></label>'
            : '<button type="button" class="btn" disabled style="font-size:12px;padding:5px 14px;border:1px solid #dfe5ec;color:#a8b3c0;background:#f4f6f9;cursor:default">다음 단계</button>';
          return '<div style="background:#fff;border:1px solid #d6deea;padding:16px 18px">'
            + '<div style="font-size:13px;font-weight:700;color:#14305c;margin-bottom:4px">'+x[0]+'</div>'
            + '<div style="font-size:11.5px;color:#8a94a6;margin-bottom:10px">'+x[2]+'</div>'
            + btn + '</div>';
        }).join('')
      + '</div>'
      + '<div id="fxUpResult" style="margin-top:14px;max-width:980px"></div>';"""

UPLOAD_NEW = """    // 자료 업로드 탭 (r126: 홈택스·은행·어음 파서 연결)
    var _lblBtn = function(handler, accept, multiple){
      return '<label class="btn" style="display:inline-block;font-size:12px;padding:5px 14px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B;cursor:pointer">파일 선택…<input type="file"'+(multiple?' multiple':'')+' accept="'+accept+'" style="display:none" onchange="'+handler+'(this)"></label>';
    };
    var _upCard = function(title, desc, inner){
      return '<div style="background:#fff;border:1px solid #d6deea;padding:16px 18px">'
        + '<div style="font-size:13px;font-weight:700;color:#14305c;margin-bottom:4px">'+title+'</div>'
        + '<div style="font-size:11.5px;color:#8a94a6;margin-bottom:10px">'+desc+'</div>'
        + inner + '</div>';
    };
    body.innerHTML =
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;max-width:1080px">'
      + _upCard('홈택스 세금계산서',
                '홈택스 조회 목록 엑셀 — 매출/매입·사업장 자동 판별 · 여러 파일 가능 · 재업로드 안전',
                _lblBtn('fxImportHometax','.xls,.xlsx',true))
      + _upCard('은행 입금·어음 내역',
                '은행 거래내역(국민·기업·농협·신한·우리·하나)·전자어음 엑셀 — 형식 자동 판별 · 입금만 반영',
                '<div style="display:flex;gap:8px;align-items:center">'
                + '<select id="fxUpBankBiz" class="q-flat" style="width:76px;background:#fff;color:#1a1a1a;cursor:pointer"><option value="서울">서울</option><option value="화성">화성</option></select>'
                + _lblBtn('fxImportBank','.xls,.xlsx',true)
                + '</div>')
      + _upCard('기존 앱 누적본 가져오기',
                '입출금 앱 누적자료 zip (거래처 파일·설정표 자동 인식, 재업로드 안전)',
                _lblBtn('fxImportLegacy','.zip',false))
      + '</div>'
      + '<div id="fxUpResult" style="margin-top:14px;max-width:1080px"></div>'
      + '<div id="fxUnasg" style="margin-top:14px;max-width:1080px"></div>';
    _fxEnsureData().then(function(){
      if(_fxTab!=='up') return;
      _fxMetaRefresh();
      _fxRenderUnasg();
    });"""

# ── (2) 파서 + 미배정 패널 JS (fxImportLegacy 뒤, parseExcelDate 앞) ──
PARSER_ANCHOR = "  function parseExcelDate(excelDate) {"

PARSER_JS = r"""  // ── r126: 홈택스 세금계산서 / 은행·어음 업로드 파서 ──────────
  var _FX_BIZREG = { '113-81-14978':'서울', '406-85-02616':'화성' };
  function _fxCell(v){ return v==null ? '' : String(v).trim(); }
  function _fxVbizOf(biz, name){
    for(var i=0;i<fxSalesInv.length;i++){ var e=fxSalesInv[i]; if(e.biz===biz && e.vendor===name && e.vbiz) return e.vbiz; }
    return '';
  }
  function _fxVendorNames(biz){
    var ns={};
    fxSalesInv.forEach(function(e){ if(e.biz===biz && e.vendor) ns[e.vendor]=1; });
    fxDeposits.forEach(function(e){ if(e.biz===biz && e.vendor) ns[e.vendor]=1; });
    Object.keys(fxTerms).forEach(function(k){ var p=k.split('|'); if(p[0]===biz && p[1]) ns[p[1]]=1; });
    return Object.keys(ns).sort();
  }
  function _fxResolveVendor(biz, payer){
    var p=String(payer||'').trim(); if(!p) return null;
    if(fxAlias[biz+'|'+p]) return fxAlias[biz+'|'+p];
    if(_fxVendorNames(biz).indexOf(p)>=0) return p;
    return null;
  }
  function _fxUpLog(html){
    var out=document.getElementById('fxUpResult');
    if(out) out.innerHTML='<div style="background:#fff;border:1px solid #d6deea;padding:14px 16px;font-size:12.5px;color:#374151;line-height:1.8">'+html+'</div>';
  }
  function _fxMetaRefresh(){
    var meta=document.getElementById('fxMeta');
    if(meta) meta.textContent='매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건';
  }
  // ── 홈택스 세금계산서 목록 (매출/매입·사업장 자동 판별) ──
  window.fxImportHometax = async function(inp){
    var files=Array.prototype.slice.call(inp.files||[]); inp.value='';
    if(!files.length) return;
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 업로드할 수 없습니다.'); return; }
    try{
      _fxUpLog('라이브러리 로드 중…');
      await _ensureXlsxLib(); await _fxEnsureData();
      var seenNo={};
      fxSalesInv.concat(fxPurchInv).forEach(function(e){ if(e.no) seenNo[e.no]=1; });
      var lgKey={};
      fxSalesInv.forEach(function(e){ if(e.src==='legacy') lgKey[e.biz+'|'+e.vbiz+'|'+e.date+'|'+e.supply]=1; });
      var nS=0, nP=0, nDup=0, errs=[], lines=[];
      for(var fi=0; fi<files.length; fi++){
        var f=files[fi];
        _fxUpLog('홈택스 파일 처리 중… ('+(fi+1)+'/'+files.length+')');
        try{
          var wb=XLSX.read(await f.arrayBuffer(), {type:'array', cellDates:true});
          var rows=XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {header:1, raw:true, defval:null});
          var biz=null, kind=null, hIdx=-1;
          for(var r=0;r<Math.min(rows.length,14);r++){
            var rr=(rows[r]||[]).map(_fxCell);
            for(var c=0;c<rr.length;c++){ var s0=rr[c].replace(/\s/g,''); if(_FX_BIZREG[s0]) biz=_FX_BIZREG[s0]; }
            var line=rr.join(' ');
            if(!kind && /매출.*세금계산서/.test(line)) kind='sales';
            else if(!kind && /매입.*세금계산서/.test(line)) kind='purch';
            if(hIdx<0 && rr.indexOf('작성일자')>=0 && rr.indexOf('승인번호')>=0) hIdx=r;
          }
          if(!biz || !kind || hIdx<0){ errs.push(f.name+': 홈택스 목록 형식을 인식하지 못했습니다'); continue; }
          var H=(rows[hIdx]||[]).map(_fxCell);
          var off=H.indexOf('작성일자');
          var A = kind==='sales' ? fxSalesInv : fxPurchInv;
          var iVb = off + (kind==='sales' ? 9 : 4), iVn = off + (kind==='sales' ? 11 : 6);
          var fN=0, fD=0;
          for(var r3=hIdx+1;r3<rows.length;r3++){
            var row=rows[r3]||[];
            var d=_fxD(row[off]), no=_fxCell(row[off+1]);
            var sup=_fxN(row[off+15]), tax=_fxN(row[off+16]), tot=_fxN(row[off+14]);
            if(!d || !no || sup==null) continue;
            var vbz=_fxCell(row[iVb]), vnm=_fxCell(row[iVn]);
            if(seenNo[no] || (kind==='sales' && lgKey[biz+'|'+vbz+'|'+d+'|'+sup])){ nDup++; fD++; continue; }
            seenNo[no]=1;
            if(tax==null) tax=Math.round(sup*0.1);
            if(tot==null) tot=sup+tax;
            A.push({ id:'H|'+biz+'|'+no, biz:biz, date:d, vendor:vnm, vbiz:vbz,
                     supply:sup, tax:tax, total:tot, no:no, src:'hometax', note:'' });
            if(kind==='sales'){ nS++; } else { nP++; }
            fN++;
          }
          lines.push(esc(f.name)+' → '+(kind==='sales'?'매출':'매입')+' · '+biz+' · '+fN+'건'+(fD?(' · 중복 제외 '+fD):''));
        }catch(e){ errs.push(f.name+': '+(e&&e.message||e)); }
      }
      _fxUpLog('저장 중… (Firebase)');
      await _fxSaveBig();
      _fxMetaRefresh();
      var html='<b style="color:#15803d">홈택스 반영 완료</b> — 매출 +'+nS+'건 · 매입 +'+nP+'건'+(nDup?(' · 중복 제외 '+nDup+'건'):'');
      if(lines.length) html+='<br><span style="color:#6b7280">'+lines.join('<br>')+'</span>';
      if(errs.length) html+='<br><span style="color:#dc2626">오류 '+errs.length+'건: '+esc(errs.slice(0,5).join(' / '))+'</span>';
      _fxUpLog(html);
    }catch(e){ _fxUpLog('<b style="color:#dc2626">업로드 실패:</b> '+esc(String(e&&e.message||e))); }
  };
  // ── 은행 거래내역 6종 + 전자어음 3종 (형식 자동 판별) ──
  var _FX_PAYKEY = [ ['보낸분/받는분','국민'], ['거래기록사항','농협'], ['기재내용','우리'], ['의뢰인/수취인','하나'], ['거래내용','기업'], ['내용','신한'] ];
  window.fxImportBank = async function(inp){
    var files=Array.prototype.slice.call(inp.files||[]); inp.value='';
    if(!files.length) return;
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 업로드할 수 없습니다.'); return; }
    var bizSel=document.getElementById('fxUpBankBiz');
    var biz=(bizSel && bizSel.value) || '서울';
    try{
      _fxUpLog('라이브러리 로드 중…');
      await _ensureXlsxLib(); await _fxEnsureData();
      var seen={};
      fxDeposits.forEach(function(e){ seen[e.id]=1; if(e.noteNo) seen['NN|'+e.biz+'|'+e.noteNo]=1; });
      var nDep=0, nNote=0, nDup=0, nAuto=0, nUn=0, errs=[], lines=[];
      for(var fi=0; fi<files.length; fi++){
        var f=files[fi];
        _fxUpLog('파일 처리 중… ('+(fi+1)+'/'+files.length+') — '+esc(f.name));
        try{
          var wb=XLSX.read(await f.arrayBuffer(), {type:'array', cellDates:true});
          var rows=XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {header:1, raw:true, defval:null});
          // 1) 어음 형식 판별
          var noteKind=null, hIdx=-1, H=null;
          for(var r=0;r<Math.min(rows.length,14);r++){
            var rr=(rows[r]||[]).map(_fxCell);
            if(rr.indexOf('전자어음번호')>=0){ noteKind='신한어음'; hIdx=r; H=rr; break; }
            if(rr.indexOf('어음번호')>=0 && rr.indexOf('구매기업명')>=0){ noteKind='기업어음'; hIdx=r; H=rr; break; }
            if(rr.indexOf('채권번호')>=0 && rr.indexOf('구매기업명')>=0){ noteKind='하나채권'; hIdx=r; H=rr; break; }
          }
          if(noteKind){
            var iNo, iVen, iAmt, iDt, iSt, iCxl=-1;
            if(noteKind==='신한어음'){
              iNo=H.indexOf('전자어음번호'); iVen=H.indexOf('발행인'); iAmt=H.indexOf('어음금액');
              iDt=H.indexOf('수취일자'); if(iDt<0) iDt=H.indexOf('발행일자'); iSt=H.indexOf('상태');
            } else if(noteKind==='기업어음'){
              iNo=H.indexOf('어음번호'); iVen=H.indexOf('구매기업명'); iAmt=H.indexOf('채권금액');
              iDt=H.indexOf('채권등록일'); iSt=H.indexOf('상태');
            } else {
              iNo=H.indexOf('채권번호'); iVen=H.indexOf('구매기업명');
              iAmt=H.indexOf('채권금액(원)'); if(iAmt<0) iAmt=H.indexOf('채권금액');
              iDt=H.indexOf('발행일'); iSt=H.indexOf('상태'); iCxl=H.indexOf('취소일');
            }
            if(iNo<0 || iVen<0 || iAmt<0 || iDt<0){ errs.push(f.name+': '+noteKind+' 헤더 열을 찾지 못했습니다'); continue; }
            var fN2=0, fD2=0, fU2=0;
            for(var r4=hIdx+1;r4<rows.length;r4++){
              var row4=rows[r4]||[];
              var noteNo=_fxCell(row4[iNo]);
              if(!noteNo || /합계/.test(_fxCell(row4[0]))) continue;
              var st=iSt>=0?_fxCell(row4[iSt]):'';
              if(/취소/.test(st) || (iCxl>=0 && _fxCell(row4[iCxl]))) continue;
              var d4=_fxD(row4[iDt]), amt4=_fxN(row4[iAmt]), ven4=_fxCell(row4[iVen]);
              if(!d4 || !amt4 || amt4<=0) continue;
              if(seen['NN|'+biz+'|'+noteNo]){ nDup++; fD2++; continue; }
              seen['NN|'+biz+'|'+noteNo]=1;
              var v4=_fxResolveVendor(biz, ven4);
              fxDeposits.push({ id:'NT|'+biz+'|'+noteNo, biz:biz, date:d4, amount:amt4, payer:ven4,
                                vendor:v4||'', vbiz:v4?_fxVbizOf(biz,v4):'', kind:'note', bank:noteKind,
                                noteNo:noteNo, src:'upload' });
              nNote++; fN2++;
              if(v4){ nAuto++; } else { nUn++; fU2++; }
            }
            lines.push(esc(f.name)+' → '+noteKind+' · 수취 '+fN2+'건'+(fU2?(' · 미배정 '+fU2):'')+(fD2?(' · 중복 '+fD2):''));
            continue;
          }
          // 2) 은행 입금 형식 판별 (입금자명 열 키워드)
          var bank=null, iPay=-1;
          for(var r5=0;r5<Math.min(rows.length,14);r5++){
            var rr5=(rows[r5]||[]).map(_fxCell);
            for(var k=0;k<_FX_PAYKEY.length;k++){
              var ii=rr5.indexOf(_FX_PAYKEY[k][0]);
              if(ii>=0){ bank=_FX_PAYKEY[k][1]; iPay=ii; hIdx=r5; H=rr5; break; }
            }
            if(bank) break;
          }
          if(!bank){ errs.push(f.name+': 은행/어음 형식을 인식하지 못했습니다'); continue; }
          var iDate=H.indexOf('거래일시'); if(iDate<0) iDate=H.indexOf('거래일자');
          var iIn=-1;
          ['입금액(원)','입금금액(원)','입금(원)','입금액','입금'].some(function(kk){ iIn=H.indexOf(kk); return iIn>=0; });
          if(iDate<0 || iIn<0){ errs.push(f.name+': '+bank+' 헤더 열을 찾지 못했습니다'); continue; }
          var fN3=0, fU3=0, fD3=0;
          for(var r6=hIdx+1;r6<rows.length;r6++){
            var row6=rows[r6]||[];
            var rawDt=_fxCell(row6[iDate]);
            var d6=_fxD(row6[iDate]), amt6=_fxN(row6[iIn]), payer=_fxCell(row6[iPay]);
            if(!d6 || !amt6 || amt6<=0) continue;
            var id6='B|'+biz+'|'+bank+'|'+(rawDt||d6)+'|'+amt6+'|'+payer;
            if(seen[id6]){ nDup++; fD3++; continue; }
            seen[id6]=1;
            var v6=_fxResolveVendor(biz, payer);
            fxDeposits.push({ id:id6, biz:biz, date:d6, amount:amt6, payer:payer,
                              vendor:v6||'', vbiz:v6?_fxVbizOf(biz,v6):'', kind:'bank', bank:bank, src:'upload' });
            nDep++; fN3++;
            if(v6){ nAuto++; } else { nUn++; fU3++; }
          }
          lines.push(esc(f.name)+' → '+bank+' · 입금 '+fN3+'건'+(fU3?(' · 미배정 '+fU3):'')+(fD3?(' · 중복 '+fD3):''));
        }catch(e){ errs.push(f.name+': '+(e&&e.message||e)); }
      }
      _fxUpLog('저장 중… (Firebase)');
      await _fxSaveBig();
      _fxSave();
      _fxMetaRefresh();
      var html='<b style="color:#15803d">반영 완료</b> — '+biz+' · 입금 +'+nDep+'건 · 어음 +'+nNote+'건'
        + (nAuto?(' · 자동 배정 '+nAuto):'') + (nDup?(' · 중복 제외 '+nDup):'');
      if(nUn) html+='<br><b style="color:#d97706">미배정 '+nUn+'건</b> — 아래 미배정 입금 패널에서 거래처를 지정해 주세요.';
      if(lines.length) html+='<br><span style="color:#6b7280">'+lines.join('<br>')+'</span>';
      if(errs.length) html+='<br><span style="color:#dc2626">오류 '+errs.length+'건: '+esc(errs.slice(0,5).join(' / '))+'</span>';
      _fxUpLog(html);
      _fxRenderUnasg();
    }catch(e){ _fxUpLog('<b style="color:#dc2626">업로드 실패:</b> '+esc(String(e&&e.message||e))); }
  };
  // ── 미배정 입금 패널 (거래처 지정 → 별칭 학습 / 제외 → 복원 가능) ──
  var _fxUnList=[], _fxExList=[], _fxShowExcl=false;
  window.fxToggleExcl = function(){ _fxShowExcl=!_fxShowExcl; _fxRenderUnasg(); };
  function _fxRenderUnasg(){
    var host=document.getElementById('fxUnasg'); if(!host) return;
    _fxUnList = fxDeposits.filter(function(e){ return !e.vendor && !e.excluded; });
    _fxExList = fxDeposits.filter(function(e){ return e.excluded; });
    if(!_fxUnList.length && !_fxExList.length){ host.innerHTML=''; return; }
    _fxUnList.sort(function(a,b){ return a.date<b.date?1:a.date>b.date?-1:0; });
    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;white-space:nowrap';
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;white-space:nowrap;vertical-align:middle';
    var html='';
    if(_fxUnList.length){
      var dl='<datalist id="fxVendDl">'
        + _fxVendorNames('서울').concat(_fxVendorNames('화성'))
            .filter(function(x,i,a){ return a.indexOf(x)===i; })
            .map(function(n){ return '<option value="'+esc(n)+'">'; }).join('')
        + '</datalist>';
      var rows=_fxUnList.slice(0,300).map(function(e,i){
        return '<tr>'
          + '<td style="'+TD+';text-align:center;color:#6b7280">'+e.biz+'</td>'
          + '<td style="'+TD+';color:#6b7280">'+e.date+'</td>'
          + '<td style="'+TD+';text-align:center;color:#6b7280">'+esc(e.bank||'')+(e.kind==='note'?' <span style="font-size:10.5px;font-weight:700;color:#7c3aed;border:1px solid #7c3aed;padding:0 5px">어음</span>':'')+'</td>'
          + '<td style="'+TD+';font-weight:700;color:#14305c">'+esc(e.payer||'')+'</td>'
          + '<td style="'+TD+';text-align:right;font-weight:700">'+_fxFmt(e.amount)+'</td>'
          + '<td style="'+TD+'"><div style="display:flex;gap:6px;align-items:center">'
          +   '<input id="fxUnV'+i+'" list="fxVendDl" class="q-flat" placeholder="거래처명 입력…" style="width:170px" onkeydown="if(event.key===\'Enter\'){event.preventDefault();fxAssignDep('+i+');}">'
          +   '<button type="button" class="btn" onclick="fxAssignDep('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B">지정</button>'
          +   '<button type="button" class="btn" onclick="fxExcludeDep('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #dc2626;color:#dc2626;background:#fff">제외</button>'
          + '</div></td></tr>';
      }).join('');
      html += '<div style="background:#fff;border:1px solid #d6deea">'
        + '<div style="padding:10px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#d97706">미배정 입금 '+_fxUnList.length+'건'
        + ' <span style="font-weight:400;color:#8a94a6">— 거래처를 지정하면 같은 입금자명은 다음부터 자동 배정됩니다. 회사 수금이 아니면 제외하세요.</span></div>'
        + '<div style="max-height:420px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
        + '<thead><tr><th style="'+TH+'">사업장</th><th style="'+TH+'">입금일</th><th style="'+TH+'">은행</th><th style="'+TH+';text-align:left">입금자</th><th style="'+TH+';text-align:right">금액</th><th style="'+TH+';text-align:left">거래처 지정</th></tr></thead>'
        + '<tbody>'+rows+'</tbody></table></div></div>' + dl;
    }
    if(_fxExList.length){
      html += '<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">제외한 입금 '+_fxExList.length+'건 '
        + '<button type="button" class="btn" onclick="fxToggleExcl()" style="font-size:11px;padding:2px 10px;border:1px solid #d6deea;color:#6b7280;background:#fff">'+(_fxShowExcl?'접기':'보기')+'</button></div>';
      if(_fxShowExcl){
        var rows2=_fxExList.slice(0,300).map(function(e,i){
          return '<tr>'
            + '<td style="'+TD+';text-align:center;color:#9ca3af">'+e.biz+'</td>'
            + '<td style="'+TD+';color:#9ca3af">'+e.date+'</td>'
            + '<td style="'+TD+';text-align:center;color:#9ca3af">'+esc(e.bank||'')+'</td>'
            + '<td style="'+TD+';color:#9ca3af">'+esc(e.payer||'')+'</td>'
            + '<td style="'+TD+';text-align:right;color:#9ca3af">'+_fxFmt(e.amount)+'</td>'
            + '<td style="'+TD+'"><button type="button" class="btn" onclick="fxRestoreDep('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #5b7ba6;color:#5b7ba6;background:#fff">복원</button></td></tr>';
        }).join('');
        html += '<div style="margin-top:6px;background:#fff;border:1px solid #e3e9f0;max-height:260px;overflow:auto"><table style="width:100%;border-collapse:collapse"><tbody>'+rows2+'</tbody></table></div>';
      }
    }
    host.innerHTML=html;
  }
  window.fxAssignDep = function(i){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 지정할 수 없습니다.'); return; }
    var d=_fxUnList[i]; if(!d) return;
    var el=document.getElementById('fxUnV'+i);
    var v=(el && el.value || '').trim();
    if(!v){ if(el) el.focus(); return; }
    d.vendor=v; d.vbiz=_fxVbizOf(d.biz, v);
    if(d.payer) fxAlias[d.biz+'|'+d.payer]=v;
    fxDeposits.forEach(function(e){
      if(e!==d && !e.vendor && !e.excluded && e.biz===d.biz && e.payer===d.payer){ e.vendor=v; e.vbiz=d.vbiz; }
    });
    _fxSaveBig().catch(function(_e){});
    _fxSave();
    _fxMetaRefresh();
    _fxRenderUnasg();
  };
  window.fxExcludeDep = function(i){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 제외할 수 없습니다.'); return; }
    var d=_fxUnList[i]; if(!d) return;
    d.excluded=true;
    _fxSaveBig().catch(function(_e){});
    _fxRenderUnasg();
  };
  window.fxRestoreDep = function(i){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 복원할 수 없습니다.'); return; }
    var d=_fxExList[i]; if(!d) return;
    d.excluded=false;
    _fxSaveBig().catch(function(_e){});
    _fxRenderUnasg();
  };
"""

def apply_r126(s, path):
    s = rep(s, UPLOAD_OLD, UPLOAD_NEW, 1, 'UPLOAD')
    s = rep(s, PARSER_ANCHOR, PARSER_JS + PARSER_ANCHOR, 1, 'PARSER')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r126(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r125 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r125 2026-08-21 -->', '<!-- test build r126 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
