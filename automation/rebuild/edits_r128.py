# -*- coding: utf-8 -*-
# r128: [매입매출 디자인 통일 + 원장 차대변]
#  1) 소 카테고리: 페이지 안 pf-btn 3개 → 상단 .sub-nav 스트립(.file-grp-tab)로 이동
#     (자료실 충해전기/거래처, 견적 견적관리/가격확인과 동일한 자리·스타일)
#  2) 페이지 툴바: 재고/매입처/바로가기와 동일한 q-toolbar inv-toolbar 패턴
#     (inv-flat-label 제목 + q-flat 검색 + 구분선 + pf-btn 사업장 필터 + q-flat select
#      + 메타 + 우측 qic 엑셀 아이콘) + #pageFx 전용 CSS 블록(각진 버튼 포함)
#  3) 거래처 원장: 증감 1열 → ERP 방식 차변(계산서 발행)/대변(입금 회수) 2열 + 합계행.
#     원장 엑셀도 동일하게 차변/대변 열로 변경.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R128 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def cut(s, a, b, new, label):
    if s.count(a) != 1 or s.count(b) != 1: raise SystemExit('R128 FAIL cut %s (a:%d b:%d)' % (label, s.count(a), s.count(b)))
    i = s.index(a); j = s.index(b)
    if j <= i: raise SystemExit('R128 FAIL cut order %s' % label)
    return s[:i] + new + s[j:]

# ── (1) 소 카테고리 스트립 ──
NAV_OLD = """<nav class="sub-nav" id="acctSubNav" style="display:none">
  <button class="sub-tab" data-page="armatch">입출금</button>
  <button class="sub-tab" data-page="fx">매입매출</button>
  <button class="sub-tab" data-page="cardsales">카드매출</button>
</nav>"""
NAV_NEW = NAV_OLD + """
<nav class="sub-nav" id="fxSubNav" style="display:none">
  <button class="file-grp-tab active" data-fxtab="ar" onclick="fxSwitchTab('ar')">미수 현황</button>
  <button class="file-grp-tab" data-fxtab="sum" onclick="fxSwitchTab('sum')">매입·매출 집계</button>
  <button class="file-grp-tab" data-fxtab="up" onclick="fxSwitchTab('up')">자료 업로드</button>
</nav>"""

SW_OLD = """    var _acctnav=document.getElementById('acctSubNav'); if(_acctnav) _acctnav.style.display = _ACCT.indexOf(page)>=0 ? 'flex' : 'none';"""
SW_NEW = SW_OLD + """
    var _fxnav=document.getElementById('fxSubNav'); if(_fxnav) _fxnav.style.display = (page==='fx') ? 'flex' : 'none';"""

# ── (2) pageFx HTML: 표준 툴바 골격 + 전용 CSS ──
PAGE_OLD = """  <!-- ─── 매입매출(신) 페이지 (r122) ─────────────────────── -->
  <div id="pageFx" class="page-section">
    <div class="q-toolbar" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <span style="font-size:12.5px;font-weight:700;color:#14305c;white-space:nowrap">매입매출</span>
      <span class="inv-flat-div"></span>
      <div id="fxSubTabs" style="display:flex;gap:4px">
        <button type="button" class="btn pf-btn" data-fxtab="ar" onclick="fxSwitchTab('ar')" style="font-size:11.5px;padding:3px 11px">미수 현황</button>
        <button type="button" class="btn pf-btn" data-fxtab="sum" onclick="fxSwitchTab('sum')" style="font-size:11.5px;padding:3px 11px">매입·매출 집계</button>
        <button type="button" class="btn pf-btn" data-fxtab="up" onclick="fxSwitchTab('up')" style="font-size:11.5px;padding:3px 11px">자료 업로드</button>
      </div>
      <span id="fxMeta" style="font-size:11px;color:#9ca3af;white-space:nowrap;margin-left:6px"></span>
      <span style="flex:1"></span>
    </div>
    <div id="fxBody" style="margin-top:14px"></div>
  </div>"""

