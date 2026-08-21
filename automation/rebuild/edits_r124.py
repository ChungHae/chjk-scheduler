# -*- coding: utf-8 -*-
# r124: [매입매출 3단계] 미수 현황 화면 — ERP식 거래처 원장.
#  - 사업장(서울/화성) 토글 + 거래처 검색 + 상태 필터(전체/미수/장기미수/완납)
#  - 잔액 = 기초 + 계산서(+조정+) − 입금·어음(−조정) / FIFO 소진으로 미결 계산서 산출
#  - 결제조건(기준설정표: 익월말·익익월중순 등, 기본 익익월말)으로 만기 계산,
#    상태: 완납 / 진행(기한 내) / 미수(기한 경과) / 장기미수(90일 초과) + 경과일
#  - 행 클릭 → 페이지 안 원장 펼침(계산서/입금/조정 시간순 + 잔액 흐름)
#  - 집계(sum) 탭은 다음 단계, 업로드 탭은 그대로

import io

def cut(s, start, end, repl, label):
    i1 = s.find(start)
    if i1 < 0 or s.find(start, i1+1) >= 0: raise SystemExit('R124 FAIL %s start' % label)
    i2 = s.find(end, i1)
    if i2 < 0: raise SystemExit('R124 FAIL %s end' % label)
    return s[:i1] + repl + s[i2:]

