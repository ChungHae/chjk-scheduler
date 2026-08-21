# -*- coding: utf-8 -*-
# r127: [매입매출 6단계·마무리] 엑셀 다운로드.
#  - 거래처 원장 엑셀 (원장 펼침 패널의 "원장 엑셀" 버튼): 요약부 + 일자/구분/내용/증감/잔액
#  - 미수 현황 목록 엑셀 (미수 현황 툴바 "엑셀"): 현재 사업장·검색·상태 필터 그대로 반영
#  - 매입·매출 집계 엑셀 (집계 툴바 "엑셀"): 현재 모드(월별/거래처별)·연도 그대로 반영
#  - 서식: 기존 앱 관례(xlsx-js-style, 헤더 볼드+배경, 금액 회계서식 #,##0)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R127 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

# (1) 원장 펼침 패널: 안내 문구 → 다운로드 버튼
LEDGER_OLD = """      +   '<span style="color:#9ca3af">엑셀 다운로드는 다음 단계에서 제공</span>'"""
LEDGER_NEW = """      +   '<button type="button" class="btn" onclick="event.stopPropagation();fxLedgerXls(\\''+String(L.key).replace(/'/g,'\\\\\\'')+'\\')" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#14305c;background:#f4f8fe">원장 엑셀</button>'"""

# (2) 미수 현황 툴바: 엑셀 버튼 (칩 앞)
AR_OLD = """          + '<span id="fxArChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-left:6px"></span>'"""
AR_NEW = """          + '<button type="button" class="btn" onclick="fxArXls()" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#14305c;background:#f4f8fe">엑셀</button>'
          + '<span id="fxArChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-left:6px"></span>'"""

# (3) 집계 툴바: 엑셀 버튼 (검색창 뒤)
SUM_OLD = """          + '<input type="text" id="fxSumQ" class="q-flat" placeholder="거래처 검색…" value="'+esc(_fxSumQ)+'" oninput="fxSumSearch(this.value)" style="width:200px;display:none">'"""
SUM_NEW = """          + '<input type="text" id="fxSumQ" class="q-flat" placeholder="거래처 검색…" value="'+esc(_fxSumQ)+'" oninput="fxSumSearch(this.value)" style="width:200px;display:none">'
          + '<button type="button" class="btn" onclick="fxSumXls()" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#14305c;background:#f4f8fe">엑셀</button>'"""

# (4) r124 결함 수정: 기초이월(fxOpenings)이 사업자번호 없는 별도 원장으로 갈라지던 것
#     → 같은 이름의 기존 원장(사업자번호 키)에 병합
OPEN_OLD = """    Object.keys(fxOpenings).forEach(function(k){
      var p=k.split('|'); if(p[0]!==region) return;
      var o=fxOpenings[k]||{}; var sl=slot('', p[1]); sl.opening=Number(o.amount)||0; sl.openDate=o.asOf||null;
    });"""
OPEN_NEW = """    Object.keys(fxOpenings).forEach(function(k){
      var p=k.split('|'); if(p[0]!==region) return;
      var o=fxOpenings[k]||{};
      var target=null;
      Object.keys(map).forEach(function(mk){ if(!target && map[mk].name===p[1]) target=map[mk]; });
      var sl = target || slot('', p[1]);
      sl.opening=Number(o.amount)||0; sl.openDate=o.asOf||null;
    });"""

# (5) 다운로드 함수 3종 (r126 파서 블록 앞)
XLS_ANCHOR = "  // ── r126: 홈택스 세금계산서 / 은행·어음 업로드 파서 ──────────"