PAGE_NEW = """  <!-- ─── 매입매출(신) 페이지 (r122, r128 디자인 통일: 재고/매입처 툴바 패턴) ─── -->
  <div id="pageFx" class="page-section">
    <style>
      /* r128: 재고(#pageInventory)·매입처(#pagePurchase) 툴바 규칙과 동일 */
      #pageFx .inv-toolbar { display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin: calc(var(--mpy)*-1) calc(var(--mpx)*-1) 14px; min-height:var(--snh,36px); padding:4px var(--mpx); background:#fff; border:0; border-bottom:1px solid #e5e5e5; box-shadow:0 2px 6px rgba(15,23,42,.06); box-sizing:border-box; }
      #pageFx .inv-flat-label { font-size:12.5px; font-weight:700; color:#14305c; white-space:nowrap; flex-shrink:0; }
      #pageFx .inv-flat-div { width:1px; height:18px; background:#e5e5e5; flex-shrink:0; margin:0 4px; }
      #pageFx .q-flat { box-sizing:border-box; height:26px; padding:4px 6px; margin:0; border:none !important; border-radius:0 !important; background:transparent; outline:none; font-size:13px; font-family:inherit; color:#14305c; }
      #pageFx input.q-flat { width:300px; max-width:100%; }
      #pageFx .q-flat:hover { background:rgba(27,58,107,.045); }
      #pageFx .q-flat:focus { background:#f2f4f7; }
      #pageFx .q-flat::placeholder { color:#aab4c2; }
      #pageFx select.q-flat { background:#fff; color:#1a1a1a; cursor:pointer; }
      #pageFx .btn { border-radius:0 !important; }
      #pageFx .inv-toolbar .qic { width:26px !important; min-width:26px; height:26px; border-radius:6px !important; flex:0 0 auto; }
      #pageFx .inv-toolbar .qic svg { width:15px; height:15px; }
      /* 우측 끝 엑셀 버튼 툴팁이 화면 밖으로 나가지 않게 (카드매출과 동일 방식) */
      #pageFx #fxExcelBtn[data-tip]:hover::after, #pageFx #fxExcelBtn[data-tip]:focus-visible::after { left:auto; right:0; transform:none; }
    </style>
    <div class="q-toolbar inv-toolbar" id="fxToolbar"></div>
    <div id="fxBody"></div>
  </div>"""

# ── (3) 원장: 차변/대변 2열 + 합계행 ──
LEDGER_A = "  function _fxLedgerRows(L, term){"
LEDGER_B = "  function _fxRenderArBody(){"
LEDGER_NEW = r"""  function _fxLedgerRows(L, term){
    var rows=[];
    if(L.opening) rows.push({date:L.openDate||'', type:'기초', desc:'기초 이월', chg:L.opening});
    L.invs.forEach(function(e){ rows.push({date:e.date, type:'계산서', desc:'세금계산서 (공급가 '+_fxFmt(e.supply)+' + 세액 '+_fxFmt(e.tax)+')'+(e.note?' · '+esc(e.note):''), chg:e.total}); });
    L.deps.forEach(function(e){ rows.push({date:e.date, type:(e.kind==='note'?'어음':'입금'), desc:esc((e.bank||'')+(e.bank?' · ':'')+(e.payer||'')), chg:-e.amount}); });
    L.adjs.forEach(function(a){ rows.push({date:a.date, type:'조정', desc:esc(a.memo||''), chg:a.amount}); });
    rows.sort(function(a,b){ return a.date<b.date?-1:a.date>b.date?1:(a.chg>0?-1:1); });
    var bal=0, tDr=0, tCr=0;
    rows.forEach(function(r){ bal+=r.chg; r.bal=bal; if(r.chg>=0){ tDr+=r.chg; } else { tCr+=-r.chg; } });
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;white-space:nowrap';
    var body=rows.map(function(r){
      var tc = r.type==='계산서'?'#14305c':(r.type==='조정'?'#d97706':(r.type==='기초'?'#6b7280':'#15803d'));
      return '<tr>'
        + '<td style="'+TD+';color:#6b7280">'+r.date+'</td>'
        + '<td style="'+TD+';text-align:center"><span style="font-weight:700;color:'+tc+'">'+r.type+'</span></td>'
        + '<td style="'+TD+';white-space:normal;word-break:break-all;color:#374151">'+r.desc+'</td>'
        + '<td style="'+TD+';text-align:right;color:#14305c">'+(r.chg>=0?_fxFmt(r.chg):'')+'</td>'
        + '<td style="'+TD+';text-align:right;color:#15803d">'+(r.chg<0?_fxFmt(-r.chg):'')+'</td>'
        + '<td style="'+TD+';text-align:right;font-weight:700;color:'+(r.bal>0?'#1a1a1a':'#9ca3af')+'">'+_fxFmt(r.bal)+'</td>'
        + '</tr>';
    }).join('');
    body += '<tr style="background:#f4f8fe">'
      + '<td style="'+TD+';font-weight:700;color:#1B3A6B" colspan="3">합계</td>'
      + '<td style="'+TD+';text-align:right;font-weight:700;color:#14305c">'+_fxFmt(tDr)+'</td>'
      + '<td style="'+TD+';text-align:right;font-weight:700;color:#15803d">'+_fxFmt(tCr)+'</td>'
      + '<td style="'+TD+';text-align:right;font-weight:700;color:'+(bal>0?'#1a1a1a':'#9ca3af')+'">'+_fxFmt(bal)+'</td>'
      + '</tr>';
    var TH='padding:7px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;border-bottom:2px solid #d3dce6;white-space:nowrap';
    return '<div style="background:#fbfcfe;border-top:1px solid #e3eaf2;padding:12px 14px">'
      + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:12px;color:#6b7280">'
      +   '<span>결제조건: <b style="color:#14305c">'+(term||'기본(익익월말)')+'</b></span>'
      +   '<span style="font-size:11.5px;color:#9ca3af">차변 = 계산서 발행(채권 증가) · 대변 = 입금·어음 회수(채권 감소)</span>'
      +   '<span style="flex:1"></span>'
      +   '<button type="button" class="btn" onclick="event.stopPropagation();fxLedgerXls(\''+String(L.key).replace(/'/g,'\\\'')+'\')" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#14305c;background:#f4f8fe">원장 엑셀</button>'
      + '</div>'
      + '<div style="background:#fff;border:1px solid #e3e9f0;max-height:420px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
      + '<thead><tr><th style="'+TH+';text-align:left">일자</th><th style="'+TH+'">구분</th><th style="'+TH+';text-align:left">적요</th><th style="'+TH+';text-align:right">차변 (계산서)</th><th style="'+TH+';text-align:right">대변 (입금)</th><th style="'+TH+';text-align:right">잔액</th></tr></thead>'
      + '<tbody>'+body+'</tbody></table></div></div>';
  }
"""

