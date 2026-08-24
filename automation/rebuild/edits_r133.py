# -*- coding: utf-8 -*-
# r133: [미배정 매칭 — 업체 목록 기준으로 전환 + 별칭표 관리]
#  사용자 보고: 홈택스 상호 기반 목록이라 "(자) 동화"/"(자)동화" 같은 표기 변형이
#  중복으로 뜨고, 그 이름으로 별칭이 학습되어 별칭표가 엉망이 됨.
#  1) 거래처 선택 드롭다운 = 일정 > 업체 탭에 등록된 업체만 (이름+사업자번호)
#  2) 지정 시 vbiz = 업체의 사업자번호 → 홈택스 상호 표기가 달라도 원장은
#     사업자번호로 정확히 연결
#  3) 자동 배정(_fxResolveVendor)도 업체명 직접 일치 인정
#  4) 별칭표 관리 패널: 목록 보기 / 개별 삭제(해당 입금 미배정 복귀) /
#     업로드 배정 전체 취소 / 별칭 다시 적용 (관리자)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R133 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r133(s, path):
    # ── (1) 업체 목록 헬퍼 + 별칭 관리 핸들러 ──
    HELPERS = r"""  // ── r133: 일정>업체 목록 기준 거래처 옵션 ──
  function _fxClientOpts(){
    var seen={}, out=[];
    (allClients()||[]).forEach(function(c){
      if(!c || !c[0]) return;
      var n=String(c[0]).trim(); if(!n || seen[n]) return; seen[n]=1;
      var d=String(c[1]||'').replace(/[^0-9]/g,'');
      var vb = d.length===10 ? (d.slice(0,3)+'-'+d.slice(3,5)+'-'+d.slice(5)) : '';
      out.push({name:n, vbiz:vb});
    });
    out.sort(function(a,b){ return a.name.localeCompare(b.name,undefined,{numeric:true,sensitivity:'base'}); });
    return out;
  }
  function _fxClientVbiz(name, biz){
    var o=_fxClientOpts().find(function(x){ return x.name===name; });
    return (o && o.vbiz) || _fxVbizOf(biz, name) || '';
  }
  var _fxAliasOpen=false;
  window.fxAliasToggle = function(){ _fxAliasOpen=!_fxAliasOpen; _fxRenderUnasg(); };
  window.fxAliasDel = function(k){
    if(!_isAdmin()) return;
    var p=String(k).split('|'), biz=p[0], payer=p.slice(1).join('|'), tgt=fxAlias[k];
    if(tgt===undefined) return;
    showConfirmModal('별칭 삭제', biz+' · "'+payer+'" → '+tgt+'\n\n이 별칭을 삭제하고, 이 별칭으로 배정된 업로드 입금을 미배정으로 되돌릴까요?', function(){
      delete fxAlias[k];
      fxDeposits.forEach(function(e){ if(e.src==='upload' && e.biz===biz && e.payer===payer && e.vendor===tgt){ e.vendor=''; e.vbiz=''; } });
      _fxSave();
      _fxSaveBig().catch(function(_e){});
      _fxMetaRefresh();
      _fxRenderUnasg();
    });
  };
  window.fxUnassignAll = function(){
    if(!_isAdmin()) return;
    var n=fxDeposits.filter(function(e){ return e.src==='upload' && e.vendor; }).length;
    if(!n){ showInfoModal('배정 취소','업로드로 들어온 배정 입금이 없습니다.'); return; }
    showConfirmModal('배정 전체 취소', '업로드로 들어온 입금 '+n+'건의 거래처 배정을 모두 취소하고 미배정으로 되돌립니다.\n(별칭표는 그대로 남습니다 — "별칭 다시 적용"으로 재배정할 수 있습니다)\n\n계속할까요?', function(){
      fxDeposits.forEach(function(e){ if(e.src==='upload' && e.vendor){ e.vendor=''; e.vbiz=''; } });
      _fxSaveBig().catch(function(_e){});
      _fxMetaRefresh();
      _fxRenderUnasg();
    }, '전체 취소', '#dc2626');
  };
  window.fxReassignAll = function(){
    if(!_isAdmin()) return;
    var n=0;
    fxDeposits.forEach(function(e){
      if(e.vendor || e.excluded) return;
      var v=_fxResolveVendor(e.biz, e.payer);
      if(v){ e.vendor=v; e.vbiz=_fxClientVbiz(v, e.biz); n++; }
    });
    if(n){ _fxSaveBig().catch(function(_e){}); }
    _fxMetaRefresh();
    _fxRenderUnasg();
    showInfoModal('별칭 다시 적용', n ? (n+'건이 별칭표 기준으로 재배정되었습니다.') : '별칭표로 배정할 수 있는 미배정 입금이 없습니다.');
  };
"""
    s = rep(s, "  // ── r132: 미배정 거래처 선택 — 앱 공통 드롭다운 ──", HELPERS + "  // ── r132: 미배정 거래처 선택 — 앱 공통 드롭다운 ──", 1, 'HELPERS')

    # ── (2) 드롭다운 소스 = 업체 목록 ──
    s = rep(s, "    var opts=_fxVendorOpts(e.biz);", "    var opts=_fxClientOpts();", 1, 'DDSRC')
    s = rep(s, "'+(q?'일치하는 거래처 없음':'등록된 거래처 없음')+'", "'+(q?'일치하는 업체 없음':'일정 > 업체에 등록된 업체가 없습니다')+'", 1, 'DDEMPTY')

    # ── (3) 지정: 업체 목록 기준 + 사업자번호 연결 ──
    s = rep(s, "    var opts=_fxVendorOpts(d.biz);", "    var opts=_fxClientOpts();", 1, 'ASSRC')
    s = rep(s, "    d.vendor=v; d.vbiz=_fxVbizOf(d.biz, v);",
            "    d.vendor=v; d.vbiz=_fxClientVbiz(v, d.biz);", 1, 'ASVBIZ')

    # ── (4) 자동 배정: 업체명 직접 일치 인정 ──
    s = rep(s, """  function _fxResolveVendor(biz, payer){
    var p=String(payer||'').trim(); if(!p) return null;
    if(fxAlias[biz+'|'+p]) return fxAlias[biz+'|'+p];
    if(_fxVendorNames(biz).indexOf(p)>=0) return p;
    return null;
  }""",
            """  function _fxResolveVendor(biz, payer){
    var p=String(payer||'').trim(); if(!p) return null;
    if(fxAlias[biz+'|'+p]) return fxAlias[biz+'|'+p];
    if(typeof allClients==='function' && (allClients()||[]).some(function(c){ return c && String(c[0]).trim()===p; })) return p;
    if(_fxVendorNames(biz).indexOf(p)>=0) return p;
    return null;
  }""", 1, 'RESOLVE')

    # ── (5) 별칭표 관리 패널 ──
    s = rep(s, "    if(!_fxUnList.length && !_fxExList.length){ host.innerHTML=''; return; }",
            "    if(!_fxUnList.length && !_fxExList.length && !Object.keys(fxAlias).length){ host.innerHTML=''; return; }", 1, 'EMPTYCOND')
    ALIAS_PANEL = r"""    var akeys=Object.keys(fxAlias).sort();
    if(akeys.length || _isAdmin()){
      html += '<div style="margin-top:8px;font-size:11.5px;color:#9ca3af">별칭표 '+akeys.length+'건 '
        + '<button type="button" class="btn" onclick="fxAliasToggle()" style="font-size:11px;padding:2px 10px;border:1px solid #d6deea;color:#6b7280;background:#fff">'+(_fxAliasOpen?'접기':'관리')+'</button>'
        + (_isAdmin()
          ? ' <button type="button" class="btn" onclick="fxReassignAll()" style="font-size:11px;padding:2px 10px;border:1px solid #5b7ba6;color:#5b7ba6;background:#fff">별칭 다시 적용</button>'
            + ' <button type="button" class="btn" onclick="fxUnassignAll()" style="font-size:11px;padding:2px 10px;border:1px solid #dc2626;color:#dc2626;background:#fff">업로드 배정 전체 취소</button>'
          : '')
        + '</div>';
      if(_fxAliasOpen && akeys.length){
        var TRASH2='<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>';
        var arows=akeys.map(function(k){
          var p=k.split('|');
          var rk=String(k).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
          return '<tr>'
            + '<td style="'+TD+';text-align:center;color:#6b7280">'+esc(p[0])+'</td>'
            + '<td style="'+TD+';color:#374151">'+esc(p.slice(1).join('|'))+'</td>'
            + '<td style="'+TD+';font-weight:700;color:#14305c">→ '+esc(fxAlias[k])+'</td>'
            + '<td style="'+TD+';text-align:center">'+(_isAdmin()?'<button type="button" onclick="fxAliasDel(\''+rk+'\')" data-tip="별칭 삭제" aria-label="별칭 삭제" style="border:none;background:transparent;cursor:pointer;padding:0 2px">'+TRASH2+'</button>':'')+'</td>'
            + '</tr>';
        }).join('');
        html += '<div style="margin-top:6px;background:#fff;border:1px solid #e3e9f0;max-height:300px;overflow:auto"><table style="width:100%;border-collapse:collapse">'
          + '<thead><tr><th style="'+TH+'">사업장</th><th style="'+TH+';text-align:left">입금자명</th><th style="'+TH+';text-align:left">거래처</th><th style="'+TH+'">삭제</th></tr></thead>'
          + '<tbody>'+arows+'</tbody></table></div>';
      }
    }
    host.innerHTML=html;"""
    s = rep(s, "    host.innerHTML=html;", ALIAS_PANEL, 1, 'PANEL')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r133(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r132 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r132 2026-08-24 -->', '<!-- test build r133 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
