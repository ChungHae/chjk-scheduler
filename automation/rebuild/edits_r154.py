# -*- coding: utf-8 -*-
# r154: [미배정 입금 배정 — 없는 거래처 배정 차단 + 배정 되돌리기]
#
#  요청 2가지:
#   (1) 등록되지 않은 거래처명을 입력하고 엔터를 치면, 있지도 않은 거래처명으로
#       그대로 배정되어 버린다.
#   (2) 마우스가 잘못 더블클릭돼서 모르는 거래처로 배정됐는데, 무엇으로 배정됐는지
#       알 수도 없고 되돌릴 수도 없다.
#
#  (1) 원인: fxAssignDep 이 이렇게 되어 있었다.
#        var mm = opts.filter(...검색...);
#        if(mm.length) v = mm[0].name;     // 후보가 있으면 "첫 항목" 을 말없이 선택
#        d.vendor = v;                     // 후보가 하나도 없으면 입력한 생 텍스트가 그대로 배정
#      즉 (a) 후보 0곳이면 존재하지 않는 이름으로 배정되고,
#          (b) 후보가 여러 곳이어도 임의로 첫 번째를 골라버린다(오배정의 주범).
#
#  (1) 수정: 정확히 일치하는 업체가 없을 때
#        후보 0곳  -> 배정하지 않고 안내. 단 계산서에만 있는 거래처와 하나로 좁혀지면
#                     기존 '업체 등록 + 배정' 흐름(fxPickNewVend)으로 넘겨줌.
#        후보 1곳  -> 그 업체로 배정(모호하지 않음).
#        후보 여러곳 -> 이름 앞에서 일치하는 곳이 딱 1곳이면 그곳, 아니면 배정하지 않고
#                     후보 목록을 보여주며 목록에서 고르라고 안내.
#      (드롭다운에서 클릭해 고르는 경로는 정확히 일치하므로 기존과 동일하게 동작)
#
#  (2) 수정: 배정 시점에 입금 자료 자체에 "되돌리기 정보" 를 함께 남긴다.
#        asgBat(배정 묶음 id) / asgAt(시각) / asgBy(작업자) / asgU(배정 직전 상태)
#      asgU 에는 이전 거래처·사업자번호·보류여부와, 그 배정으로 학습된 별칭 키와
#      별칭의 이전 값까지 담는다. 되돌리면 별칭도 배정 전 상태로 정확히 복원된다
#      (자동 배정 재실행은 별칭을 학습하지 않으므로 별칭을 건드리지 않는다).
#      새 저장소 키를 만들지 않고 입금 자료에 얹기 때문에 동기화 배선을 안 건드림.
#      자료가 무한히 커지지 않도록 최근 50묶음까지만 정보를 유지(그 이전은 자동 삭제).
#
#      화면: 자료 업로드 탭 맨 위에 "최근 거래처 배정 N건 [보기 / 되돌리기]" 줄을 추가.
#      펼치면 배정 시각·거래처·건수·입금자가 보이고 묶음별 [되돌리기] 버튼이 있다.
#      한 번의 배정이 같은 입금자명 여러 건을 함께 배정하므로, 되돌리기도 묶음 단위.
#
#  대상: fxAssignDep(지정 버튼·엔터·드롭다운 선택) 과 fxReassignRun(자동 배정 재실행).
#        fxPickCrossVend(사업장 이동 배정)는 자체 확인창이 있고 사업장까지 바꾸므로 제외
#        (그 건은 기존대로 원장 화면의 입금 재배정으로 되돌린다).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R154 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r154(s, path):
    # ── 1. 되돌리기 인프라 + 패널 (fxAssignDep 앞에 삽입) ──
    s = rep(s,
        "  window.fxAssignDep = function(i){",
        r"""  // ── r154: 배정 되돌리기 ────────────────────────────────
  //  배정 직전 상태를 입금 자료에 얹어 둔다(별도 저장소 키 없이 입금 블롭에 함께 저장).
  var _fxAsgOpen=false, _fxAsgSeq=0;
  var _FX_ASG_KEEP=50;   // 최근 몇 묶음까지 되돌리기 정보를 유지할지
  function _fxAsgNewBat(){ return 'B'+Date.now()+'.'+(++_fxAsgSeq); }
  //  반드시 vendor/vbiz/held 를 바꾸기 "전" 에 호출할 것
  function _fxAsgStamp(e, bat){
    e.asgBat=bat; e.asgAt=Date.now(); e.asgBy=(_authUser&&_authUser.name)||'';
    var u={ v:e.vendor||'', b:e.vbiz||'' };
    if(e.held) u.h=1;
    e.asgU=u;
    return u;
  }
  function _fxAsgBatches(){
    var m={};
    fxDeposits.forEach(function(e){
      if(!e.asgBat) return;
      var b=m[e.asgBat];
      if(!b) b=m[e.asgBat]={ bat:e.asgBat, at:e.asgAt||0, by:e.asgBy||'', items:[] };
      if((e.asgAt||0)>b.at) b.at=e.asgAt||0;
      b.items.push(e);
    });
    return Object.keys(m).map(function(k){ return m[k]; }).sort(function(a,b){ return b.at-a.at; });
  }
  function _fxAsgClear(e){ delete e.asgBat; delete e.asgAt; delete e.asgBy; delete e.asgU; }
  function _fxAsgPrune(){
    var bs=_fxAsgBatches();
    if(bs.length<=_FX_ASG_KEEP) return;
    bs.slice(_FX_ASG_KEEP).forEach(function(b){ b.items.forEach(_fxAsgClear); });
  }
  function _fxAsgVendors(b){
    var seen={}, out=[];
    b.items.forEach(function(e){ var v=e.vendor||'(미배정)'; if(!seen[v]){ seen[v]=1; out.push(v); } });
    return out;
  }
  function _fxAsgWhen(ms){
    if(!ms) return '';
    var d=new Date(ms);
    return _fxD(d)+' '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
  }
  window.fxAsgToggle = function(){ _fxAsgOpen=!_fxAsgOpen; _fxRenderUnasg(); };
  window.fxAsgUndo = function(bat){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 사용할 수 없습니다.'); return; }
    var b=_fxAsgBatches().filter(function(x){ return x.bat===bat; })[0];
    if(!b){ showInfoModal('배정 되돌리기','해당 배정 기록을 찾지 못했습니다. 화면을 새로 불러온 뒤 다시 시도해 주세요.'); return; }
    var vs=_fxAsgVendors(b);
    var head = vs.length===1 ? ('"'+vs[0]+'"(으)로 배정한') : ('거래처 '+vs.length+'곳으로 배정한');
    var lines=b.items.slice(0,5).map(function(e){
      return ' · '+e.date+' · '+_fxFmt(e.amount)+'원 · 입금자 "'+(e.payer||'')+'" → '+(e.vendor||'');
    }).join('\n');
    var alias=b.items.some(function(e){ return e.asgU && e.asgU.a; });
    showConfirmModal('배정 되돌리기',
      head+' 입금 '+b.items.length+'건을 배정 전 상태로 되돌립니다.\n\n'
      + lines + (b.items.length>5 ? '\n … 외 '+(b.items.length-5)+'건' : '')
      + (alias ? '\n\n이 배정으로 학습된 별칭(입금자명 → 거래처)도 배정 전 상태로 되돌립니다.' : '')
      + '\n\n계속할까요?',
      function(){
        b.items.forEach(function(e){
          var u=e.asgU||{};
          if(u.a){
            if(u.pa===null || u.pa===undefined) delete fxAlias[u.a];
            else fxAlias[u.a]=u.pa;
          }
          e.vendor=u.v||''; e.vbiz=u.b||'';
          if(u.h) e.held=true; else delete e.held;
          _fxAsgClear(e);
        });
        _fxSaveBig().catch(function(_e){});
        _fxSave();
        _fxMetaRefresh();
        _fxRenderUnasg();
        showInfoModal('배정 되돌리기', b.items.length+'건을 배정 전 상태로 되돌렸습니다.');
      }, '되돌리기', '#dc2626');
  };
  function _fxAsgBarHtml(){
    var bs=_fxAsgBatches();
    if(!bs.length) return '';
    var h='<div style="margin-bottom:8px;font-size:11.5px;color:#5b7ba6;font-weight:700">최근 거래처 배정 '+bs.length+'건 '
      + '<button type="button" class="btn" onclick="fxAsgToggle()" style="font-size:11px;padding:2px 10px;border:1px solid #5b7ba6;color:#5b7ba6;background:#fff;font-weight:400">'+(_fxAsgOpen?'접기':'보기 / 되돌리기')+'</button>'
      + ' <span style="font-weight:400;color:#9ca3af">— 잘못 배정했으면 여기서 배정 전으로 되돌릴 수 있습니다</span></div>';
    if(!_fxAsgOpen) return h;
    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;white-space:nowrap';
    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;vertical-align:middle';
    var rows=bs.map(function(b){
      var vs=_fxAsgVendors(b);
      var vtxt = vs.length===1 ? esc(vs[0]) : (esc(vs[0])+' <span style="color:#9ca3af;font-weight:400">외 '+(vs.length-1)+'곳</span>');
      var e0=b.items[0];
      var rb=String(b.bat).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
      return '<tr>'
        + '<td style="'+TD+';text-align:center;color:#6b7280;white-space:nowrap">'+_fxAsgWhen(b.at)+'</td>'
        + '<td style="'+TD+';color:#9ca3af;text-align:center">'+esc(b.by||'')+'</td>'
        + '<td style="'+TD+';font-weight:700;color:#14305c">'+vtxt+'</td>'
        + '<td style="'+TD+';color:#6b7280">'+esc(e0.payer||'')+(b.items.length>1?' <span style="color:#9ca3af">외 '+(b.items.length-1)+'건</span>':'')+'</td>'
        + '<td style="'+TD+';text-align:right;font-weight:700">'+_fxFmt(b.items.reduce(function(a,e){ return a+(e.amount||0); },0))+'</td>'
        + '<td style="'+TD+';text-align:center"><button type="button" class="btn" onclick="fxAsgUndo(\''+rb+'\')" style="font-size:11.5px;padding:3px 12px;border:1px solid #5b7ba6;color:#5b7ba6;background:#fff">되돌리기</button></td>'
        + '</tr>';
    }).join('');
    return h + '<div style="margin-bottom:10px;background:#fff;border:1px solid #d6e4f5;max-height:300px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
      + '<thead><tr><th style="'+TH+'">배정 시각</th><th style="'+TH+'">작업자</th><th style="'+TH+';text-align:left">배정한 거래처</th><th style="'+TH+';text-align:left">입금자</th><th style="'+TH+';text-align:right">금액</th><th style="'+TH+'">되돌리기</th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div>';
  }
  window.fxAssignDep = function(i){""", 1, 'UNDOINFRA')

    # ── 2. fxAssignDep: 없는 거래처 차단 + 배정 기록 ──
    s = rep(s,
        """    var opts=_fxClientOpts();
    if(!opts.some(function(o){ return o.name===v; })){
      var q=v.toLowerCase();
      var mm=opts.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
      if(mm.length) v=mm[0].name;   // 검색 첫 항목 자동 선택 (프로젝트 업체 검색과 동일 규칙)
    }
    d.vendor=v; d.vbiz=_fxClientVbiz(v, d.biz);
    if(d.payer) fxAlias[d.biz+'|'+d.payer]=v;
    fxDeposits.forEach(function(e){
      if(e!==d && !e.vendor && !e.excluded && e.biz===d.biz && e.payer===d.payer){ e.vendor=v; e.vbiz=d.vbiz; }
    });
    _fxSaveBig().catch(function(_e){});
    _fxSave();
    _fxMetaRefresh();
    _fxRenderUnasg();
  };""",
        r"""    var opts=_fxClientOpts();
    // r154: 등록된 거래처로 확정되지 않으면 배정하지 않는다 (예전에는 후보 첫 항목을
    //  말없이 고르거나, 후보가 없으면 입력한 생 텍스트를 그대로 배정해 버렸다)
    if(!opts.some(function(o){ return o.name===v; })){
      var q=v.toLowerCase();
      var mm=opts.filter(function(o){ return o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
      var _reopen=function(){ if(el){ el.focus(); try{ fxUnDdRender(i); }catch(_e){} } };
      if(mm.length===1){
        v=mm[0].name;
      } else if(mm.length>1){
        var nv=_fxNormName(v);
        var pre=mm.filter(function(o){ return _fxNormName(o.name).indexOf(nv)===0; });
        if(pre.length===1){ v=pre[0].name; }
        else {
          showInfoModal('거래처 지정',
            '"'+v+'" (으)로 검색되는 거래처가 '+mm.length+'곳입니다.\n\n'
            + mm.slice(0,6).map(function(o){ return ' · '+o.name+(o.vbiz?' ('+o.vbiz+')':''); }).join('\n')
            + (mm.length>6 ? '\n … 외 '+(mm.length-6)+'곳' : '')
            + '\n\n어느 곳인지 확정할 수 없어 배정하지 않았습니다.\n아래 목록에서 정확한 거래처를 선택해 주세요.');
          _reopen(); return;
        }
      } else {
        // 등록된 업체에 없음 — 계산서에만 있는 거래처로 하나 좁혀지면 등록+배정 흐름으로
        var invo=_fxInvOnlyOpts(d.biz).filter(function(o){ return o.name===v || o.name.toLowerCase().indexOf(q)>=0 || (o.vbiz && o.vbiz.indexOf(q)>=0); });
        if(invo.length===1){ fxPickNewVend(i, invo[0].name, invo[0].vbiz||''); return; }
        showInfoModal('거래처 지정',
          '"'+v+'" 은(는) 등록된 거래처가 아닙니다.\n\n'
          + (invo.length>1 ? '계산서에만 있는 비슷한 거래처가 '+invo.length+'곳 있습니다 — 아래 목록의 \'계산서에만 있는 거래처\' 칸에서 선택하면 업체 등록 후 배정됩니다.\n\n' : '')
          + '아래 목록에서 거래처를 선택하거나, 새 거래처라면 일정 > 업체에 먼저 등록한 뒤 지정해 주세요.\n'
          + '(등록되지 않은 이름으로는 배정하지 않습니다)');
        _reopen(); return;
      }
    }
    // r154: 되돌리기용 배정 기록 (vendor 를 바꾸기 전에 남겨야 한다)
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
  };""", 1, 'ASSIGNGUARD')

    # ── 3. 자동 배정 재실행도 되돌릴 수 있게 ──
    s = rep(s,
        "        hits.forEach(function(h){ var e=h[0]; e.vendor=h[1]; e.vbiz=_fxClientVbiz(h[1], e.biz); delete e.held; });\n"
        "        _fxSaveBig().catch(function(_e){});",
        "        var _bat=_fxAsgNewBat();\n"
        "        hits.forEach(function(h){ var e=h[0]; _fxAsgStamp(e, _bat); e.vendor=h[1]; e.vbiz=_fxClientVbiz(h[1], e.biz); delete e.held; });\n"
        "        _fxAsgPrune();\n"
        "        _fxSaveBig().catch(function(_e){});", 1, 'REASSIGNLOG')
    s = rep(s,
        "        showInfoModal('자동 배정', hits.length+'건을 배정했습니다. 잘못 배정된 건은 원장의 연필 버튼으로 되돌릴 수 있습니다.');",
        "        showInfoModal('자동 배정', hits.length+'건을 배정했습니다.\\n잘못 배정됐다면 이 화면 위쪽 \\'최근 거래처 배정\\' 에서 한 번에 되돌릴 수 있습니다.');",
        1, 'REASSIGNMSG')

    # ── 4. 화면: 배정 기록만 있어도 영역이 보이도록 + 패널 배치 ──
    s = rep(s,
        "    if(!_fxUnList.length && !_fxHeldList.length && !_fxExList.length && !Object.keys(fxAlias).length){ host.innerHTML=''; return; }",
        "    if(!_fxUnList.length && !_fxHeldList.length && !_fxExList.length && !Object.keys(fxAlias).length && !_fxAsgBatches().length){ host.innerHTML=''; return; }",
        1, 'UNASGGUARD')
    s = rep(s,
        "    var html='';\n    if(_fxUnList.length){\n      fxUnDdHide();",
        "    var html='';\n    html += _fxAsgBarHtml();   // r154: 최근 거래처 배정 / 되돌리기\n    if(_fxUnList.length){\n      fxUnDdHide();",
        1, 'PANELMOUNT')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r154(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r153 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r153 2026-08-26 -->', '<!-- test build r154 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