# ── (4) renderFxPage: 탭별 표준 툴바 + 본문 ──
RENDER_A = "  function renderFxPage(){"
RENDER_B = "  // ── 누적본 zip 이관 ──"
RENDER_NEW = r"""  function _fxRegionBtnsHtml(){
    return '<div id="fxRegionBtns" style="display:flex;gap:4px">'
      + ['서울','화성'].map(function(b){ return '<button type="button" class="btn pf-btn'+(_fxRegion===b?' active':'')+'" onclick="fxSetRegion(\''+b+'\')" style="font-size:11.5px;padding:3px 11px">'+b+'</button>'; }).join('')
      + '</div>';
  }
  var _FX_DL_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12"/><path d="M7.5 11.5 12 16l4.5-4.5"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/></svg>';
  function renderFxPage(){
    var tb = document.getElementById('fxToolbar'), body = document.getElementById('fxBody');
    if(!tb || !body) return;
    var nv=document.getElementById('fxSubNav');
    if(nv) nv.querySelectorAll('.file-grp-tab').forEach(function(b){ b.classList.toggle('active', b.dataset.fxtab===_fxTab); });
    var metaSpan='<span id="fxMeta" style="font-size:11px;color:#9ca3af;white-space:nowrap"></span>';
    var _empty = function(msg){ return '<div style="text-align:center;padding:56px 20px;color:#b6bec9;font-size:13px;line-height:1.9">'+msg+'</div>'; };
    var _loading='<div style="text-align:center;padding:40px;color:#9ca3af;font-size:13px">자료 불러오는 중…</div>';
    var _xlsBtn=function(fn){ return '<button type="button" class="qic" id="fxExcelBtn" onclick="'+fn+'()" data-tip="엑셀 다운로드" aria-label="엑셀 다운로드" style="border-color:#1B3A6B;color:#1B3A6B">'+_FX_DL_SVG+'</button>'; };
    if(_fxTab==='ar'){
      tb.innerHTML =
        '<span class="inv-flat-label">미수 현황</span>'
        + '<input type="text" class="q-flat" placeholder="거래처명/사업자번호 검색…" value="'+esc(_fxQ)+'" oninput="fxSearchInput(this.value)" autocomplete="off">'
        + '<span class="inv-flat-div"></span>'
        + _fxRegionBtnsHtml()
        + '<select class="q-flat" onchange="fxSetStatusF(this.value)" style="width:110px;flex:0 0 auto">'
        +   [['all','전체 상태'],['미수','미수(장기 포함)'],['장기미수','장기미수'],['진행','진행'],['완납','완납']].map(function(o){ return '<option value="'+o[0]+'"'+(_fxStatusF===o[0]?' selected':'')+'>'+o[1]+'</option>'; }).join('')
        + '</select>'
        + metaSpan
        + '<span style="flex:1"></span>'
        + _xlsBtn('fxArXls');
      body.innerHTML = _loading;
      _fxEnsureData().then(function(){
        if(_fxTab!=='ar') return;
        _fxMetaRefresh();
        if(!fxSalesInv.length && !fxDeposits.length){
          body.innerHTML = _empty('자료가 아직 없습니다.<br><b style="color:#5b7ba6">자료 업로드</b> 탭에서 기존 앱 누적본(zip)을 가져오거나 계산서·입금 자료를 올려주세요.');
          return;
        }
        body.innerHTML =
          '<div id="fxArChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px"></div>'
          + '<div id="fxArList"></div>';
        _fxRenderArBody();
      });
      return;
    }
    if(_fxTab==='sum'){
      tb.innerHTML =
        '<span class="inv-flat-label">매입·매출 집계</span>'
        + '<span class="inv-flat-div"></span>'
        + _fxRegionBtnsHtml()
        + '<select id="fxSumYearSel" class="q-flat" onchange="fxSumYear(this.value)" style="width:88px;flex:0 0 auto"></select>'
        + '<div id="fxSumModeBtns" style="display:flex;gap:4px">'
        +   '<button type="button" class="btn pf-btn" data-m="month" onclick="fxSumMode(\'month\')" style="font-size:11.5px;padding:3px 11px">월별</button>'
        +   '<button type="button" class="btn pf-btn" data-m="vendor" onclick="fxSumMode(\'vendor\')" style="font-size:11.5px;padding:3px 11px">거래처별</button>'
        + '</div>'
        + '<input type="text" id="fxSumQ" class="q-flat" placeholder="거래처 검색…" value="'+esc(_fxSumQ)+'" oninput="fxSumSearch(this.value)" autocomplete="off" style="width:200px;display:none">'
        + metaSpan
        + '<span style="flex:1"></span>'
        + _xlsBtn('fxSumXls');
      body.innerHTML = _loading;
      _fxEnsureData().then(function(){
        if(_fxTab!=='sum') return;
        _fxMetaRefresh();
        if(!fxSalesInv.length && !fxPurchInv.length){
          body.innerHTML = _empty('자료가 아직 없습니다.<br><b style="color:#5b7ba6">자료 업로드</b> 탭에서 계산서 자료를 올려주세요.');
          return;
        }
        body.innerHTML = '<div id="fxSumBody"></div>';
        _fxRenderSumBody();
      });
      return;
    }
    // 자료 업로드 탭
    tb.innerHTML =
      '<span class="inv-flat-label">자료 업로드</span>'
      + metaSpan
      + '<span style="flex:1"></span>';
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
                + '<select id="fxUpBankBiz" class="q-flat" style="width:76px;border:1px solid #d6deea !important">'
                + '<option value="서울">서울</option><option value="화성">화성</option></select>'
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
    });
  }
"""

