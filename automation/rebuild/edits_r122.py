# -*- coding: utf-8 -*-
# r122: [매입매출 1단계] 회계 > "매입매출" 새 탭 뼈대.
#       기존 입출금 탭은 그대로 두고 나란히 신설. 이번 단계 내용:
#       - 하위 화면 3개 골격: 미수 현황(거래처 원장) / 매입·매출 집계 / 자료 업로드
#       - 데이터 저장소 6종 신설 + Firebase 동기화(선언·로드·저장) 연결
#       - 다음 단계에서 엑셀 파서와 원장 계산을 붙임

# (old, new, expected_count)
R122_EDITS = [

# (1) 회계 하위 탭에 매입매출 추가 (입출금 다음)
("""  <button class="sub-tab" data-page="armatch">입출금</button>""",
 """  <button class="sub-tab" data-page="armatch">입출금</button>
  <button class="sub-tab" data-page="fx">매입매출</button>""", 1),

# (2) 페이지 HTML (재고 페이지 직전)
("""  <!-- ─── 재고 페이지 ─────────────────────────────────── -->""",
 """  <!-- ─── 매입매출(신) 페이지 (r122) ─────────────────────── -->
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
  </div>

  <!-- ─── 재고 페이지 ─────────────────────────────────── -->""", 1),

# (3) 데이터 선언 (기존 상태 선언부에 이어서)
("""  let assignComments = load('sched_assign_comments') ?? {}; // { assignId: [{id,authorId,authorName,text,ts}] }""",
 """  let assignComments = load('sched_assign_comments') ?? {}; // { assignId: [{id,authorId,authorName,text,ts}] }
  // ─── 매입매출(신) 데이터 (r122) ───
  let fxSalesInv  = load('sched_fx_sales')    ?? [];  // 매출 세금계산서 [{id,date,vendor,supply,tax,total,no}]
  let fxPurchInv  = load('sched_fx_purch')    ?? [];  // 매입 세금계산서 (구조 동일)
  let fxDeposits  = load('sched_fx_deposits') ?? [];  // 입금 [{id,date,amount,payer,vendor}]
  let fxAlias     = load('sched_fx_alias')    ?? {};  // { 입금자명: 거래처명 }
  let fxOpenings  = load('sched_fx_openings') ?? {};  // { 거래처명: {amount, asOf} } 기초이월
  let fxAdjusts   = load('sched_fx_adjusts')  ?? [];  // 조정 [{id,date,vendor,amount,memo,author}]
  let fxTerms     = load('sched_fx_terms')    ?? {};  // { 사업장|거래처: 결제조건 } 미수판정 기준
  let fxExcluded  = load('sched_fx_excluded') ?? [];  // 제외 거래처 [{biz,vendor,vbiz,reason}]""", 1),

# (4) doFbSave 페이로드에 키 추가
("""        sched_proj_memos: projMemos,""",
 """        sched_proj_memos: projMemos,
        sched_fx_sales: fxSalesInv,
        sched_fx_purch: fxPurchInv,
        sched_fx_deposits: fxDeposits,
        sched_fx_alias: fxAlias,
        sched_fx_openings: fxOpenings,
        sched_fx_adjusts: fxAdjusts,
        sched_fx_terms: fxTerms,
        sched_fx_excluded: fxExcluded,""", 1),

# (5) reloadState 로드 추가
("""    projMemos        = _pmNormList(load('sched_proj_memos') ?? []);""",
 """    projMemos        = _pmNormList(load('sched_proj_memos') ?? []);
    fxSalesInv       = load('sched_fx_sales')    ?? [];
    fxPurchInv       = load('sched_fx_purch')    ?? [];
    fxDeposits       = load('sched_fx_deposits') ?? [];
    fxAlias          = load('sched_fx_alias')    ?? {};
    fxOpenings       = load('sched_fx_openings') ?? {};
    fxAdjusts        = load('sched_fx_adjusts')  ?? [];
    fxTerms          = load('sched_fx_terms')    ?? {};
    fxExcluded       = load('sched_fx_excluded') ?? [];""", 1),

# (6) switchPage 연결
("""    var _ACCT=['armatch','cardsales'];""",
 """    var _ACCT=['armatch','fx','cardsales'];""", 1),
("""armatch:'pageArmatch',""",
 """armatch:'pageArmatch', fx:'pageFx',""", 1),
("""    if (page === 'armatch'){ if(typeof loadMisuSummary==='function') loadMisuSummary(); }""",
 """    if (page === 'armatch'){ if(typeof loadMisuSummary==='function') loadMisuSummary(); }
    if (page === 'fx'){ if(typeof renderFxPage==='function') renderFxPage(); }""", 1),

# (7) 렌더러 골격 (parseExcelDate 앞에 삽입)
("""  function parseExcelDate(excelDate) {""",
 """  // ─── 매입매출(신) 페이지 (r122 골격) ──────────────────
  var _fxTab = 'ar';
  function _fxSave(){
    save('sched_fx_sales', fxSalesInv);
    save('sched_fx_purch', fxPurchInv);
    save('sched_fx_deposits', fxDeposits);
    save('sched_fx_alias', fxAlias);
    save('sched_fx_openings', fxOpenings);
    save('sched_fx_adjusts', fxAdjusts);
    save('sched_fx_terms', fxTerms);
    save('sched_fx_excluded', fxExcluded);
    localStorage.setItem('sched_local_ts', Date.now().toString());
    try{ debouncedFbSave(); }catch(_e){}
  }
  window.fxSwitchTab = function(t){ _fxTab = t; renderFxPage(); };
  function _fxCounts(){
    return { s: fxSalesInv.length, p: fxPurchInv.length, d: fxDeposits.length,
             o: Object.keys(fxOpenings).length, a: fxAdjusts.length };
  }
  function renderFxPage(){
    var body = document.getElementById('fxBody'); if(!body) return;
    document.querySelectorAll('#fxSubTabs .pf-btn').forEach(function(b){ b.classList.toggle('active', b.dataset.fxtab===_fxTab); });
    var c = _fxCounts();
    var meta = document.getElementById('fxMeta');
    if(meta) meta.textContent = (c.s||c.p||c.d) ? ('매출 '+c.s+'건 · 매입 '+c.p+'건 · 입금 '+c.d+'건') : '';
    var _empty = function(msg){ return '<div style="text-align:center;padding:56px 20px;color:#b6bec9;font-size:13px;line-height:1.9">'+msg+'</div>'; };
    if(_fxTab==='ar'){
      body.innerHTML = _empty('거래처별 미수 현황이 여기에 표시됩니다.<br>먼저 <b style="color:#5b7ba6">자료 업로드</b>에서 계산서·입금 자료를 올려주세요.<br><span style="font-size:12px">잔액 = 기초이월 + 매출 계산서 − 입금 ± 조정 (ERP 방식)</span>');
    } else if(_fxTab==='sum'){
      body.innerHTML = _empty('세금계산서 기준 월별·거래처별 매입·매출 집계가 여기에 표시됩니다.');
    } else {
      body.innerHTML =
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;max-width:900px">'
        + [['홈택스 매출 계산서','fxUpSales','매출 세금계산서 목록 엑셀'],
           ['홈택스 매입 계산서','fxUpPurch','매입 세금계산서 목록 엑셀'],
           ['은행 입금 내역','fxUpBank','은행 거래내역 엑셀 (입금 추출)'],
           ['기존 앱 누적본 가져오기','fxUpLegacy','입출금 앱의 누적자료 zip/엑셀 (최초 1회)']]
          .map(function(x){
            return '<div style="background:#fff;border:1px solid #d6deea;padding:16px 18px">'
              + '<div style="font-size:13px;font-weight:700;color:#14305c;margin-bottom:4px">'+x[0]+'</div>'
              + '<div style="font-size:11.5px;color:#8a94a6;margin-bottom:10px">'+x[2]+'</div>'
              + '<button type="button" class="btn" data-fxup="'+x[1]+'" onclick="fxUploadStub(this.dataset.fxup)" style="font-size:12px;padding:5px 14px;border:1px solid #aac4e6;color:#14305c;background:#f4f8fe">파일 선택…</button>'
              + '</div>';
          }).join('')
        + '</div>'
        + '<div style="margin-top:14px;font-size:11.5px;color:#9ca3af">※ 파서 연결 전 골격 화면입니다 — 다음 단계에서 실제 업로드가 동작합니다.</div>';
    }
  }
  window.fxUploadStub = function(kind){
    showInfoModal('매입매출', '업로드 기능은 다음 단계에서 연결됩니다. (' + kind + ')');
  };
  function parseExcelDate(excelDate) {""", 1),
]

def apply_r122(s, path):
    for i,(old,new,exp) in enumerate(R122_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R122 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r122(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r121 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r121 2026-08-21 -->', '<!-- test build r122 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
