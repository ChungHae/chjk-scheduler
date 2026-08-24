# -*- coding: utf-8 -*-
# r131: [전면 재적재 2단계 — 규칙을 화면에서 직접 관리]
#  1) 초기화 범위 변경: 유지 = 입금자명 별칭만.
#     (결제조건·제외거래처도 삭제 — 사용자 결정: 규칙은 나열 후 하나씩 다시 적용)
#  2) 입금 기한(결제조건) 편집: 원장 헤더에서 관리자가 select 로 즉시 설정/해제
#  3) 조정(상계) 추가/삭제: 원장에서 일자·금액(±)·메모 입력, 조정 행에 삭제(휴지통)
#  4) 미수 제외/복원: 원장 헤더 "미수 제외" + 상단 '제외 N곳' 칩 → 목록/복원 패널
#  5) 버그 수정: 원장 엑셀 버튼이 r129 키 체계 변경(rgn|key) 이후 잘못된 키를
#     넘겨 "거래처를 찾지 못했습니다"가 뜨던 문제 (L.key → x.key)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R131 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def cut(s, a, b, new, label):
    if s.count(a) != 1 or s.count(b) != 1: raise SystemExit('R131 FAIL cut %s (a:%d b:%d)' % (label, s.count(a), s.count(b)))
    i = s.index(a); j = s.index(b)
    if j <= i: raise SystemExit('R131 FAIL cut order %s' % label)
    return s[:i] + new + s[j:]