# ── (5) 원장 엑셀: 차변/대변 열 ──
XLS_A = "  // 거래처 원장 엑셀"
XLS_B = "  // 미수 현황 목록 엑셀 (현재 필터 반영)"
XLS_NEW = r"""  // 거래처 원장 엑셀 (차변/대변)
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
      var bal=0, tDr=0, tCr=0;
      rows.forEach(function(r){ bal+=r.chg; r.bal=bal; if(r.chg>=0){ tDr+=r.chg; } else { tCr+=-r.chg; } });
      var aoa=[
        ['거래처', lg.name, '사업자번호', lg.vbiz||'-'],
        ['사업장', _fxRegion, '결제조건', lg.term||'기본(익익월말)'],
        ['계산서 누계', lg.invSum, '입금·조정 누계', lg.depSum],
        ['미수 잔액', lg.bal, '작성일', dk(new Date())],
        [],
        ['일자','구분','적요','차변','대변','잔액']
      ];
      rows.forEach(function(r){ aoa.push([r.date, r.type, r.desc, r.chg>=0?r.chg:null, r.chg<0?-r.chg:null, r.bal]); });
      aoa.push(['합계','','',tDr,tCr,bal]);
      var ws=XLSX.utils.aoa_to_sheet(aoa);
      ws['!cols']=[{wch:12},{wch:8},{wch:46},{wch:14},{wch:14},{wch:14}];
      _fxXlsStyle(ws, 5, [3,4,5], [2]);
      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, '원장');
      XLSX.writeFile(wb, _fxSafeName(lg.name)+' 원장_'+_fxRegion+'_'+_fxDs()+'.xlsx');
    }catch(e){ showInfoModal('다운로드 실패', (e&&e.message||String(e))); }
  };
"""

def apply_r128(s, path):
    s = rep(s, NAV_OLD, NAV_NEW, 1, 'NAV')
    s = rep(s, SW_OLD, SW_NEW, 1, 'SWITCH')
    s = rep(s, PAGE_OLD, PAGE_NEW, 1, 'PAGE')
    s = cut(s, LEDGER_A, LEDGER_B, LEDGER_NEW, 'LEDGER')
    s = cut(s, RENDER_A, RENDER_B, RENDER_NEW, 'RENDER')
    s = cut(s, XLS_A, XLS_B, XLS_NEW, 'XLS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r128(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r127 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r127 2026-08-21 -->', '<!-- test build r128 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
