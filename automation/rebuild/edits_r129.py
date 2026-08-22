# -*- coding: utf-8 -*-
# r129: [매입매출 확장 5종]
#  1) 사업장 필터에 "전체" 추가 (서울+화성 통합, 거래처 옆 사업장 배지) — 기본값 전체
#  2) 표 가로 전체 사용 (업로드 결과/미배정 패널 max-width 제거)
#  3) 원장 기간 조회: 시작~종료 date 입력, 기간 이전은 "전기이월" 한 줄 합산 (ERP 방식)
#  4) 채권 연령분석: 미수 잔액을 만기 기준 미도래/1~30/31~60/61~90/90+ 구간 분해
#     — 상단 칩 + 거래처 테이블 구간 열 + 엑셀 포함
#  5) 어음 만기 관리: 파서에 만기일(due) 저장(재업로드 시 기존 어음도 채움) +
#     미수 현황 상단 어음 칩 클릭 → 만기일순 어음 목록 패널

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R129 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def cut(s, a, b, new, label):
    if s.count(a) != 1 or s.count(b) != 1: raise SystemExit('R129 FAIL cut %s (a:%d b:%d)' % (label, s.count(a), s.count(b)))
    i = s.index(a); j = s.index(b)
    if j <= i: raise SystemExit('R129 FAIL cut order %s' % label)
    return s[:i] + new + s[j:]