def apply_r131(s, path):
    # ── (1) 상태 + 펼침 초기화 ──
    s = rep(s, "  var _fxRegion='all', _fxQ='', _fxStatusF='all', _fxExp=null, _fxLdFrom='', _fxLdTo='', _fxNotesOpen=false;",
            "  var _fxRegion='all', _fxQ='', _fxStatusF='all', _fxExp=null, _fxLdFrom='', _fxLdTo='', _fxNotesOpen=false, _fxAdjForm=false, _fxExclOpen=false;", 1, 'STATE')
    s = rep(s, "  window.fxExpand = function(key){ _fxExp = (_fxExp===key)?null:key; _fxLdFrom=''; _fxLdTo=''; _fxRenderArBody(); };",
            "  window.fxExpand = function(key){ _fxExp = (_fxExp===key)?null:key; _fxLdFrom=''; _fxLdTo=''; _fxAdjForm=false; _fxRenderArBody(); };", 1, 'EXPAND')

    # ── (2) 초기화: 별칭만 유지 ──
    s = rep(s, """          fxSalesInv=[]; fxPurchInv=[]; fxDeposits=[];
          fxAdjusts=[]; fxOpenings={};""",
            """          fxSalesInv=[]; fxPurchInv=[]; fxDeposits=[];
          fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[];""", 1, 'RESET1')
    s = rep(s, "'매입매출의 거래 자료를 모두 삭제합니다.\\n\\n삭제: 매출·매입 세금계산서, 입금·어음 내역, 조정(상계·예외처리), 기초이월\\n유지: 입금자명 별칭, 결제조건, 제외거래처\\n\\n삭제 후에는 되돌릴 수 없습니다. 계속할까요?'",
            "'매입매출의 거래 자료와 규칙을 모두 삭제합니다.\\n\\n삭제: 매출·매입 세금계산서, 입금·어음 내역, 조정(상계·예외처리), 기초이월, 입금 기한(결제조건), 제외거래처\\n유지: 입금자명 별칭만\\n\\n삭제 후에는 되돌릴 수 없습니다. 계속할까요?'", 1, 'RESET2')
    s = rep(s, "'<b style=\"color:#15803d\">초기화 완료</b> — 계산서·입금·어음·조정·기초이월이 삭제되었습니다. 설정(별칭·결제조건·제외거래처)은 유지됩니다.<br>'",
            "'<b style=\"color:#15803d\">초기화 완료</b> — 거래 자료와 규칙(결제조건·제외거래처·조정)이 삭제되었습니다. 입금자명 별칭만 유지됩니다.<br>'", 1, 'RESET3')
    s = rep(s, "'계산서(매출·매입)·입금·어음·조정(상계/예외)·기초이월을 모두 삭제하고 처음부터 다시 올릴 때 사용합니다. 별칭·결제조건·제외거래처 설정은 유지됩니다.'",
            "'계산서(매출·매입)·입금·어음·조정·기초이월·입금 기한·제외거래처를 모두 삭제하고 처음부터 다시 올릴 때 사용합니다. 입금자명 별칭만 유지됩니다.'", 1, 'RESET4')

    # ── (3) 조정 행에 id 부여 (삭제용) ──
    s = rep(s, "    L.adjs.forEach(function(a){ rows.push({date:a.date, type:'조정', desc:a.memo||'', chg:a.amount}); });",
            "    L.adjs.forEach(function(a){ rows.push({date:a.date, type:'조정', desc:a.memo||'', chg:a.amount, aid:a.id}); });", 1, 'AID')

    # ── (4) 원장 패널 재작성: 입금기한 select + 조정/제외 버튼 + 조정 폼 + 엑셀 키 수정 ──
    LR_NEW = r"""  var _FX_TERMOPTS=['익월초','익월중순','익월말','익익월초','익익월중순','익익월말','익익익월초','익익익월중순','익익익월말'];
  function _fxTermCtl(rgn, name, term){
    if(!_isAdmin()) return '<b style="color:#14305c">'+(term||'기본(익익월말)')+'</b>';
    var o='<option value="">기본(익익월말)</option>'
      + _FX_TERMOPTS.map(function(t){ return '<option value="'+t+'"'+(term===t?' selected':'')+'>'+t+'</option>'; }).join('');
    return '<select class="q-flat" style="border:1px solid #cdd8e6 !important;height:24px;padding:0 4px;width:132px" '
      + 'onclick="event.stopPropagation()" onchange="fxSetTerm(this)" data-rgn="'+esc(rgn)+'" data-name="'+esc(name)+'">'+o+'</select>';
  }
  window.fxSetTerm = function(sel){
    if(!_isAdmin()) return;
    var rgn=sel.dataset.rgn, name=sel.dataset.name, v=sel.value;
    if(v) fxTerms[rgn+'|'+name]=v; else delete fxTerms[rgn+'|'+name];
    _fxSave();
    _fxRenderArBody();
  };
  window.fxAdjToggle = function(){ _fxAdjForm=!_fxAdjForm; _fxRenderArBody(); };
  window.fxAdjSave = function(){
    if(!_isAdmin()) return;
    var x=_fxLedgers(_fxRegion).find(function(e){ return e.key===_fxExp; }); if(!x) return;
    var d=(document.getElementById('fxAdjDate')||{}).value;
    var amt=_fxN((document.getElementById('fxAdjAmt')||{}).value);
    var memo=String((document.getElementById('fxAdjMemo')||{}).value||'').trim();
    if(!d || !amt){ showInfoModal('조정','일자와 금액을 입력하세요. (음수 = 미수 차감/상계, 양수 = 미수 증가)'); return; }
    fxAdjusts.push({ id:'M|'+x.rgn+'|'+(x.vbiz||x.name)+'|'+Date.now(), biz:x.rgn, date:d, vendor:x.name,
                     vbiz:x.vbiz||'', amount:amt, memo:memo||'수동 조정', author:(_authUser&&_authUser.name)||'' });
    _fxAdjForm=false;
    _fxSave();
    _fxRenderArBody();
  };
  window.fxDelAdjust = function(id){
    if(!_isAdmin()) return;
    var a=fxAdjusts.find(function(e){ return e.id===id; }); if(!a) return;
    showConfirmModal('조정 삭제', a.date+' · '+_fxFmt(a.amount)+'원 · '+(a.memo||'')+'\n이 조정을 삭제할까요?', function(){
      fxAdjusts=fxAdjusts.filter(function(e){ return e.id!==id; });
      _fxSave();
      _fxRenderArBody();
    });
  };
  window.fxExcludeVendor = function(){
    if(!_isAdmin()) return;
    var x=_fxLedgers(_fxRegion).find(function(e){ return e.key===_fxExp; }); if(!x) return;
    showConfirmModal('미수 대상 제외', '"'+esc(x.name)+'" ('+x.rgn+') 거래처를 미수 집계에서 제외합니다.\n상단 \'제외\' 칩에서 언제든 복원할 수 있습니다.', function(){
      fxExcluded.push({ biz:x.rgn, vendor:x.name, vbiz:x.vbiz||'', reason:'수동 제외' });
      _fxExp=null;
      _fxSave();
      _fxRenderArBody();
    }, '제외', '#dc2626');
  };
  function _fxExclList(){ return fxExcluded.filter(function(x){ return _fxRegion==='all'||x.biz===_fxRegion; }); }
  window.fxExclToggle = function(){ _fxExclOpen=!_fxExclOpen; _fxRenderArBody(); };
  window.fxRestoreVendor = function(i){
    if(!_isAdmin()) return;
    var t=_fxExclList()[i]; if(!t) return;
    fxExcluded=fxExcluded.filter(function(e){ return e!==t; });
    _fxSave();
    _fxRenderArBody();
  };
  function _fxExclPanelHtml(){
    var l=_fxExclList();
    if(!l.length) return '';
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;white-space:nowrap;vertical-align:middle';
    var rows=l.map(function(e,i){
      return '<tr>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+(_fxRegion==='all'?_fxBizBadge(e.biz):'')+esc(e.vendor)+(e.vbiz?' <span style="font-weight:400;color:#9ca3af;font-size:11px">'+e.vbiz+'</span>':'')+'</td>'
        + '<td style="'+TD+';color:#6b7280">'+esc(e.reason||'')+'</td>'
        + '<td style="'+TD+';text-align:right">'+(_isAdmin()?'<button type="button" class="btn" onclick="fxRestoreVendor('+i+')" style="font-size:11.5px;padding:3px 12px;border:1px solid #5b7ba6;color:#5b7ba6;background:#fff">복원</button>':'')+'</td>'
        + '</tr>';
    }).join('');
    return '<div style="background:#fff;border:1px solid #d6deea;margin-bottom:12px">'
      + '<div style="padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#14305c">미수 제외 거래처 <span style="font-weight:400;color:#8a94a6">— '+l.length+'곳 (미수 집계에서 빠집니다)</span></div>'
      + '<div style="max-height:260px;overflow:auto"><table style="width:100%;border-collapse:collapse"><tbody>'+rows+'</tbody></table></div></div>';
  }
  function _fxLedgerRows(x){
    var L=x.L, term=x.term, rgn=x.rgn;
    var pr=_fxLedgerPeriodRows(L);
    var rows=pr.rows, carry=pr.carry;
    var tDr=0, tCr=0;
    rows.forEach(function(r){ if(r.chg>=0){ tDr+=r.chg; } else { tCr+=-r.chg; } });
    var endBal = rows.length ? rows[rows.length-1].bal : (carry!=null?carry:0);
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;white-space:nowrap';
    var TRASH='<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>';
    var body='';
    if(carry!=null){
      body += '<tr style="background:#fbfcfe">'
        + '<td style="'+TD+';color:#6b7280">'+_fxLdFrom+'</td>'
        + '<td style="'+TD+';text-align:center"><span style="font-weight:700;color:#6b7280">이월</span></td>'
        + '<td style="'+TD+';color:#6b7280">전기이월 (조회기간 이전 합산)</td>'
        + '<td style="'+TD+'"></td><td style="'+TD+'"></td>'
        + '<td style="'+TD+';text-align:right;font-weight:700;color:'+(carry>0?'#1a1a1a':'#9ca3af')+'">'+_fxFmt(carry)+'</td>'
        + '</tr>';
    }
    body += rows.map(function(r){
      var tc = r.type==='계산서'?'#14305c':(r.type==='조정'?'#d97706':(r.type==='기초'?'#6b7280':'#15803d'));
      var del = (r.aid && _isAdmin()) ? ' <button type="button" onclick="event.stopPropagation();fxDelAdjust(\''+String(r.aid).replace(/'/g,'\\\'')+'\')" data-tip="조정 삭제" aria-label="조정 삭제" style="border:none;background:transparent;cursor:pointer;padding:0 2px;vertical-align:-1px">'+TRASH+'</button>' : '';
      return '<tr>'
        + '<td style="'+TD+';color:#6b7280">'+r.date+'</td>'
        + '<td style="'+TD+';text-align:center"><span style="font-weight:700;color:'+tc+'">'+r.type+'</span></td>'
        + '<td style="'+TD+';white-space:normal;word-break:break-all;color:#374151">'+esc(r.desc)+del+'</td>'
        + '<td style="'+TD+';text-align:right;color:#14305c">'+(r.chg>=0?_fxFmt(r.chg):'')+'</td>'
        + '<td style="'+TD+';text-align:right;color:#15803d">'+(r.chg<0?_fxFmt(-r.chg):'')+'</td>'
        + '<td style="'+TD+';text-align:right;font-weight:700;color:'+(r.bal>0?'#1a1a1a':'#9ca3af')+'">'+_fxFmt(r.bal)+'</td>'
        + '</tr>';
    }).join('');
    if(!rows.length && carry==null){
      body += '<tr><td style="'+TD+';text-align:center;color:#b6bec9" colspan="6">조회기간에 거래가 없습니다.</td></tr>';
    }
    body += '<tr style="background:#f4f8fe">'
      + '<td style="'+TD+';font-weight:700;color:#1B3A6B" colspan="3">'+((_fxLdFrom||_fxLdTo)?'기간 합계':'합계')+'</td>'
      + '<td style="'+TD+';text-align:right;font-weight:700;color:#14305c">'+_fxFmt(tDr)+'</td>'
      + '<td style="'+TD+';text-align:right;font-weight:700;color:#15803d">'+_fxFmt(tCr)+'</td>'
      + '<td style="'+TD+';text-align:right;font-weight:700;color:'+(endBal>0?'#1a1a1a':'#9ca3af')+'">'+_fxFmt(endBal)+'</td>'
      + '</tr>';
    var TH='padding:7px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;border-bottom:2px solid #d3dce6;white-space:nowrap';
    var DI='height:24px;box-sizing:border-box;padding:0 6px;border:1px solid #cdd8e6;font-size:11.5px;font-family:inherit;background:#fff;color:#1a1a1a';
    var adminBtns = _isAdmin()
      ? '<button type="button" class="btn" onclick="event.stopPropagation();fxAdjToggle()" style="font-size:11.5px;padding:3px 12px;border:1px solid #d97706;color:#b45309;background:#fff">+ 조정</button>'
        + '<button type="button" class="btn" onclick="event.stopPropagation();fxExcludeVendor()" style="font-size:11.5px;padding:3px 12px;border:1px solid #dc2626;color:#dc2626;background:#fff">미수 제외</button>'
      : '';
    var adjForm = (_fxAdjForm && _isAdmin())
      ? '<div onclick="event.stopPropagation()" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px;padding:9px 12px;background:#fff8ef;border:1px solid #f0d9b8;font-size:12px">'
        + '<b style="color:#b45309">조정 추가</b>'
        + '<input type="date" id="fxAdjDate" value="'+dk(new Date())+'" style="'+DI+'">'
        + '<input type="text" id="fxAdjAmt" placeholder="금액 (음수=상계·차감)" style="'+DI+';width:150px;text-align:right">'
        + '<input type="text" id="fxAdjMemo" placeholder="메모 (예: 상계처리)" style="'+DI+';width:220px" onkeydown="if(event.key===\'Enter\'){event.preventDefault();fxAdjSave();}">'
        + '<button type="button" class="btn" onclick="fxAdjSave()" style="font-size:11.5px;padding:3px 14px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B">저장</button>'
        + '<button type="button" class="btn" onclick="fxAdjToggle()" style="font-size:11.5px;padding:3px 12px;border:1px solid #d6deea;color:#6b7280;background:#fff">취소</button>'
        + '<span style="color:#9ca3af;font-size:11.5px">음수 금액 = 미수 차감(상계·할인), 양수 = 미수 증가</span>'
        + '</div>'
      : '';
    return '<div style="background:#fbfcfe;border-top:1px solid #e3eaf2;padding:12px 14px">'
      + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:12px;color:#6b7280;flex-wrap:wrap">'
      +   '<span onclick="event.stopPropagation()">입금 기한: '+_fxTermCtl(rgn, x.name, term)+'</span>'
      +   '<span style="display:inline-flex;align-items:center;gap:4px">조회기간'
      +     ' <input type="date" value="'+esc(_fxLdFrom)+'" onchange="fxLdFrom(this.value)" onclick="event.stopPropagation()" style="'+DI+'">'
      +     ' ~ <input type="date" value="'+esc(_fxLdTo)+'" onchange="fxLdTo(this.value)" onclick="event.stopPropagation()" style="'+DI+'">'
      +     ((_fxLdFrom||_fxLdTo)?' <button type="button" class="btn" onclick="event.stopPropagation();fxLdReset()" style="font-size:11px;padding:2px 8px;border:1px solid #d6deea;color:#6b7280;background:#fff">전체</button>':'')
      +   '</span>'
      +   '<span style="flex:1"></span>'
      +   adminBtns
      +   '<button type="button" class="btn" onclick="event.stopPropagation();fxLedgerXls(\''+String(x.key).replace(/'/g,'\\\'')+'\')" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#14305c;background:#f4f8fe">원장 엑셀</button>'
      + '</div>'
      + adjForm
      + '<div style="background:#fff;border:1px solid #e3e9f0;max-height:420px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
      + '<thead><tr><th style="'+TH+';text-align:left">일자</th><th style="'+TH+'">구분</th><th style="'+TH+';text-align:left">적요</th><th style="'+TH+';text-align:right">차변 (계산서)</th><th style="'+TH+';text-align:right">대변 (입금)</th><th style="'+TH+';text-align:right">잔액</th></tr></thead>'
      + '<tbody>'+body+'</tbody></table></div></div>';
  }
"""
    s = cut(s, "  function _fxLedgerRows(L, term){", "  var _FX_AGL=", LR_NEW, 'LEDGERROWS')

    # ── (5) 렌더 연결: 호출부·칩·패널 ──
    s = rep(s, "'+_fxLedgerRows(x.L, x.term)+'", "'+_fxLedgerRows(x)+'", 1, 'CALL')
    s = rep(s, "      h+=_fxChip('미수', nMisu+'곳', false)+_fxChip('장기미수', nLong+'곳', false)+_fxChip('거래처', base.length+'곳', false);",
            """      h+=_fxChip('미수', nMisu+'곳', false)+_fxChip('장기미수', nLong+'곳', false)+_fxChip('거래처', base.length+'곳', false);
      var nExcl=_fxExclList().length;
      if(nExcl) h+='<span onclick="fxExclToggle()" style="cursor:pointer" title="클릭하면 제외 목록이 열립니다">'+_fxChip('제외', nExcl+'곳'+(_fxExclOpen?' ▲':' ▼'), false)+'</span>';""", 1, 'CHIP')
    s = rep(s, "    var noteHtml = _fxNotesOpen ? _fxNotesPanelHtml() : '';",
            "    var noteHtml = (_fxNotesOpen ? _fxNotesPanelHtml() : '') + (_fxExclOpen ? _fxExclPanelHtml() : '');", 1, 'PANEL')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r131(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r130 2026-08-22 -->') == 1
            s = s.replace('<!-- test build r130 2026-08-22 -->', '<!-- test build r131 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