NEW_JS = r"""  window.fxSwitchTab = function(t){ _fxTab = t; renderFxPage(); };
  function _fxFmt(n){ return (Number(n)||0).toLocaleString(); }
  var _fxRegion='서울', _fxQ='', _fxStatusF='all', _fxExp=null;
  window.fxSetRegion = function(b){ _fxRegion=b; _fxExp=null; renderFxPage(); };
  window.fxSearchInput = function(v){ _fxQ=String(v||'').trim().toLowerCase(); _fxExp=null; _fxRenderArBody(); };
  window.fxSetStatusF = function(v){ _fxStatusF=v; _fxExp=null; _fxRenderArBody(); };
  window.fxExpand = function(key){ _fxExp = (_fxExp===key)?null:key; _fxRenderArBody(); };
  // 결제조건 → 만기일 ('익월말','익익월중순','익익익월초' … 기본 익익월말)
  function _fxDue(dateStr, term){
    var m=String(term||'').match(/^(익+)월(초|중순|말)$/);
    var n=m?m[1].length:2, part=m?m[2]:'말';
    var d=new Date(dateStr+'T12:00:00');
    if(isNaN(d.getTime())) return dateStr;
    var y=d.getFullYear(), mo=d.getMonth()+n;
    if(part==='말') return _fxD(new Date(y, mo+1, 0));
    return _fxD(new Date(y, mo, part==='초'?10:15));
  }
  // 사업장별 거래처 원장 구성 (key = 사업자번호 우선, 없으면 이름)
  function _fxLedgers(region){
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
      var o=fxOpenings[k]||{}; var sl=slot('', p[1]); sl.opening=Number(o.amount)||0; sl.openDate=o.asOf||null;
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
      unpaid.forEach(function(u){
        var dd=Math.floor((new Date(today+'T12:00:00')-new Date(u.due+'T12:00:00'))/86400000);
        if(dd>over) over=dd;
      });
      var st = bal<=0 ? '완납' : (over<=0 ? '진행' : (over>90 ? '장기미수' : '미수'));
      var lastInv = L.invs.length ? L.invs.reduce(function(a,e){ return e.date>a?e.date:a; },'') : '';
      var lastDep = L.deps.length ? L.deps.reduce(function(a,e){ return e.date>a?e.date:a; },'') : '';
      out.push({ key:k, name:L.name, vbiz:L.vbiz, bal:bal, invSum:invSum, depSum:creditTotal,
                 status:st, over:over>0?over:0, lastInv:lastInv, lastDep:lastDep, term:term, L:L });
    });
    return out;
  }
  var _FX_STC = { '완납':'#15803d', '진행':'#1B3A6B', '미수':'#d97706', '장기미수':'#dc2626' };
  function _fxChip(label, val, hi){
    return '<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:'+(hi?'#1B3A6B':'#EAF1FB')+';font-size:12px;color:'+(hi?'#ccdcf5':'#6b7280')+';white-space:nowrap">'+label+' <b style="color:'+(hi?'#fff':'#1a1a1a')+';font-size:13px">'+val+'</b></span>';
  }
  function _fxLedgerRows(L, term){
    var rows=[];
    if(L.opening) rows.push({date:L.openDate||'', type:'기초', desc:'기초 이월', chg:L.opening});
    L.invs.forEach(function(e){ rows.push({date:e.date, type:'계산서', desc:'세금계산서 (공급가 '+_fxFmt(e.supply)+' + 세액 '+_fxFmt(e.tax)+')'+(e.note?' · '+esc(e.note):''), chg:e.total}); });
    L.deps.forEach(function(e){ rows.push({date:e.date, type:(e.kind==='note'?'어음':'입금'), desc:esc((e.bank||'')+(e.bank?' · ':'')+(e.payer||'')), chg:-e.amount}); });
    L.adjs.forEach(function(a){ rows.push({date:a.date, type:'조정', desc:esc(a.memo||''), chg:a.amount}); });
    rows.sort(function(a,b){ return a.date<b.date?-1:a.date>b.date?1:(a.chg>0?-1:1); });
    var bal=0;
    rows.forEach(function(r){ bal+=r.chg; r.bal=bal; });
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;white-space:nowrap';
    var body=rows.map(function(r){
      var tc = r.type==='계산서'?'#14305c':(r.type==='조정'?'#d97706':(r.type==='기초'?'#6b7280':'#15803d'));
      return '<tr>'
        + '<td style="'+TD+';color:#6b7280">'+r.date+'</td>'
        + '<td style="'+TD+';text-align:center"><span style="font-weight:700;color:'+tc+'">'+r.type+'</span></td>'
        + '<td style="'+TD+';white-space:normal;word-break:break-all;color:#374151">'+r.desc+'</td>'
        + '<td style="'+TD+';text-align:right;color:'+(r.chg>=0?'#14305c':'#15803d')+'">'+(r.chg>=0?'+':'')+_fxFmt(r.chg)+'</td>'
        + '<td style="'+TD+';text-align:right;font-weight:700;color:'+(r.bal>0?'#1a1a1a':'#9ca3af')+'">'+_fxFmt(r.bal)+'</td>'
        + '</tr>';
    }).join('');
    var TH='padding:7px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;border-bottom:2px solid #d3dce6;white-space:nowrap';
    return '<div style="background:#fbfcfe;border-top:1px solid #e3eaf2;padding:12px 14px">'
      + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:12px;color:#6b7280">'
      +   '<span>결제조건: <b style="color:#14305c">'+(term||'기본(익익월말)')+'</b></span>'
      +   '<span style="flex:1"></span>'
      +   '<span style="color:#9ca3af">엑셀 다운로드는 다음 단계에서 제공</span>'
      + '</div>'
      + '<div style="background:#fff;border:1px solid #e3e9f0;max-height:420px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
      + '<thead><tr><th style="'+TH+';text-align:left">일자</th><th style="'+TH+'">구분</th><th style="'+TH+';text-align:left">내용</th><th style="'+TH+';text-align:right">증감</th><th style="'+TH+';text-align:right">잔액</th></tr></thead>'
      + '<tbody>'+body+'</tbody></table></div></div>';
  }
  function _fxRenderArBody(){
    var host=document.getElementById('fxArList'); if(!host) return;
    var data=_fxLedgers(_fxRegion);
    if(_fxQ) data=data.filter(function(x){ return x.name.toLowerCase().indexOf(_fxQ)>=0 || x.vbiz.indexOf(_fxQ)>=0; });
    if(_fxStatusF!=='all'){
      if(_fxStatusF==='미수') data=data.filter(function(x){ return x.status==='미수'||x.status==='장기미수'; });
      else data=data.filter(function(x){ return x.status===_fxStatusF; });
    }
    data.sort(function(a,b){ return b.bal-a.bal; });
    var totBal=0, nMisu=0, nLong=0;
    _fxLedgers(_fxRegion).forEach(function(x){ if(x.bal>0) totBal+=x.bal; if(x.status==='미수') nMisu++; if(x.status==='장기미수') nLong++; });
    var chips=document.getElementById('fxArChips');
    if(chips) chips.innerHTML = _fxChip('총 미수', _fxFmt(totBal)+'원', true) + _fxChip('미수', nMisu+'곳', false) + _fxChip('장기미수', nLong+'곳', false) + _fxChip('거래처', _fxLedgers(_fxRegion).length+'곳', false);
    if(!data.length){ host.innerHTML='<div style="text-align:center;padding:48px;color:#b6bec9;font-size:13px">조건에 맞는 거래처가 없습니다.</div>'; return; }
    var TH='padding:9px 10px;background:#fafafa;color:#888;font-weight:500;font-size:12px;text-align:center;border-bottom:2px solid #d3dce6;border-right:1px solid #e3e9f0;white-space:nowrap';
    var TD='padding:9px 10px;border-bottom:1px solid #eef2f7;border-right:1px solid #eef2f7;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle;font-size:12.5px';
    var rows=data.map(function(x){
      var exp = _fxExp===x.key;
      var sc=_FX_STC[x.status]||'#6b7280';
      var tr='<tr onclick="fxExpand(\''+x.key.replace(/'/g,"\\'")+'\')" style="cursor:pointer;'+(exp?'background:#f4f8fe;':'')+'" onmouseover="this.style.background=\'#f7fafd\'" onmouseout="this.style.background=\''+(exp?'#f4f8fe':'')+'\'">'
        + '<td style="'+TD+';text-align:center"><span style="font-size:11px;font-weight:700;color:'+sc+';border:1px solid '+sc+';padding:1px 7px">'+x.status+'</span></td>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+esc(x.name)+(x.vbiz?' <span style="font-weight:400;color:#9ca3af;font-size:11px">'+x.vbiz+'</span>':'')+'</td>'
        + '<td style="'+TD+';text-align:right;font-weight:700;color:'+(x.bal>0?'#1a1a1a':'#9ca3af')+'">'+_fxFmt(x.bal)+'</td>'
        + '<td style="'+TD+';text-align:right;color:#6b7280">'+_fxFmt(x.invSum)+'</td>'
        + '<td style="'+TD+';text-align:right;color:#6b7280">'+_fxFmt(x.depSum)+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.lastInv||'-')+'</td>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+(x.lastDep||'-')+'</td>'
        + '<td style="'+TD+';text-align:center;color:'+(x.over>90?'#dc2626':(x.over>0?'#d97706':'#9ca3af'))+'">'+(x.over>0?(x.over+'일'):'-')+'</td>'
        + '</tr>';
      if(exp) tr += '<tr><td colspan="8" style="padding:0;border-bottom:2px solid #1B3A6B;background:#fff">'+_fxLedgerRows(x.L, x.term)+'</td></tr>';
      return tr;
    }).join('');
    host.innerHTML =
      '<div style="background:#fff;border:1px solid #d6deea"><table style="width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:12.5px">'
      + '<colgroup><col style="width:84px"><col><col style="width:120px"><col style="width:120px"><col style="width:120px"><col style="width:96px"><col style="width:96px"><col style="width:72px"></colgroup>'
      + '<thead><tr><th style="'+TH+'">상태</th><th style="'+TH+'">거래처</th><th style="'+TH+'">미수 잔액</th><th style="'+TH+'">계산서 누계</th><th style="'+TH+'">입금 누계</th><th style="'+TH+'">최근 계산서</th><th style="'+TH+'">최근 입금</th><th style="'+TH+'">경과</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div>';
  }
  function renderFxPage(){
    var body = document.getElementById('fxBody'); if(!body) return;
    document.querySelectorAll('#fxSubTabs .pf-btn').forEach(function(b){ b.classList.toggle('active', b.dataset.fxtab===_fxTab); });
    var meta = document.getElementById('fxMeta');
    if(meta) meta.textContent = _fxLoaded ? ('매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건') : '';
    var _empty = function(msg){ return '<div style="text-align:center;padding:56px 20px;color:#b6bec9;font-size:13px;line-height:1.9">'+msg+'</div>'; };
    if(_fxTab==='ar'){
      body.innerHTML = '<div style="text-align:center;padding:40px;color:#9ca3af;font-size:13px">자료 불러오는 중…</div>';
      _fxEnsureData().then(function(){
        if(_fxTab!=='ar') return;
        if(meta) meta.textContent = '매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건';
        if(!fxSalesInv.length && !fxDeposits.length){
          body.innerHTML = _empty('자료가 아직 없습니다.<br><b style="color:#5b7ba6">자료 업로드</b> 탭에서 기존 앱 누적본(zip)을 가져오거나 계산서·입금 자료를 올려주세요.');
          return;
        }
        body.innerHTML =
          '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px">'
          + '<div style="display:flex;gap:4px">'
          +   ['서울','화성'].map(function(b){ return '<button type="button" class="btn pf-btn'+(_fxRegion===b?' active':'')+'" onclick="fxSetRegion(\''+b+'\')" style="font-size:11.5px;padding:3px 12px">'+b+'</button>'; }).join('')
          + '</div>'
          + '<input type="text" class="q-flat" placeholder="거래처 검색…" value="'+esc(_fxQ)+'" oninput="fxSearchInput(this.value)" style="width:220px">'
          + '<select class="q-flat" onchange="fxSetStatusF(this.value)" style="width:110px;background:#fff;color:#1a1a1a;cursor:pointer">'
          +   [['all','전체 상태'],['미수','미수(장기 포함)'],['장기미수','장기미수'],['진행','진행'],['완납','완납']].map(function(o){ return '<option value="'+o[0]+'"'+(_fxStatusF===o[0]?' selected':'')+'>'+o[1]+'</option>'; }).join('')
          + '</select>'
          + '<span id="fxArChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-left:6px"></span>'
          + '</div>'
          + '<div id="fxArList"></div>';
        _fxRenderArBody();
      });
      return;
    }
    if(_fxTab==='sum'){
      body.innerHTML = '<div style="text-align:center;padding:40px;color:#9ca3af;font-size:13px">자료 불러오는 중…</div>';
      _fxEnsureData().then(function(){
        if(_fxTab!=='sum') return;
        body.innerHTML = _empty('세금계산서 기준 월별·거래처별 매입·매출 집계 — 다음 단계(r125)에서 제공됩니다.');
      });
      return;
    }
    // 자료 업로드 탭
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
      + '<div id="fxUpResult" style="margin-top:14px;max-width:980px"></div>';
  }
"""

def apply_r124(s, path):
    s = cut(s, '  window.fxSwitchTab = function(t){', '  // ── 누적본 zip 이관 ──', NEW_JS, 'JS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r124(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r123 2026-08-21 -->') == 1
            s = s.replace('<!-- test build r123 2026-08-21 -->', '<!-- test build r124 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