def apply_r129(s, path):
    # ── (1) 상태 변수: 기본 사업장 '전체' + 기간/어음 상태 ──
    s = rep(s, "  var _fxRegion='서울', _fxQ='', _fxStatusF='all', _fxExp=null;",
            "  var _fxRegion='all', _fxQ='', _fxStatusF='all', _fxExp=null, _fxLdFrom='', _fxLdTo='', _fxNotesOpen=false;", 1, 'STATE')

    # fxExpand: 펼침 대상 바뀌면 기간 초기화 + 기간/어음 핸들러 추가
    s = rep(s, "  window.fxExpand = function(key){ _fxExp = (_fxExp===key)?null:key; _fxRenderArBody(); };",
            """  window.fxExpand = function(key){ _fxExp = (_fxExp===key)?null:key; _fxLdFrom=''; _fxLdTo=''; _fxRenderArBody(); };
  window.fxLdFrom = function(v){ _fxLdFrom=String(v||''); _fxRenderArBody(); };
  window.fxLdTo = function(v){ _fxLdTo=String(v||''); _fxRenderArBody(); };
  window.fxLdReset = function(){ _fxLdFrom=''; _fxLdTo=''; _fxRenderArBody(); };
  window.fxNotesToggle = function(){ _fxNotesOpen=!_fxNotesOpen; _fxRenderArBody(); };""", 1, 'EXPAND')

    # ── 사업장 필터: 전체/서울/화성 ──
    s = rep(s, """  function _fxRegionBtnsHtml(){
    return '<div id="fxRegionBtns" style="display:flex;gap:4px">'
      + ['서울','화성'].map(function(b){ return '<button type="button" class="btn pf-btn'+(_fxRegion===b?' active':'')+'" onclick="fxSetRegion(\\''+b+'\\')" style="font-size:11.5px;padding:3px 11px">'+b+'</button>'; }).join('')
      + '</div>';
  }""",
            """  function _fxRegionBtnsHtml(){
    return '<div id="fxRegionBtns" style="display:flex;gap:4px">'
      + [['all','전체'],['서울','서울'],['화성','화성']].map(function(b){ return '<button type="button" class="btn pf-btn'+(_fxRegion===b[0]?' active':'')+'" onclick="fxSetRegion(\\''+b[0]+'\\')" style="font-size:11.5px;padding:3px 11px">'+b[1]+'</button>'; }).join('')
      + '</div>';
  }
  function _fxRegionLabel(){ return _fxRegion==='all' ? '전체' : _fxRegion; }
  function _fxBizBadge(b){ return '<span style="font-size:10.5px;color:#5b7ba6;border:1px solid #cdd8e6;padding:0 4px;margin-right:6px;vertical-align:1px">'+b+'</span>'; }""", 1, 'REGIONBTN')

    # ── 집계: 전체 지원 (연도·매출·매입 필터) ──
    s = rep(s, "    fxSalesInv.concat(fxPurchInv).forEach(function(e){ if(e.biz===_fxRegion && e.date) ys[e.date.slice(0,4)]=1; });",
            "    fxSalesInv.concat(fxPurchInv).forEach(function(e){ if((_fxRegion==='all'||e.biz===_fxRegion) && e.date) ys[e.date.slice(0,4)]=1; });", 1, 'YEARS')
    s = rep(s, "    var sv=fxSalesInv.filter(function(e){ return e.biz===_fxRegion && e.date && e.date.slice(0,4)===_fxSumYear; });",
            "    var sv=fxSalesInv.filter(function(e){ return (_fxRegion==='all'||e.biz===_fxRegion) && e.date && e.date.slice(0,4)===_fxSumYear; });", 1, 'SV1')
    s = rep(s, "    var pv=fxPurchInv.filter(function(e){ return e.biz===_fxRegion && e.date && e.date.slice(0,4)===_fxSumYear; });",
            "    var pv=fxPurchInv.filter(function(e){ return (_fxRegion==='all'||e.biz===_fxRegion) && e.date && e.date.slice(0,4)===_fxSumYear; });", 1, 'PV1')
    # 거래처별 slot: 전체 모드에서 사업장별로 분리 + b 저장 (렌더용 4칸 들여쓰기)
    s = rep(s, "\n    function vslot(e){ var k=(e.vbiz&&/\\d{3}-\\d{2}-\\d{5}/.test(e.vbiz))?e.vbiz:('N|'+e.vendor); if(!V[k]) V[k]={name:e.vendor, vbiz:e.vbiz||'', sc:0, stt:0, pc:0, ptt:0}; if(e.vendor) V[k].name=e.vendor; return V[k]; }",
            "\n    function vslot(e){ var k=(_fxRegion==='all'?(e.biz+'|'):'')+((e.vbiz&&/\\d{3}-\\d{2}-\\d{5}/.test(e.vbiz))?e.vbiz:('N|'+e.vendor)); if(!V[k]) V[k]={name:e.vendor, vbiz:e.vbiz||'', b:e.biz, sc:0, stt:0, pc:0, ptt:0}; if(e.vendor) V[k].name=e.vendor; return V[k]; }", 1, 'VSLOT1')
    # 거래처별 이름 칸: 전체 모드 배지
    s = rep(s, """        + '<td style="'+TD+';text-align:left;font-weight:700;color:#14305c;overflow:hidden;text-overflow:ellipsis">'+esc(x.name)+(x.vbiz?' <span style="font-weight:400;color:#9ca3af;font-size:11px">'+x.vbiz+'</span>':'')+'</td>'""",
            """        + '<td style="'+TD+';text-align:left;font-weight:700;color:#14305c;overflow:hidden;text-overflow:ellipsis">'+(_fxRegion==='all'&&x.b?_fxBizBadge(x.b):'')+esc(x.name)+(x.vbiz?' <span style="font-weight:400;color:#9ca3af;font-size:11px">'+x.vbiz+'</span>':'')+'</td>'""", 1, 'VNAME')

    # ── 원장 구성: 단일 사업장 로직 → _fxLedgersOne + 전체 래퍼 + 연령분석 ──
    LG_NEW = r"""  function _fxLedgersOne(region){
    var map={};
    function slot(vbiz, name){
      var key = (vbiz && /\d{3}-\d{2}-\d{5}/.test(vbiz)) ? vbiz : ('N|'+name);
      if(!map[key]) map[key] = { key:key, name:name, vbiz:(vbiz||''), invs:[], deps:[], adjs:[], opening:0, openDate:null };
      if(name && (!map[key].name || map[key].name==='')) map[key].name=name;
      return map[key];
    }
    fxSalesInv.forEach(function(e){ if(e.biz===region) slot(e.vbiz, e.vendor).invs.push(e); });
    fxDeposits.forEach(function(e){ if(e.biz===region && e.vendor && !e.excluded) slot(e.vbiz, e.vendor).deps.push(e); });
    fxAdjusts.forEach(function(a){ if(a.biz===region) slot(a.vbiz, a.vendor).adjs.push(a); });
    Object.keys(fxOpenings).forEach(function(k){
      var p=k.split('|'); if(p[0]!==region) return;
      var o=fxOpenings[k]||{};
      var target=null;
      Object.keys(map).forEach(function(mk){ if(!target && map[mk].name===p[1]) target=map[mk]; });
      var sl = target || slot('', p[1]);
      sl.opening=Number(o.amount)||0; sl.openDate=o.asOf||null;
    });
    var excl={}; fxExcluded.forEach(function(x){ if(x.biz===region){ excl[x.vbiz||'']=1; excl['N:'+x.vendor]=1; } });
    var today=dk(new Date());
    var out=[];
    Object.keys(map).forEach(function(k){
      var L=map[k];
      if(excl[L.vbiz] || excl['N:'+L.name]) return;
      var term = fxTerms[region+'|'+L.name] || '';
      // 채무(계산서·기초·양수조정) / 변제(입금·음수조정) FIFO
      var obls=[];
      if(L.opening) obls.push({date:L.openDate||'0000-00-00', amt:L.opening, due:_fxDue(L.openDate||today, term)});
      L.invs.forEach(function(e){ obls.push({date:e.date, amt:e.total, due:_fxDue(e.date, term)}); });
      L.adjs.forEach(function(a){ if(a.amount>0) obls.push({date:a.date, amt:a.amount, due:_fxDue(a.date, term)}); });
      obls.sort(function(a,b){ return a.date<b.date?-1:a.date>b.date?1:0; });
      var credit = L.deps.reduce(function(s,e){ return s+(e.amount||0); },0)
                 + L.adjs.reduce(function(s,a){ return s+(a.amount<0?-a.amount:0); },0);
      var creditTotal = credit;
      var unpaid=[];
      obls.forEach(function(o){
        if(credit>=o.amt){ credit-=o.amt; }
        else { unpaid.push({date:o.date, due:o.due, amt:o.amt-credit}); credit=0; }
      });
      var invSum=L.invs.reduce(function(s,e){ return s+(e.total||0); },0);
      var oblSum=obls.reduce(function(s,o){ return s+o.amt; },0);
      var bal=oblSum-creditTotal;
      var over=0;
      var ag=[0,0,0,0,0];  // 연령: 미도래 / 1~30 / 31~60 / 61~90 / 90+
      unpaid.forEach(function(u){
        var dd=Math.floor((new Date(today+'T12:00:00')-new Date(u.due+'T12:00:00'))/86400000);
        if(dd>over) over=dd;
        if(dd<=0) ag[0]+=u.amt; else if(dd<=30) ag[1]+=u.amt; else if(dd<=60) ag[2]+=u.amt; else if(dd<=90) ag[3]+=u.amt; else ag[4]+=u.amt;
      });
      var st = bal<=0 ? '완납' : (over<=0 ? '진행' : (over>90 ? '장기미수' : '미수'));
      var lastInv = L.invs.length ? L.invs.reduce(function(a,e){ return e.date>a?e.date:a; },'') : '';
      var lastDep = L.deps.length ? L.deps.reduce(function(a,e){ return e.date>a?e.date:a; },'') : '';
      out.push({ key:region+'|'+k, rgn:region, name:L.name, vbiz:L.vbiz, bal:bal, invSum:invSum, depSum:creditTotal,
                 status:st, over:over>0?over:0, aging:ag, lastInv:lastInv, lastDep:lastDep, term:term, L:L });
    });
    return out;
  }
  function _fxLedgers(region){
    if(region==='all') return _fxLedgersOne('서울').concat(_fxLedgersOne('화성'));
    return _fxLedgersOne(region);
  }
"""
    s = cut(s, "  function _fxLedgers(region){", "  var _FX_STC = {", LG_NEW, 'LEDGERS')

    # ── 원장 표시: 기간 조회 + 전기이월 ──
    LR_NEW = r"""  function _fxLedgerAllRows(L){
    var rows=[];
    if(L.opening) rows.push({date:L.openDate||'', type:'기초', desc:'기초 이월', chg:L.opening});
    L.invs.forEach(function(e){ rows.push({date:e.date, type:'계산서', desc:'세금계산서 (공급가 '+_fxFmt(e.supply)+' + 세액 '+_fxFmt(e.tax)+')'+(e.note?' · '+e.note:''), chg:e.total}); });
    L.deps.forEach(function(e){ rows.push({date:e.date, type:(e.kind==='note'?'어음':'입금'), desc:(e.bank||'')+(e.bank?' · ':'')+(e.payer||''), chg:-e.amount}); });
    L.adjs.forEach(function(a){ rows.push({date:a.date, type:'조정', desc:a.memo||'', chg:a.amount}); });
    rows.sort(function(a,b){ return a.date<b.date?-1:a.date>b.date?1:(a.chg>0?-1:1); });
    var bal=0;
    rows.forEach(function(r){ bal+=r.chg; r.bal=bal; });
    return rows;
  }
  // 기간 적용: from 이전은 '전기이월' 한 줄로 압축, to 이후 제외
  function _fxLedgerPeriodRows(L){
    var all=_fxLedgerAllRows(L);
    if(!_fxLdFrom && !_fxLdTo) return { rows:all, carry:null };
    var carry=0, rows=[];
    all.forEach(function(r){
      if(_fxLdFrom && r.date < _fxLdFrom){ carry+=r.chg; return; }
      if(_fxLdTo && r.date > _fxLdTo) return;
      rows.push(r);
    });
    return { rows:rows, carry:(_fxLdFrom?carry:null) };
  }
  function _fxLedgerRows(L, term){
    var pr=_fxLedgerPeriodRows(L);
    var rows=pr.rows, carry=pr.carry;
    var tDr=0, tCr=0;
    rows.forEach(function(r){ if(r.chg>=0){ tDr+=r.chg; } else { tCr+=-r.chg; } });
    var endBal = rows.length ? rows[rows.length-1].bal : (carry!=null?carry:0);
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;white-space:nowrap';
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
      return '<tr>'
        + '<td style="'+TD+';color:#6b7280">'+r.date+'</td>'
        + '<td style="'+TD+';text-align:center"><span style="font-weight:700;color:'+tc+'">'+r.type+'</span></td>'
        + '<td style="'+TD+';white-space:normal;word-break:break-all;color:#374151">'+esc(r.desc)+'</td>'
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
    return '<div style="background:#fbfcfe;border-top:1px solid #e3eaf2;padding:12px 14px">'
      + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:12px;color:#6b7280;flex-wrap:wrap">'
      +   '<span>결제조건: <b style="color:#14305c">'+(term||'기본(익익월말)')+'</b></span>'
      +   '<span style="display:inline-flex;align-items:center;gap:4px">조회기간'
      +     ' <input type="date" value="'+esc(_fxLdFrom)+'" onchange="fxLdFrom(this.value)" onclick="event.stopPropagation()" style="'+DI+'">'
      +     ' ~ <input type="date" value="'+esc(_fxLdTo)+'" onchange="fxLdTo(this.value)" onclick="event.stopPropagation()" style="'+DI+'">'
      +     ((_fxLdFrom||_fxLdTo)?' <button type="button" class="btn" onclick="event.stopPropagation();fxLdReset()" style="font-size:11px;padding:2px 8px;border:1px solid #d6deea;color:#6b7280;background:#fff">전체</button>':'')
      +   '</span>'
      +   '<span style="font-size:11.5px;color:#9ca3af">차변 = 계산서 발행(채권 증가) · 대변 = 입금·어음 회수(채권 감소)</span>'
      +   '<span style="flex:1"></span>'
      +   '<button type="button" class="btn" onclick="event.stopPropagation();fxLedgerXls(\''+String(L.key).replace(/'/g,'\\\'')+'\')" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#14305c;background:#f4f8fe">원장 엑셀</button>'
      + '</div>'
      + '<div style="background:#fff;border:1px solid #e3e9f0;max-height:420px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
      + '<thead><tr><th style="'+TH+';text-align:left">일자</th><th style="'+TH+'">구분</th><th style="'+TH+';text-align:left">적요</th><th style="'+TH+';text-align:right">차변 (계산서)</th><th style="'+TH+';text-align:right">대변 (입금)</th><th style="'+TH+';text-align:right">잔액</th></tr></thead>'
      + '<tbody>'+body+'</tbody></table></div></div>';
  }
"""
    s = cut(s, "  function _fxLedgerRows(L, term){", "  function _fxRenderArBody(){", LR_NEW, 'LEDGERROWS')

    # ── 미수 현황 본문: 연령 열 + 사업장 배지 + 어음 패널 ──
    AR_NEW = r"""  var _FX_AGL=['미도래','1~30일','31~60일','61~90일','90일 초과'];
  function _fxNotes(){
    return fxDeposits.filter(function(e){ return e.kind==='note' && !e.excluded && (_fxRegion==='all'||e.biz===_fxRegion); });
  }
  function _fxNotesPanelHtml(){
    var notes=_fxNotes();
    if(!notes.length) return '';
    var today=dk(new Date());
    notes.sort(function(a,b){
      var ad=a.due||'9999-12-31', bd=b.due||'9999-12-31';
      return ad<bd?-1:ad>bd?1:(a.date<b.date?1:-1);
    });
    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;white-space:nowrap';
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;white-space:nowrap;vertical-align:middle';
    var rows=notes.map(function(e){
      var st, sc;
      if(!e.due){ st='만기일 미상'; sc='#9ca3af'; }
      else {
        var dd=Math.floor((new Date(today+'T12:00:00')-new Date(e.due+'T12:00:00'))/86400000);
        if(dd>0){ st='만기 경과 '+dd+'일'; sc='#6b7280'; }
        else if(dd===0){ st='오늘 만기'; sc='#dc2626'; }
        else if(dd>=-7){ st='D-'+(-dd); sc='#d97706'; }
        else { st='D-'+(-dd); sc='#1B3A6B'; }
      }
      return '<tr>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+(_fxRegion==='all'?_fxBizBadge(e.biz):'')+esc(e.vendor||e.payer||'미배정')+(e.vendor?'':' <span style="font-size:10.5px;color:#d97706">(미배정)</span>')+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+esc(e.bank||'')+'</td>'
        + '<td style="'+TD+';color:#6b7280;font-size:11px">'+esc(e.noteNo||'')+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+e.date+'</td>'
        + '<td style="'+TD+';text-align:center;font-weight:700;color:'+(e.due?'#1a1a1a':'#b6bec9')+'">'+(e.due||'-')+'</td>'
        + '<td style="'+TD+';text-align:right;font-weight:700">'+_fxFmt(e.amount)+'</td>'
        + '<td style="'+TD+';text-align:center"><span style="font-size:11px;font-weight:700;color:'+sc+'">'+st+'</span></td>'
        + '</tr>';
    }).join('');
    var tot=notes.reduce(function(a,e){ return a+e.amount; },0);
    var noDue=notes.filter(function(e){ return !e.due; }).length;
    return '<div style="background:#fff;border:1px solid #d6deea;margin-bottom:12px">'
      + '<div style="padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#14305c">받을어음 현황 '
      + '<span style="font-weight:400;color:#8a94a6">— '+notes.length+'건 · 합계 '+_fxFmt(tot)+'원'
      + (noDue?(' · 만기일 미상 '+noDue+'건(어음 파일을 다시 올리면 채워집니다)'):'')+'</span></div>'
      + '<div style="max-height:340px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
      + '<thead><tr><th style="'+TH+';text-align:left">거래처(발행인)</th><th style="'+TH+'">은행</th><th style="'+TH+';text-align:left">어음번호</th><th style="'+TH+'">수취일</th><th style="'+TH+'">만기일</th><th style="'+TH+';text-align:right">금액</th><th style="'+TH+'">상태</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div></div>';
  }
  function _fxRenderArBody(){
    var host=document.getElementById('fxArList'); if(!host) return;
    var base=_fxLedgers(_fxRegion);
    var data=base.slice();
    if(_fxQ) data=data.filter(function(x){ return x.name.toLowerCase().indexOf(_fxQ)>=0 || x.vbiz.indexOf(_fxQ)>=0; });
    if(_fxStatusF!=='all'){
      if(_fxStatusF==='미수') data=data.filter(function(x){ return x.status==='미수'||x.status==='장기미수'; });
      else data=data.filter(function(x){ return x.status===_fxStatusF; });
    }
    data.sort(function(a,b){ return b.bal-a.bal; });
    var totBal=0, nMisu=0, nLong=0, agT=[0,0,0,0,0];
    base.forEach(function(x){
      if(x.bal>0) totBal+=x.bal;
      if(x.status==='미수') nMisu++; if(x.status==='장기미수') nLong++;
      for(var i=0;i<5;i++) agT[i]+=x.aging[i];
    });
    var notes=_fxNotes();
    var today=dk(new Date());
    var nSoon=notes.filter(function(e){ if(!e.due) return false; var dd=Math.floor((new Date(e.due+'T12:00:00')-new Date(today+'T12:00:00'))/86400000); return dd>=0 && dd<=7; }).length;
    var chips=document.getElementById('fxArChips');
    if(chips){
      var h=_fxChip('총 미수', _fxFmt(totBal)+'원', true);
      for(var ci=1;ci<5;ci++){ if(agT[ci]) h+=_fxChip(_FX_AGL[ci], _fxFmt(agT[ci])+'원', false); }
      if(agT[0]) h+=_fxChip('미도래', _fxFmt(agT[0])+'원', false);
      h+=_fxChip('미수', nMisu+'곳', false)+_fxChip('장기미수', nLong+'곳', false)+_fxChip('거래처', base.length+'곳', false);
      if(notes.length) h+='<span onclick="fxNotesToggle()" style="cursor:pointer" title="클릭하면 어음 목록이 열립니다">'+_fxChip('어음', notes.length+'건'+(nSoon?(' · 7일 내 만기 '+nSoon):'')+(_fxNotesOpen?' ▲':' ▼'), false)+'</span>';
      chips.innerHTML=h;
    }
    var noteHtml = _fxNotesOpen ? _fxNotesPanelHtml() : '';
    if(!data.length){ host.innerHTML=noteHtml+'<div style="text-align:center;padding:48px;color:#b6bec9;font-size:13px">조건에 맞는 거래처가 없습니다.</div>'; return; }
    var TH='padding:9px 10px;background:#fafafa;color:#888;font-weight:500;font-size:12px;text-align:center;border-bottom:2px solid #d3dce6;border-right:1px solid #e3e9f0;white-space:nowrap';
    var TD='padding:9px 10px;border-bottom:1px solid #eef2f7;border-right:1px solid #eef2f7;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle;font-size:12.5px';
    var agCell=function(v,last){
      return '<td style="'+TD+';text-align:right;font-size:12px;color:'+(v?(last?'#dc2626':'#374151'):'#c9d0da')+'">'+(v?_fxFmt(v):'-')+'</td>';
    };
    var rows=data.map(function(x){
      var exp = _fxExp===x.key;
      var sc=_FX_STC[x.status]||'#6b7280';
      var tr='<tr onclick="fxExpand(\''+x.key.replace(/'/g,"\\'")+'\')" style="cursor:pointer;'+(exp?'background:#f4f8fe;':'')+'" onmouseover="this.style.background=\'#f7fafd\'" onmouseout="this.style.background=\''+(exp?'#f4f8fe':'')+'\'">'
        + '<td style="'+TD+';text-align:center"><span style="font-size:11px;font-weight:700;color:'+sc+';border:1px solid '+sc+';padding:1px 7px">'+x.status+'</span></td>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+(_fxRegion==='all'?_fxBizBadge(x.rgn):'')+esc(x.name)+(x.vbiz?' <span style="font-weight:400;color:#9ca3af;font-size:11px">'+x.vbiz+'</span>':'')+'</td>'
        + '<td style="'+TD+';text-align:right;font-weight:700;color:'+(x.bal>0?'#1a1a1a':'#9ca3af')+'">'+_fxFmt(x.bal)+'</td>'
        + agCell(x.aging[0],false)+agCell(x.aging[1],false)+agCell(x.aging[2],false)+agCell(x.aging[3],false)+agCell(x.aging[4],true)
        + '<td style="'+TD+';text-align:right;color:#6b7280">'+_fxFmt(x.invSum)+'</td>'
        + '<td style="'+TD+';text-align:right;color:#6b7280">'+_fxFmt(x.depSum)+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.lastInv||'-')+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.lastDep||'-')+'</td>'
        + '<td style="'+TD+';text-align:center;color:'+(x.over>90?'#dc2626':(x.over>0?'#d97706':'#9ca3af'))+'">'+(x.over>0?(x.over+'일'):'-')+'</td>'
        + '</tr>';
      if(exp) tr += '<tr><td colspan="13" style="padding:0;border-bottom:2px solid #1B3A6B;background:#fff">'+_fxLedgerRows(x.L, x.term)+'</td></tr>';
      return tr;
    }).join('');
    host.innerHTML = noteHtml
      + '<div style="background:#fff;border:1px solid #d6deea;overflow-x:auto"><table style="width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:12.5px;min-width:1280px">'
      + '<colgroup><col style="width:80px"><col><col style="width:112px"><col style="width:92px"><col style="width:92px"><col style="width:92px"><col style="width:92px"><col style="width:92px"><col style="width:112px"><col style="width:112px"><col style="width:92px"><col style="width:92px"><col style="width:64px"></colgroup>'
      + '<thead><tr><th style="'+TH+'" rowspan="2">상태</th><th style="'+TH+'" rowspan="2">거래처</th><th style="'+TH+'" rowspan="2">미수 잔액</th><th style="'+TH+'" colspan="5">채권 연령 (만기 기준)</th><th style="'+TH+'" rowspan="2">계산서 누계</th><th style="'+TH+'" rowspan="2">입금 누계</th><th style="'+TH+'" rowspan="2">최근 계산서</th><th style="'+TH+'" rowspan="2">최근 입금</th><th style="'+TH+'" rowspan="2">경과</th></tr>'
      + '<tr><th style="'+TH+'">미도래</th><th style="'+TH+'">1~30일</th><th style="'+TH+'">31~60일</th><th style="'+TH+'">61~90일</th><th style="'+TH+'">90일+</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div>';
  }
"""
    s = cut(s, "  function _fxRenderArBody(){", "  function _fxRegionBtnsHtml(){", AR_NEW, 'ARBODY')

    # ── 표 가로 전체: 업로드 카드/결과/미배정 max-width 제거 ──
    s = rep(s, ";max-width:1080px", "", 3, 'MAXW')

    # ── 어음 파서: 만기일 저장 + 재업로드 시 기존 어음 만기일 채움 ──
    s = rep(s, """            var iNo, iVen, iAmt, iDt, iSt, iCxl=-1;
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
            }""",
            """            var iNo, iVen, iAmt, iDt, iSt, iCxl=-1, iDue=-1;
            if(noteKind==='신한어음'){
              iNo=H.indexOf('전자어음번호'); iVen=H.indexOf('발행인'); iAmt=H.indexOf('어음금액');
              iDt=H.indexOf('수취일자'); if(iDt<0) iDt=H.indexOf('발행일자'); iSt=H.indexOf('상태');
              iDue=H.indexOf('만기일자');
            } else if(noteKind==='기업어음'){
              iNo=H.indexOf('어음번호'); iVen=H.indexOf('구매기업명'); iAmt=H.indexOf('채권금액');
              iDt=H.indexOf('채권등록일'); iSt=H.indexOf('상태');
              iDue=H.indexOf('채권만기일');
            } else {
              iNo=H.indexOf('채권번호'); iVen=H.indexOf('구매기업명');
              iAmt=H.indexOf('채권금액(원)'); if(iAmt<0) iAmt=H.indexOf('채권금액');
              iDt=H.indexOf('발행일'); iSt=H.indexOf('상태'); iCxl=H.indexOf('취소일');
              iDue=H.indexOf('만기일');
            }""", 1, 'NOTEIDX')
    s = rep(s, """              if(seen['NN|'+biz+'|'+noteNo]){ nDup++; fD2++; continue; }""",
            """              if(seen['NN|'+biz+'|'+noteNo]){
                if(iDue>=0){
                  var nd0=_fxD(row4[iDue]);
                  if(nd0){ fxDeposits.forEach(function(e){ if(e.noteNo===noteNo && e.biz===biz && !e.due){ e.due=nd0; } }); }
                }
                nDup++; fD2++; continue;
              }""", 1, 'NOTEDUP')
    s = rep(s, """              fxDeposits.push({ id:'NT|'+biz+'|'+noteNo, biz:biz, date:d4, amount:amt4, payer:ven4,
                                vendor:v4||'', vbiz:v4?_fxVbizOf(biz,v4):'', kind:'note', bank:noteKind,
                                noteNo:noteNo, src:'upload' });""",
            """              fxDeposits.push({ id:'NT|'+biz+'|'+noteNo, biz:biz, date:d4, amount:amt4, payer:ven4,
                                vendor:v4||'', vbiz:v4?_fxVbizOf(biz,v4):'', kind:'note', bank:noteKind,
                                noteNo:noteNo, due:(iDue>=0?_fxD(row4[iDue]):null), src:'upload' });""", 1, 'NOTEPUSH')

    # ── 집계 엑셀용 vslot(6칸 들여쓰기) + 파일명 전체 라벨 ──
    s = rep(s, "\n      function vslot(e){ var k=(e.vbiz&&/\\d{3}-\\d{2}-\\d{5}/.test(e.vbiz))?e.vbiz:('N|'+e.vendor); if(!V[k]) V[k]={name:e.vendor, vbiz:e.vbiz||'', sc:0, stt:0, pc:0, ptt:0}; if(e.vendor) V[k].name=e.vendor; return V[k]; }",
            "\n      function vslot(e){ var k=(_fxRegion==='all'?(e.biz+'|'):'')+((e.vbiz&&/\\d{3}-\\d{2}-\\d{5}/.test(e.vbiz))?e.vbiz:('N|'+e.vendor)); if(!V[k]) V[k]={name:e.vendor, vbiz:e.vbiz||'', b:e.biz, sc:0, stt:0, pc:0, ptt:0}; if(e.vendor) V[k].name=e.vendor; return V[k]; }", 1, 'VSLOT2')
    s = rep(s, "      var sv=fxSalesInv.filter(function(e){ return e.biz===_fxRegion && e.date && e.date.slice(0,4)===yr; });",
            "      var sv=fxSalesInv.filter(function(e){ return (_fxRegion==='all'||e.biz===_fxRegion) && e.date && e.date.slice(0,4)===yr; });", 1, 'SV2')
    s = rep(s, "      var pv=fxPurchInv.filter(function(e){ return e.biz===_fxRegion && e.date && e.date.slice(0,4)===yr; });",
            "      var pv=fxPurchInv.filter(function(e){ return (_fxRegion==='all'||e.biz===_fxRegion) && e.date && e.date.slice(0,4)===yr; });", 1, 'PV2')
    s = rep(s, "        fn='매입매출집계_월별_'+_fxRegion+'_'+yr+'_'+_fxDs()+'.xlsx';",
            "        fn='매입매출집계_월별_'+_fxRegionLabel()+'_'+yr+'_'+_fxDs()+'.xlsx';", 1, 'FN1')
    s = rep(s, "      XLSX.writeFile(wb2, '매입매출집계_거래처별_'+_fxRegion+'_'+yr+'_'+_fxDs()+'.xlsx');",
            "      XLSX.writeFile(wb2, '매입매출집계_거래처별_'+_fxRegionLabel()+'_'+yr+'_'+_fxDs()+'.xlsx');", 1, 'FN2')
    # 집계 엑셀 거래처별: 사업장 열 (전체 모드)
    s = rep(s, """      aoa=[['거래처','사업자번호','매출 건수','매출 합계','매입 건수','매입 합계']];
      list.forEach(function(x){ aoa.push([x.name, x.vbiz||'', x.sc, x.stt, x.pc, x.ptt]); });""",
            """      var allMode=(_fxRegion==='all');
      aoa=[(allMode?['사업장']:[]).concat(['거래처','사업자번호','매출 건수','매출 합계','매입 건수','매입 합계'])];
      list.forEach(function(x){ aoa.push((allMode?[x.b||'']:[]).concat([x.name, x.vbiz||'', x.sc, x.stt, x.pc, x.ptt])); });""", 1, 'SUMXLSA')
    s = rep(s, """      aoa.push(['합계 ('+list.length+'곳)','', list.reduce(function(a,x){return a+x.sc;},0), list.reduce(function(a,x){return a+x.stt;},0), list.reduce(function(a,x){return a+x.pc;},0), list.reduce(function(a,x){return a+x.ptt;},0)]);
      var ws2=XLSX.utils.aoa_to_sheet(aoa);
      ws2['!cols']=[{wch:26},{wch:14},{wch:9},{wch:14},{wch:9},{wch:14}];
      _fxXlsStyle(ws2, 0, [3,5], [0]);""",
            """      aoa.push((allMode?['']:[]).concat(['합계 ('+list.length+'곳)','', list.reduce(function(a,x){return a+x.sc;},0), list.reduce(function(a,x){return a+x.stt;},0), list.reduce(function(a,x){return a+x.pc;},0), list.reduce(function(a,x){return a+x.ptt;},0)]));
      var ws2=XLSX.utils.aoa_to_sheet(aoa);
      ws2['!cols']=(allMode?[{wch:8}]:[]).concat([{wch:26},{wch:14},{wch:9},{wch:14},{wch:9},{wch:14}]);
      _fxXlsStyle(ws2, 0, (allMode?[4,6]:[3,5]), (allMode?[1]:[0]));""", 1, 'SUMXLSB')

    # ── 원장 엑셀: 기간·사업장 반영 / 미수현황 엑셀: 연령·사업장 열 ──
    XL_NEW = r"""  // 거래처 원장 엑셀 (차변/대변 · 조회기간 반영)
  window.fxLedgerXls = async function(key){
    try{
      await _ensureXlsxLib();
      var lg=_fxLedgers(_fxRegion).find(function(x){ return x.key===key; });
      if(!lg){ showInfoModal('원장 다운로드','거래처를 찾지 못했습니다.'); return; }
      var pr=_fxLedgerPeriodRows(lg.L);
      var rows=pr.rows, carry=pr.carry;
      var tDr=0, tCr=0;
      rows.forEach(function(r){ if(r.chg>=0){ tDr+=r.chg; } else { tCr+=-r.chg; } });
      var endBal = rows.length ? rows[rows.length-1].bal : (carry!=null?carry:0);
      var aoa=[
        ['거래처', lg.name, '사업자번호', lg.vbiz||'-'],
        ['사업장', lg.rgn, '결제조건', lg.term||'기본(익익월말)'],
        ['계산서 누계', lg.invSum, '입금·조정 누계', lg.depSum],
        ['미수 잔액', lg.bal, '작성일', dk(new Date())],
        (_fxLdFrom||_fxLdTo) ? ['조회기간', (_fxLdFrom||'처음')+' ~ '+(_fxLdTo||'현재'), '', ''] : [],
        ['일자','구분','적요','차변','대변','잔액']
      ];
      var headRow=5;
      if(carry!=null) aoa.push([_fxLdFrom, '이월', '전기이월 (조회기간 이전 합산)', null, null, carry]);
      rows.forEach(function(r){ aoa.push([r.date, r.type, r.desc, r.chg>=0?r.chg:null, r.chg<0?-r.chg:null, r.bal]); });
      aoa.push([(_fxLdFrom||_fxLdTo)?'기간 합계':'합계','','',tDr,tCr,endBal]);
      var ws=XLSX.utils.aoa_to_sheet(aoa);
      ws['!cols']=[{wch:12},{wch:8},{wch:46},{wch:14},{wch:14},{wch:14}];
      _fxXlsStyle(ws, headRow, [3,4,5], [2]);
      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, '원장');
      XLSX.writeFile(wb, _fxSafeName(lg.name)+' 원장_'+lg.rgn+'_'+_fxDs()+'.xlsx');
    }catch(e){ showInfoModal('다운로드 실패', (e&&e.message||String(e))); }
  };
  // 미수 현황 목록 엑셀 (현재 필터 반영 · 연령 구간 포함)
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
      var aoa=[['상태','사업장','거래처','사업자번호','미수 잔액','미도래','1~30일','31~60일','61~90일','90일 초과','계산서 누계','입금·조정 누계','최근 계산서','최근 입금','경과일','결제조건']];
      data.forEach(function(x){
        aoa.push([x.status, x.rgn, x.name, x.vbiz||'', x.bal, x.aging[0], x.aging[1], x.aging[2], x.aging[3], x.aging[4], x.invSum, x.depSum, x.lastInv||'', x.lastDep||'', x.over||0, x.term||'']);
      });
      var tB=data.reduce(function(a,x){ return a+(x.bal>0?x.bal:0); },0);
      var agS=[0,1,2,3,4].map(function(i){ return data.reduce(function(a,x){ return a+x.aging[i]; },0); });
      aoa.push(['합계','','미수 '+data.filter(function(x){return x.bal>0;}).length+'곳','', tB, agS[0], agS[1], agS[2], agS[3], agS[4],
                data.reduce(function(a,x){return a+x.invSum;},0), data.reduce(function(a,x){return a+x.depSum;},0),'','','','']);
      var ws=XLSX.utils.aoa_to_sheet(aoa);
      ws['!cols']=[{wch:8},{wch:7},{wch:24},{wch:14},{wch:13},{wch:12},{wch:12},{wch:12},{wch:12},{wch:12},{wch:13},{wch:13},{wch:11},{wch:11},{wch:7},{wch:11}];
      _fxXlsStyle(ws, 0, [4,5,6,7,8,9,10,11], [2]);
      var wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, '미수현황');
      XLSX.writeFile(wb, '미수현황_'+_fxRegionLabel()+'_'+_fxDs()+'.xlsx');
    }catch(e){ showInfoModal('다운로드 실패', (e&&e.message||String(e))); }
  };
"""
    s = cut(s, "  // 거래처 원장 엑셀 (차변/대변)", "  // 매입·매출 집계 엑셀 (현재 모드·연도 반영)", XL_NEW, 'XLS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r129(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r128 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r128 2026-08-21 -->', '<!-- test build r129 2026-08-22 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