XLS_JS = r"""  // ── r127: 매입매출 엑셀 다운로드 ──────────────────────
  var _FX_ACC_Z = '_-* #,##0_-;-* #,##0_-;_-* "-"_-;_-@_-';
  function _fxDs(){ var d=new Date(); return ''+d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0'); }
  function _fxSafeName(n){ return String(n||'거래처').replace(/[\/:*?"<>|]/g,' ').trim(); }
  function _fxXlsStyle(ws, headRow, moneyCols, leftCols){
    var range=XLSX.utils.decode_range(ws['!ref']);
    for(var R=range.s.r; R<=range.e.r; R++){
      for(var C=range.s.c; C<=range.e.c; C++){
        var ref=XLSX.utils.encode_cell({r:R,c:C});
        var cell=ws[ref]; if(!cell) continue;
        var st={ font:{sz:10}, alignment:{horizontal:'center', vertical:'center'} };
        if(R===headRow){
          st.font={sz:10, bold:true};
          st.fill={patternType:'solid', fgColor:{rgb:'DCE6F5'}};
        } else if(R>headRow){
          if(moneyCols.indexOf(C)>=0 && typeof cell.v==='number'){
            cell.z=_FX_ACC_Z;
            st.alignment={horizontal:'right', vertical:'center'};
          } else if(leftCols && leftCols.indexOf(C)>=0){
            st.alignment={horizontal:'left', vertical:'center'};
          }
        } else {
          if(typeof cell.v==='number'){ cell.z='#,##0'; st.alignment={horizontal:'right', vertical:'center'}; }
          else { st.alignment={horizontal:'left', vertical:'center'}; if(C===0||C===2) st.font={sz:10, bold:true}; }
        }
        cell.s=st;
      }
    }
  }
  // 거래처 원장 엑셀
  window.fxLedgerXls = async function(key){
    try{
      await _ensureXlsxLib();
      var lg=_fxLedgers(_fxRegion).find(function(x){ return x.key===key; });
      if(!lg){ showInfoModal('원장 다운로드','거래처를 찾지 못했습니다.'); return; }
      var L=lg.L, rows=[];
      if(L.opening) rows.push({date:L.openDate||'', type:'기초', desc:'기초 이월', chg:L.opening});
      L.invs.forEach(function(e){ rows.push({date:e.date, type:'계산서', desc:'세금계산서 (공급가 '+_fxFmt(e.supply)+' + 세액 '+_fxFmt(e.tax)+')'+(e.note?' · '+e.note:''), chg:e.total}); });
      L.deps.forEach(function(e){ rows.push({date:e.date, type:(e.kind==='note'?'어음':'입금'), desc:(e.bank||'')+(e.bank?' · ':'')+(e.payer||''), chg:-e.amount}); });
      L.adjs.forEach(function(a){ rows.push({date:a.date, type:'조정', desc:a.memo||'', chg:a.amount}); });
      rows.sort(function(a,b){ return a.date<b.date?-1:a.date>b.date?1:(a.chg>0?-1:1); });
      var bal=0; rows.forEach(function(r){ bal+=r.chg; r.bal=bal; });
      var aoa=[
        ['거래처', lg.name, '사업자번호', lg.vbiz||'-'],
        ['사업장', _fxRegion, '결제조건', lg.term||'기본(익익월말)'],
        ['계산서 누계', lg.invSum, '입금·조정 누계', lg.depSum],
        ['미수 잔액', lg.bal, '작성일', dk(new Date())],
        [],
        ['일자','구분','내용','증감','잔액']
      ];
      rows.forEach(function(r){ aoa.push([r.date, r.type, r.desc, r.chg, r.bal]); });
      var ws=XLSX.utils.aoa_to_sheet(aoa);
      ws['!cols']=[{wch:12},{wch:8},{wch:48},{wch:14},{wch:14}];
      _fxXlsStyle(ws, 5, [3,4], [2]);
      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, '원장');
      XLSX.writeFile(wb, _fxSafeName(lg.name)+' 원장_'+_fxRegion+'_'+_fxDs()+'.xlsx');
    }catch(e){ showInfoModal('다운로드 실패', (e&&e.message||String(e))); }
  };
  // 미수 현황 목록 엑셀 (현재 필터 반영)
  window.fxArXls = async function(){
    try{
      await _ensureXlsxLib();
      var data=_fxLedgers(_fxRegion);
      if(_fxQ) data=data.filter(function(x){ return x.name.toLowerCase().indexOf(_fxQ)>=0 || x.vbiz.indexOf(_fxQ)>=0; });
      if(_fxStatusF!=='all'){
        if(_fxStatusF==='미수') data=data.filter(function(x){ return x.status==='미수'||x.status==='장기미수'; });
        else data=data.filter(function(x){ return x.status===_fxStatusF; });
      }
      data.sort(function(a,b){ return b.bal-a.bal; });
      if(!data.length){ showInfoModal('미수 현황','다운로드할 거래처가 없습니다.'); return; }
      var aoa=[['상태','거래처','사업자번호','미수 잔액','계산서 누계','입금·조정 누계','최근 계산서','최근 입금','경과일','결제조건']];
      data.forEach(function(x){
        aoa.push([x.status, x.name, x.vbiz||'', x.bal, x.invSum, x.depSum, x.lastInv||'', x.lastDep||'', x.over||0, x.term||'']);
      });
      var tB=data.reduce(function(a,x){ return a+(x.bal>0?x.bal:0); },0);
      aoa.push(['합계','미수 '+data.filter(function(x){return x.bal>0;}).length+'곳','', tB, data.reduce(function(a,x){return a+x.invSum;},0), data.reduce(function(a,x){return a+x.depSum;},0),'','','','']);
      var ws=XLSX.utils.aoa_to_sheet(aoa);
      ws['!cols']=[{wch:8},{wch:24},{wch:14},{wch:13},{wch:13},{wch:13},{wch:11},{wch:11},{wch:7},{wch:11}];
      _fxXlsStyle(ws, 0, [3,4,5], [1]);
      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, '미수현황');
      XLSX.writeFile(wb, '미수현황_'+_fxRegion+'_'+_fxDs()+'.xlsx');
    }catch(e){ showInfoModal('다운로드 실패', (e&&e.message||String(e))); }
  };
  // 매입·매출 집계 엑셀 (현재 모드·연도 반영)
  window.fxSumXls = async function(){
    try{
      await _ensureXlsxLib();
      var yr=_fxSumYear || _fxYears()[0];
      var sv=fxSalesInv.filter(function(e){ return e.biz===_fxRegion && e.date && e.date.slice(0,4)===yr; });
      var pv=fxPurchInv.filter(function(e){ return e.biz===_fxRegion && e.date && e.date.slice(0,4)===yr; });
      if(!sv.length && !pv.length){ showInfoModal('집계','해당 연도 자료가 없습니다.'); return; }
      var aoa, fn, money, left;
      if(_fxSumMode==='month'){
        var M={}, m;
        for(m=1;m<=12;m++) M[m]={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
        sv.forEach(function(e){ var k=Number(e.date.slice(5,7)); if(M[k]){ M[k].sc++; M[k].ss+=e.supply||0; M[k].st+=e.tax||0; M[k].stt+=e.total||0; } });
        pv.forEach(function(e){ var k=Number(e.date.slice(5,7)); if(M[k]){ M[k].pc++; M[k].ps+=e.supply||0; M[k].pt+=e.tax||0; M[k].ptt+=e.total||0; } });
        var T={ sc:0, ss:0, st:0, stt:0, pc:0, ps:0, pt:0, ptt:0 };
        aoa=[['월','매출 건수','매출 공급가액','매출 세액','매출 합계','매입 건수','매입 공급가액','매입 세액','매입 합계','차액(합계)']];
        for(m=1;m<=12;m++){
          var x=M[m];
          ['sc','ss','st','stt','pc','ps','pt','ptt'].forEach(function(k){ T[k]+=x[k]; });
          aoa.push([m+'월', x.sc, x.ss, x.st, x.stt, x.pc, x.ps, x.pt, x.ptt, x.stt-x.ptt]);
        }
        aoa.push(['합계', T.sc, T.ss, T.st, T.stt, T.pc, T.ps, T.pt, T.ptt, T.stt-T.ptt]);
        fn='매입매출집계_월별_'+_fxRegion+'_'+yr+'_'+_fxDs()+'.xlsx';
        money=[2,3,4,6,7,8,9]; left=null;
        var ws1=XLSX.utils.aoa_to_sheet(aoa);
        ws1['!cols']=[{wch:6},{wch:9},{wch:14},{wch:12},{wch:14},{wch:9},{wch:14},{wch:12},{wch:14},{wch:14}];
        _fxXlsStyle(ws1, 0, money, left);
        var wb1=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb1, ws1, yr+'년 월별');
        XLSX.writeFile(wb1, fn);
        return;
      }
      var V={};
      function vslot(e){ var k=(e.vbiz&&/\d{3}-\d{2}-\d{5}/.test(e.vbiz))?e.vbiz:('N|'+e.vendor); if(!V[k]) V[k]={name:e.vendor, vbiz:e.vbiz||'', sc:0, stt:0, pc:0, ptt:0}; if(e.vendor) V[k].name=e.vendor; return V[k]; }
      sv.forEach(function(e){ var s2=vslot(e); s2.sc++; s2.stt+=e.total||0; });
      pv.forEach(function(e){ var s3=vslot(e); s3.pc++; s3.ptt+=e.total||0; });
      var list=Object.keys(V).map(function(k){ return V[k]; });
      if(_fxSumQ) list=list.filter(function(x){ return x.name.toLowerCase().indexOf(_fxSumQ)>=0 || x.vbiz.indexOf(_fxSumQ)>=0; });
      list.sort(function(a,b){ return (b.stt+b.ptt)-(a.stt+a.ptt); });
      if(!list.length){ showInfoModal('집계','조건에 맞는 거래처가 없습니다.'); return; }
      aoa=[['거래처','사업자번호','매출 건수','매출 합계','매입 건수','매입 합계']];
      list.forEach(function(x){ aoa.push([x.name, x.vbiz||'', x.sc, x.stt, x.pc, x.ptt]); });
      aoa.push(['합계 ('+list.length+'곳)','', list.reduce(function(a,x){return a+x.sc;},0), list.reduce(function(a,x){return a+x.stt;},0), list.reduce(function(a,x){return a+x.pc;},0), list.reduce(function(a,x){return a+x.ptt;},0)]);
      var ws2=XLSX.utils.aoa_to_sheet(aoa);
      ws2['!cols']=[{wch:26},{wch:14},{wch:9},{wch:14},{wch:9},{wch:14}];
      _fxXlsStyle(ws2, 0, [3,5], [0]);
      var wb2=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb2, ws2, yr+'년 거래처별');
      XLSX.writeFile(wb2, '매입매출집계_거래처별_'+_fxRegion+'_'+yr+'_'+_fxDs()+'.xlsx');
    }catch(e){ showInfoModal('다운로드 실패', (e&&e.message||String(e))); }
  };
"""

def apply_r127(s, path):
    s = rep(s, LEDGER_OLD, LEDGER_NEW, 1, 'LEDGER')
    s = rep(s, AR_OLD, AR_NEW, 1, 'AR')
    s = rep(s, SUM_OLD, SUM_NEW, 1, 'SUM')
    s = rep(s, OPEN_OLD, OPEN_NEW, 1, 'OPEN')
    s = rep(s, XLS_ANCHOR, XLS_JS + XLS_ANCHOR, 1, 'JS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r127(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r126 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r126 2026-08-21 -->', '<!-- test build r127 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
