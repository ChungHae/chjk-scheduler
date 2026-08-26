# -*- coding: utf-8 -*-
# r155: [사업자번호 없는 거래처 배정 차단 + 기존 배정 점검]
#
#  사용자 논지: 미수현황은 세금계산서와 맞춰보는 자료다. 사업자번호가 없으면 세금계산서가
#  발행될 수 없으니, 사업자번호 없는 거래처로의 입금 배정은 성립할 수 없다.
#
#  실측으로 확인한 예외 2가지(그대로 막으면 안 되는 이유):
#   (가) 업체 목록의 사업자번호 칸이 비어 있어도, 세금계산서 자료에 번호가 있으면
#        _fxClientVbiz 가 그것을 찾아 채운다(실측: 333-33-33333 정상 확인).
#        따라서 "업체 목록 번호 칸이 비었다" 로 판정하면 멀쩡한 거래처가 막힌다.
#        -> 반드시 업체목록 -> 계산서 자료 순으로 찾아본 뒤 판정한다.
#   (나) 기초이월·조정은 계산서를 거치지 않고 미수를 만든다.
#        실측: 번호가 전혀 없어도 기초이월만으로 미수 2,000,000 / 조정만으로 1,500,000 이
#        원장에 정상으로 잡힌다. 기초이월 재적재와 예외처리 조정 31건이 아직 대기 중이라
#        이 경로는 살아 있어야 한다.
#
#  확정 규칙(사용자 선택):
#   1. 배정 직전에 사업자번호를 업체목록 -> 계산서 자료 순으로 찾는다.
#   2. 찾으면 그대로 배정(기존과 동일).
#   3. 못 찾았고 그 거래처에 기초이월/조정/계산서 근거도 없으면 -> 배정하지 않고 안내.
#   4. 못 찾았지만 기초이월/조정/계산서 근거가 있으면 -> 무엇 때문인지 밝히는 확인창을
#      띄우고, 사용자가 승인하면 배정.
#   5. 자동 배정 재실행(fxReassignRun)도 같은 기준으로 근거 없는 건은 건너뛰고 그 수를 알린다.
#
#  함께: 자료 업로드 탭에 "사업자번호 없이 배정된 입금 N건 [보기]" 점검 패널 추가.
#        각 건마다 지금 자료로 번호가 찾아지면 [번호 채우기], 아니면 [미배정으로] 를 제공하고,
#        찾아지는 건은 [찾아지는 번호 일괄 채우기] 로 한 번에 정리할 수 있다.
#        목록 계산은 계산서 15,000건을 매번 훑지 않도록 자료 지문(_fxDataStamp) 으로 캐시한다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R155 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r155(s, path):
    # ── 1. 판정 helper + 점검 패널 (되돌리기 인프라 앞에 삽입) ──
    s = rep(s,
        "  // ── r154: 배정 되돌리기 ────────────────────────────────",
        r"""  // ── r155: 사업자번호 판정 ──────────────────────────────
  //  계산서와 맞출 수 있으려면 사업자번호가 있어야 한다. 단 기초이월·조정은
  //  계산서 없이도 미수를 만들므로, 그 근거가 있으면 확인 후 진행을 허용한다.
  function _fxHasLedgerBasis(name, biz){
    var n=_fxNormWs(name);
    if(fxOpenings[biz+'|'+name]) return '기초이월';
    for(var i=0;i<fxAdjusts.length;i++){
      var a=fxAdjusts[i];
      if(a.biz===biz && _fxNormWs(a.vendor)===n) return '조정';
    }
    for(var j=0;j<fxSalesInv.length;j++){
      var e=fxSalesInv[j];
      if(e.biz===biz && _fxNormWs(e.vendor)===n) return '계산서';
    }
    return '';
  }
  // 거래처명 -> 사업자번호 조회기 (업체목록 우선, 없으면 계산서 자료). 한 번 만들어 재사용.
  function _fxVbizResolver(){
    var byInv=Object.create(null);
    fxSalesInv.forEach(function(e){
      if(!e.vendor || !e.vbiz) return;
      var k=e.biz+'|'+e.vendor;
      if(byInv[k]===undefined) byInv[k]=e.vbiz;
    });
    var byCli=Object.create(null);
    _fxClientOpts().forEach(function(o){ if(o.vbiz) byCli[o.name]=o.vbiz; });
    return function(name, biz){ return byCli[name] || byInv[biz+'|'+name] || ''; };
  }
  var _fxNbCache=null, _fxNbStamp=null, _fxNbOpen=false;
  function _fxNoBizAssigned(){
    var st=_fxDataStamp();
    if(_fxNbStamp===st && _fxNbCache) return _fxNbCache;
    var res=_fxVbizResolver();
    var out=[];
    fxDeposits.forEach(function(e){
      if(!e.vendor || e.excluded) return;
      if(e.vbiz && /\d{3}-\d{2}-\d{5}/.test(e.vbiz)) return;
      out.push({ e:e, fix:res(e.vendor, e.biz), basis:'' });
    });
    out.sort(function(a,b){ return a.e.date<b.e.date?1:a.e.date>b.e.date?-1:0; });
    _fxNbStamp=st; _fxNbCache=out;
    return out;
  }
  window.fxNbToggle = function(){ _fxNbOpen=!_fxNbOpen; _fxRenderUnasg(); };
  window.fxNbFill = function(id){
    if(_isViewer()) return;
    var res=_fxVbizResolver();
    var d=fxDeposits.filter(function(e){ return e.id===id; })[0]; if(!d) return;
    var vb=res(d.vendor, d.biz);
    if(!vb){ showInfoModal('번호 채우기','"'+d.vendor+'" 의 사업자번호를 업체 목록·계산서 어디에서도 찾지 못했습니다.'); return; }
    d.vbiz=vb;
    _fxSaveBig().catch(function(_e){});
    _fxMetaRefresh();
    _fxRenderUnasg();
  };
  window.fxNbFillAll = function(){
    if(_isViewer()) return;
    var list=_fxNoBizAssigned().filter(function(x){ return x.fix; });
    if(!list.length){ showInfoModal('번호 일괄 채우기','지금 자료로 사업자번호를 찾을 수 있는 건이 없습니다.'); return; }
    showConfirmModal('사업자번호 일괄 채우기',
      '사업자번호 없이 배정된 입금 중 '+list.length+'건은 업체 목록·계산서에서 번호를 찾을 수 있습니다.\n'
      + '이 건들의 사업자번호를 채워 원장이 계산서와 연결되도록 할까요?\n(배정된 거래처는 바뀌지 않습니다)',
      function(){
        list.forEach(function(x){ x.e.vbiz=x.fix; });
        _fxSaveBig().catch(function(_e){});
        _fxMetaRefresh();
        _fxRenderUnasg();
        showInfoModal('번호 일괄 채우기', list.length+'건의 사업자번호를 채웠습니다.');
      }, '채우기', '#1B3A6B');
  };
  window.fxNbUnassign = function(id){
    if(_isViewer()) return;
    var d=fxDeposits.filter(function(e){ return e.id===id; })[0]; if(!d) return;
    showConfirmModal('미배정으로 되돌리기',
      d.date+' · '+_fxFmt(d.amount)+'원 · 입금자 "'+(d.payer||'')+'"\n현재 배정: '+(d.vendor||'-')+' (사업자번호 없음)\n\n'
      + '이 입금을 미배정으로 되돌리고, 이 입금자명으로 학습된 별칭도 지울까요?',
      function(){
        var k=d.biz+'|'+d.payer;
        if(fxAlias[k]===d.vendor) delete fxAlias[k];
        d.vendor=''; d.vbiz='';
        _fxSaveBig().catch(function(_e){});
        _fxSave();
        _fxMetaRefresh();
        _fxRenderUnasg();
      }, '되돌리기', '#dc2626');
  };
  function _fxNoBizBarHtml(){
    var list=_fxNoBizAssigned();
    if(!list.length) return '';
    var nFix=list.filter(function(x){ return x.fix; }).length;
    var h='<div style="margin-bottom:8px;font-size:11.5px;color:#b45309;font-weight:700">사업자번호 없이 배정된 입금 '+list.length+'건 '
      + '<button type="button" class="btn" onclick="fxNbToggle()" style="font-size:11px;padding:2px 10px;border:1px solid #b45309;color:#b45309;background:#fff;font-weight:400">'+(_fxNbOpen?'접기':'보기')+'</button>'
      + (nFix && _isAdmin() ? ' <button type="button" class="btn" onclick="fxNbFillAll()" style="font-size:11px;padding:2px 10px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B;font-weight:400">찾아지는 번호 일괄 채우기 ('+nFix+')</button>' : '')
      + ' <span style="font-weight:400;color:#9ca3af">— 사업자번호가 없으면 세금계산서와 연결되지 않습니다</span></div>';
    if(!_fxNbOpen) return h;
    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;white-space:nowrap';
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;vertical-align:middle;white-space:nowrap';
    var rows=list.slice(0,300).map(function(x){
      var e=x.e;
      var rid=String(e.id).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
      return '<tr>'
        + '<td style="'+TD+';text-align:center;color:#6b7280">'+e.biz+'</td>'
        + '<td style="'+TD+';color:#6b7280">'+e.date+'</td>'
        + '<td style="'+TD+';color:#374151">'+esc(e.payer||'')+'</td>'
        + '<td style="'+TD+';text-align:right;font-weight:700">'+_fxFmt(e.amount)+'</td>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+esc(e.vendor||'')+'</td>'
        + '<td style="'+TD+';color:'+(x.fix?'#15803d':'#b45309')+'">'+(x.fix?('찾음 '+x.fix):'번호 없음')+'</td>'
        + '<td style="'+TD+';text-align:center"><div style="display:flex;gap:6px;justify-content:center">'
        +   (x.fix&&_isAdmin() ? '<button type="button" class="btn" onclick="fxNbFill(\''+rid+'\')" style="font-size:11.5px;padding:3px 12px;border:1px solid #1B3A6B;color:#14305c;background:#f4f8fe">번호 채우기</button>' : '')
        +   (_isAdmin() ? '<button type="button" class="btn" onclick="fxNbUnassign(\''+rid+'\')" style="font-size:11.5px;padding:3px 12px;border:1px solid #dc2626;color:#dc2626;background:#fff">미배정으로</button>' : '')
        + '</div></td></tr>';
    }).join('');
    return h + '<div style="margin-bottom:10px;background:#fff;border:1px solid #f0d9b8;max-height:320px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
      + '<thead><tr><th style="'+TH+'">사업장</th><th style="'+TH+'">입금일</th><th style="'+TH+';text-align:left">입금자</th><th style="'+TH+';text-align:right">금액</th><th style="'+TH+';text-align:left">배정된 거래처</th><th style="'+TH+'">사업자번호</th><th style="'+TH+'">정리</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table>'
      + (list.length>300 ? '<div style="padding:6px 12px;font-size:11px;color:#b6bec9">… 외 '+(list.length-300)+'건</div>' : '')
      + '</div>';
  }
  // ── r154: 배정 되돌리기 ────────────────────────────────""", 1, 'NOBIZINFRA')

    # ── 2. fxAssignDep: 사업자번호 확인 후 배정 ──
    s = rep(s,
        """    // r154: 되돌리기용 배정 기록 (vendor 를 바꾸기 전에 남겨야 한다)
    var _bat=_fxAsgNewBat();
    var _akey = d.payer ? (d.biz+'|'+d.payer) : '';
    var _aprev = _akey ? (Object.prototype.hasOwnProperty.call(fxAlias,_akey) ? fxAlias[_akey] : null) : null;
    var _u=_fxAsgStamp(d, _bat);
    if(_akey){ _u.a=_akey; _u.pa=_aprev; }
    d.vendor=v; d.vbiz=_fxClientVbiz(v, d.biz);
    if(d.payer) fxAlias[d.biz+'|'+d.payer]=v;
    fxDeposits.forEach(function(e){
      if(e!==d && !e.vendor && !e.excluded && e.biz===d.biz && e.payer===d.payer){ _fxAsgStamp(e, _bat); e.vendor=v; e.vbiz=d.vbiz; }
    });
    _fxAsgPrune();
    _fxSaveBig().catch(function(_e){});
    _fxSave();
    _fxMetaRefresh();
    _fxRenderUnasg();
  };""",
        r"""    // r155: 사업자번호 확인 — 미수현황은 세금계산서와 맞추는 자료이므로
    //  번호가 없으면 어떤 계산서와도 연결되지 않는다. (업체목록 -> 계산서 순으로 조회)
    var _vb=_fxClientVbiz(v, d.biz);
    var _fin=v;
    var _go=function(){
      // r154: 되돌리기용 배정 기록 (vendor 를 바꾸기 전에 남겨야 한다)
      var _bat=_fxAsgNewBat();
      var _akey = d.payer ? (d.biz+'|'+d.payer) : '';
      var _aprev = _akey ? (Object.prototype.hasOwnProperty.call(fxAlias,_akey) ? fxAlias[_akey] : null) : null;
      var _u=_fxAsgStamp(d, _bat);
      if(_akey){ _u.a=_akey; _u.pa=_aprev; }
      d.vendor=_fin; d.vbiz=_vb;
      if(d.payer) fxAlias[d.biz+'|'+d.payer]=_fin;
      fxDeposits.forEach(function(e){
        if(e!==d && !e.vendor && !e.excluded && e.biz===d.biz && e.payer===d.payer){ _fxAsgStamp(e, _bat); e.vendor=_fin; e.vbiz=_vb; }
      });
      _fxAsgPrune();
      _fxSaveBig().catch(function(_e){});
      _fxSave();
      _fxMetaRefresh();
      _fxRenderUnasg();
    };
    if(_vb){ _go(); return; }
    var _basis=_fxHasLedgerBasis(v, d.biz);
    if(!_basis){
      showInfoModal('거래처 지정',
        '"'+v+'" 은(는) 사업자번호가 없습니다.\n\n'
        + '미수현황은 세금계산서와 맞춰보는 자료입니다. 사업자번호가 없으면 세금계산서가\n'
        + '발행될 수 없으므로, 이 입금은 어떤 계산서와도 연결되지 않습니다.\n\n'
        + '일정 > 업체에서 "'+v+'" 의 사업자번호를 등록한 뒤 다시 지정해 주세요.\n'
        + '(회사 수금이 아니라면 제외 처리하세요)');
      if(el){ el.focus(); try{ fxUnDdRender(i); }catch(_e2){} }
      return;
    }
    showConfirmModal('사업자번호 없는 거래처',
      '"'+v+'" 은(는) 업체 목록·세금계산서 어디에서도 사업자번호를 찾지 못했습니다.\n'
      + '다만 이 거래처에는 '+_basis+'(으)로 미수가 잡혀 있습니다.\n\n'
      + '사업자번호가 없으면 세금계산서와는 맞출 수 없고, '+_basis+' 잔액에만 반영됩니다.\n\n'
      + '그래도 배정할까요?',
      _go, '배정', '#b45309');
  };""", 1, 'ASSIGNVBIZ')

    # ── 3. 자동 배정 재실행도 같은 기준 ──
    s = rep(s,
        """    var hits=[];
    fxDeposits.forEach(function(e){
      if(e.vendor || e.excluded) return;
      var v=_fxResolveVendor(e.biz, e.payer);
      if(v) hits.push([e,v]);
    });""",
        r"""    var hits=[], skipped=0;
    var _res=_fxVbizResolver();
    fxDeposits.forEach(function(e){
      if(e.vendor || e.excluded) return;
      var v=_fxResolveVendor(e.biz, e.payer);
      if(!v) return;
      // r155: 사업자번호도 없고 기초이월·조정·계산서 근거도 없으면 자동 배정하지 않는다
      var vb=_res(v, e.biz);
      if(!vb && !_fxHasLedgerBasis(v, e.biz)){ skipped++; return; }
      hits.push([e,v]);
    });""", 1, 'REASSIGNVBIZ')
    s = rep(s,
        "    if(!hits.length){ showInfoModal('자동 배정 재실행','현재 규칙(별칭·업체명·대표자명)으로 새로 배정되는 미배정·보류 입금이 없습니다.'); return; }",
        "    if(!hits.length){ showInfoModal('자동 배정 재실행','현재 규칙(별칭·업체명·대표자명)으로 새로 배정되는 미배정·보류 입금이 없습니다.'"
        "\n      + (skipped ? '\\n\\n(사업자번호가 없고 기초이월·조정·계산서 근거도 없어 건너뛴 건 '+skipped+'건)' : '')); return; }",
        1, 'REASSIGNMSG0')
    s = rep(s,
        "      '별칭·업체명·대표자명 규칙으로 미배정·보류 입금 '+hits.length+'건이 배정됩니다.\\n(대표자명은 동명이인이 없을 때만 매칭됩니다)\\n\\n계속할까요?',",
        "      '별칭·업체명·대표자명 규칙으로 미배정·보류 입금 '+hits.length+'건이 배정됩니다.\\n(대표자명은 동명이인이 없을 때만 매칭됩니다)'"
        "\n      + (skipped ? '\\n\\n사업자번호가 없고 기초이월·조정·계산서 근거도 없는 '+skipped+'건은 건너뜁니다.' : '')"
        "\n      + '\\n\\n계속할까요?',",
        1, 'REASSIGNMSG1')

    # ── 4. 점검 패널 배치 + 영역 표시 조건 ──
    s = rep(s,
        "    if(!_fxUnList.length && !_fxHeldList.length && !_fxExList.length && !Object.keys(fxAlias).length && !_fxAsgBatches().length){ host.innerHTML=''; return; }",
        "    if(!_fxUnList.length && !_fxHeldList.length && !_fxExList.length && !Object.keys(fxAlias).length && !_fxAsgBatches().length && !_fxNoBizAssigned().length){ host.innerHTML=''; return; }",
        1, 'UNASGGUARD2')
    s = rep(s,
        "    html += _fxAsgBarHtml();   // r154: 최근 거래처 배정 / 되돌리기",
        "    html += _fxNoBizBarHtml();  // r155: 사업자번호 없이 배정된 입금 점검\n"
        "    html += _fxAsgBarHtml();   // r154: 최근 거래처 배정 / 되돌리기",
        1, 'NBMOUNT')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r155(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r154 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r154 2026-08-26 -->', '<!-- test build r155 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
