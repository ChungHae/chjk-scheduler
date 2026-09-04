# -*- coding: utf-8 -*-
# r176: '업체명 불일치'와 '중복 거래처 후보'에 [그대로 두기] 추가
#
#  사용자 요청: 두 패널 모두 "고치지 않고 지금 이대로 넘어가는" 버튼이 있으면 좋겠다.
#
#  왜 필요한가: 두 목록 다 '후보'일 뿐 확정이 아니다. 실제로는 다른 회사인데 이름이 비슷해
#    잡히거나(중복 후보), 원장 이름을 일부러 그대로 두고 싶은 경우(업체명 불일치)가 있다.
#    지금은 고치는 것 말고 선택지가 없어서 같은 후보를 볼 때마다 매번 다시 판단해야 했다.
#
#  방식: 판단 결과를 '그대로 두기' 목록(fxKeepAs)에 남긴다.
#    · 저장 키 하나(sched_fx_keepas)에 두 종류를 함께 담는다 — 접두어로 구분.
#        업체명 불일치 : 'NM|<사업자번호10자리>|<옛이름>|<새이름>'
#        중복 후보     : 'DUP|<원장키A>\t<원장키B>'   (두 키를 정렬해 순서 무관)
#    · 다른 설정과 같은 경로로 동기화·백업된다(등록 지점 7곳 — 아래 (0) 참고).
#
#  ★ 되돌릴 수 있어야 한다: 그대로 둔 항목은 사라지지 않고 패널 아래 '그대로 둔 N곳' 칸에
#    남아 [다시 보기] 로 언제든 되살릴 수 있다. 모두 그대로 두어 활성 후보가 0이 되어도
#    칩은 회색으로 남는다 — 안 그러면 패널을 열 방법이 없어져 결정을 되돌릴 수 없다.
#
#  ★ 이름이 바뀌면 다시 뜬다: 'NM' 키에 옛이름·새이름이 모두 들어가므로, 업체 목록의 이름이
#    또 바뀌면 키가 달라져 새 후보로 다시 나타난다(예전 판단이 새 상황을 덮지 않는다).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R176 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

KEEP_HELPERS = r'''  // ── r176: '그대로 두기' 판단 보관 ──
  //  '업체명 불일치'와 '중복 거래처 후보'는 확정이 아니라 후보다. 고치지 않기로 한 판단도
  //  남겨 두어야 같은 후보를 볼 때마다 다시 판단하지 않는다. 되살리기는 항상 가능하다.
  function _fxKeepHas(k){ return fxKeepAs.indexOf(k)>=0; }
  function _fxKeepAdd(k){ if(!_fxKeepHas(k)){ fxKeepAs.push(k); _fxSave(); } }
  function _fxKeepDel(k){ var i=fxKeepAs.indexOf(k); if(i>=0){ fxKeepAs.splice(i,1); _fxSave(); } }
  function _fxKeepDelPrefix(p){
    var before=fxKeepAs.length;
    var rest=fxKeepAs.filter(function(k){ return String(k).indexOf(p)!==0; });
    if(rest.length!==before){ fxKeepAs.length=0; rest.forEach(function(k){ fxKeepAs.push(k); }); _fxSave(); }
    return before-fxKeepAs.length;
  }
  function _fxKeepBtn(onclick){
    return '<button type="button" class="btn" onclick="'+onclick+'" style="font-size:11px;padding:2px 10px;border:1px solid #c8d2de;color:#6b7280;background:#fff">그대로 두기</button>';
  }
  function _fxUnkeepBtn(onclick){
    return '<button type="button" class="btn" onclick="'+onclick+'" style="font-size:11px;padding:2px 10px;border:1px solid #c8d2de;color:#5b7ba6;background:#fff">다시 보기</button>';
  }
  //  그대로 둔 항목을 보여 주는 공통 꼬리말 — 결정을 되돌릴 통로다.
  function _fxKeptFootHtml(rows, allOnclick){
    if(!rows.length) return '';
    return '<div style="padding:8px 14px;border-top:1px solid #e3e9f0;background:#fafbfc;font-size:11.5px;color:#8a94a6">'
      + '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:'+(rows.length?'6px':'0')+'">'
      +   '<b style="color:#6b7280;font-weight:600">그대로 두기로 한 '+rows.length+'곳</b>'
      +   '<span>— 목록에서 빼 두었을 뿐 자료는 그대로입니다.</span>'
      +   '<span style="flex:1"></span>'
      +   _fxUnkeepBtn(allOnclick+'()')
      + '</div>'
      + rows.join('')
      + '</div>';
  }
'''

NM_NEW = r'''  var _fxNmOpen=false;
  function _fxNmKey(m){ return 'NM|'+String(m.vbiz||'').replace(/[^0-9]/g,'')+'|'+m.old+'|'+m.neu; }
  //  withKept=true 면 '그대로 두기' 한 것까지 모두 돌려준다(꼬리말·칩 계산용).
  function _fxNameMismatch(region, withKept){
    var out=[], seen={};
    var cliNames={}, byBiz={};
    try{
      (allClients()||[]).forEach(function(c){
        if(!c || !c[0]) return;
        var nm=String(c[0]).trim(); if(!nm) return;
        cliNames[nm]=1;
        var bd=String(c[1]||'').replace(/[^0-9]/g,'');
        if(bd.length!==10) return;
        if(!byBiz[bd]) byBiz[bd]=[];
        if(byBiz[bd].indexOf(nm)<0) byBiz[bd].push(nm);   // 같은 사업자번호에 이름이 여러 개면 확정 불가
      });
    }catch(_e){ return out; }
    _fxLedgers(region).forEach(function(x){
      var nm=String(x.name||'').trim();
      if(!nm || !x.vbiz || !/\d{3}-\d{2}-\d{5}/.test(x.vbiz)) return;
      if(cliNames[nm]) return;                     // 원장 이름이 업체 목록에 있으면 그대로 둔다
      var cand=byBiz[String(x.vbiz).replace(/[^0-9]/g,'')];
      if(!cand || cand.length!==1) return;          // 등록이 없거나 이름이 둘 이상이면 손대지 않는다
      var reg=cand[0];
      if(reg===nm) return;
      var k=nm+'|'+reg;
      if(seen[k]) return;
      seen[k]=1;
      var m={ old:nm, neu:reg, vbiz:x.vbiz, rgn:x.rgn, bal:x.bal };
      m.kk=_fxNmKey(m); m.kept=_fxKeepHas(m.kk);     // r176
      if(m.kept && !withKept) return;
      out.push(m);
    });
    return out;
  }
'''

NM_KEEPFNS = r'''  // r176: 고치지 않고 그대로 두기 / 되살리기
  window.fxNmKeepIt = function(oldName, newName, vbiz){
    if(!_isAdmin()) return;
    _fxKeepAdd(_fxNmKey({old:oldName, neu:newName, vbiz:vbiz}));
    _fxRenderArBody();
  };
  window.fxNmUnkeep = function(oldName, newName, vbiz){
    if(!_isAdmin()) return;
    _fxKeepDel(_fxNmKey({old:oldName, neu:newName, vbiz:vbiz}));
    _fxRenderArBody();
  };
  window.fxNmUnkeepAll = function(){
    if(!_isAdmin()) return;
    _fxKeepDelPrefix('NM|');
    _fxRenderArBody();
  };
  window.fxNmToggle = function(){ _fxNmOpen=!_fxNmOpen; _fxRenderArBody(); };
'''

def apply_r176(s, path):
    # ── (0) 새 설정값 등록 (선언·저장·동기화·백업·복원·초기화) ──
    s = rep(s,
        "  let fxExcluded  = load('sched_fx_excluded') ?? [];  // 제외 거래처 [{biz,vendor,vbiz,reason}]",
        "  let fxExcluded  = load('sched_fx_excluded') ?? [];  // 제외 거래처 [{biz,vendor,vbiz,reason}]\n"
        "  // r176: 고치지 않고 '그대로 두기'로 판단한 후보들. 'NM|사업자번호|옛이름|새이름' / 'DUP|원장키A\\t원장키B'\n"
        "  let fxKeepAs    = load('sched_fx_keepas')   ?? [];",
        1, 'DECL')

    s = rep(s,
        "    save('sched_fx_excluded', fxExcluded);\n"
        "    localStorage.setItem('sched_local_ts', Date.now().toString());",
        "    save('sched_fx_excluded', fxExcluded);\n"
        "    save('sched_fx_keepas', fxKeepAs);   // r176\n"
        "    localStorage.setItem('sched_local_ts', Date.now().toString());",
        1, 'SAVE')

    s = rep(s,
        "        sched_fx_excluded: fxExcluded,\n"
        "        _updatedAt: ts,",
        "        sched_fx_excluded: fxExcluded,\n"
        "        sched_fx_keepas: fxKeepAs,\n"
        "        _updatedAt: ts,",
        1, 'FBPUT')

    #  test 빌드에는 '정식→테스트 복사'(r134)에도 같은 목록이 하나 더 있다.
    s = rep(s,
        "'sched_fx_adjusts','sched_fx_terms','sched_fx_excluded']",
        "'sched_fx_adjusts','sched_fx_terms','sched_fx_excluded','sched_fx_keepas']",
        3 if 'testpage' in path else 2, 'KEYS')
    if 'testpage' in path:
        #  복사 시 기본값 — keepas 는 배열이다
        s = rep(s,
            "(k==='sched_fx_adjusts'||k==='sched_fx_excluded') ? [] : {}",
            "(k==='sched_fx_adjusts'||k==='sched_fx_excluded'||k==='sched_fx_keepas') ? [] : {}",
            1, 'STGDEFAULT')

    s = rep(s,
        "    fxExcluded       = load('sched_fx_excluded') ?? [];\n"
        "    _fxCacheBump++;",
        "    fxExcluded       = load('sched_fx_excluded') ?? [];\n"
        "    fxKeepAs         = load('sched_fx_keepas')   ?? [];   // r176\n"
        "    _fxCacheBump++;",
        1, 'FBLOAD')

    s = rep(s,
        "      sched_fx_terms: fxTerms, sched_fx_excluded: fxExcluded\n"
        "    };",
        "      sched_fx_terms: fxTerms, sched_fx_excluded: fxExcluded, sched_fx_keepas: fxKeepAs\n"
        "    };",
        1, 'BACKUP')

    s = rep(s,
        "          fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[];",
        "          fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxKeepAs=[];   // r176",
        1, 'RESET')

    # ── (1) 공통 도우미 ──
    s = rep(s,
        "  function _fxDupPanelHtml(){",
        KEEP_HELPERS + "  function _fxDupPanelHtml(){",
        1, 'HELPERS')

    # ── (2) 중복 거래처 후보: 그대로 두기 ──
    s = rep(s,
        "  function _fxDupPanelHtml(){\n"
        "    var dups=_fxDupCandidates(_fxRegion);\n"
        "    if(!dups.length) return '';",
        "  // r176: 후보 한 쌍의 '그대로 두기' 키 — 두 원장키를 정렬해 담으므로 A/B 순서가 바뀌어도 같은 키다.\n"
        "  function _fxDupKey(p){ return 'DUP|'+[String(p[0].key), String(p[1].key)].sort().join('\\t'); }\n"
        "  //  withKept=true 면 그대로 두기 한 쌍까지 모두 돌려준다.\n"
        "  function _fxDupActive(region, withKept){\n"
        "    return _fxDupCandidates(region).filter(function(p){\n"
        "      return withKept ? true : !_fxKeepHas(_fxDupKey(p));\n"
        "    });\n"
        "  }\n"
        "  window.fxDupKeepIt = function(kA, kB){\n"
        "    if(!_isAdmin()) return;\n"
        "    _fxKeepAdd(_fxDupKey([{key:kA},{key:kB}]));\n"
        "    _fxRenderArBody();\n"
        "  };\n"
        "  window.fxDupUnkeep = function(kA, kB){\n"
        "    if(!_isAdmin()) return;\n"
        "    _fxKeepDel(_fxDupKey([{key:kA},{key:kB}]));\n"
        "    _fxRenderArBody();\n"
        "  };\n"
        "  window.fxDupUnkeepAll = function(){\n"
        "    if(!_isAdmin()) return;\n"
        "    _fxKeepDelPrefix('DUP|');\n"
        "    _fxRenderArBody();\n"
        "  };\n"
        "  function _fxDupPanelHtml(){\n"
        "    var all=_fxDupActive(_fxRegion, true);\n"
        "    var dups=all.filter(function(p){ return !_fxKeepHas(_fxDupKey(p)); });\n"
        "    var kept=all.filter(function(p){ return _fxKeepHas(_fxDupKey(p)); });\n"
        "    if(!all.length) return '';",
        1, 'DUPFNS')

    # 병합 버튼 옆에 [그대로 두기]
    s = rep(s,
        "        +   '<button type=\"button\" class=\"btn\" onclick=\"fxMergeDup(\\''+b.rgn+'\\',\\''+b.key.replace(/'/g,\"\\\\'\")+'\\',\\''+a.key.replace(/'/g,\"\\\\'\")+'\\')\" style=\"font-size:11px;padding:2px 8px;border:1px solid #1B3A6B;color:#14305c;background:#fff\">B로 병합 ▶</button>'\n"
        "        + '</td></tr>';",
        "        +   '<button type=\"button\" class=\"btn\" onclick=\"fxMergeDup(\\''+b.rgn+'\\',\\''+b.key.replace(/'/g,\"\\\\'\")+'\\',\\''+a.key.replace(/'/g,\"\\\\'\")+'\\')\" style=\"font-size:11px;padding:2px 8px;border:1px solid #1B3A6B;color:#14305c;background:#fff;margin-right:4px\">B로 병합 ▶</button>'\n"
        "        +   _fxKeepBtn('fxDupKeepIt(\\''+a.key.replace(/'/g,\"\\\\'\")+'\\',\\''+b.key.replace(/'/g,\"\\\\'\")+'\\')')   // r176\n"
        "        + '</td></tr>';",
        1, 'DUPROW')

    # 표가 비어도(전부 그대로 두기) 꼬리말은 보여야 한다
    s = rep(s,
        "      + '<div style=\"max-height:300px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\">'\n"
        "      + '<thead><tr><th style=\"'+TH+';text-align:left\">거래처 A</th><th style=\"'+TH+'\"></th><th style=\"'+TH+';text-align:left\">거래처 B</th><th style=\"'+TH+'\">병합</th></tr></thead>'\n"
        "      + '<tbody>'+rows+'</tbody></table></div></div>';\n"
        "  }",
        "      + (dups.length\n"
        "          ? ('<div style=\"max-height:300px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\">'\n"
        "             + '<thead><tr><th style=\"'+TH+';text-align:left\">거래처 A</th><th style=\"'+TH+'\"></th><th style=\"'+TH+';text-align:left\">거래처 B</th><th style=\"'+TH+'\">병합 / 넘어가기</th></tr></thead>'\n"
        "             + '<tbody>'+rows+'</tbody></table></div>')\n"
        "          : '<div style=\"padding:10px 14px;font-size:12px;color:#8a94a6\">확인이 필요한 후보가 없습니다.</div>')\n"
        "      + _fxKeptFootHtml(keptRows, 'fxDupUnkeepAll')   // r176\n"
        "      + '</div>';\n"
        "  }",
        1, 'DUPFOOT')

    # 꼬리말에 쓸 그대로 둔 쌍 목록
    s = rep(s,
        "    return '<div style=\"background:#fff;border:1px solid #d6deea;margin-bottom:12px\">'\n"
        "      + '<div style=\"padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#14305c\">중복 거래처 후보 '",
        "    var keptRows=kept.map(function(p){\n"
        "      var a=p[0], b=p[1];\n"
        "      return '<div style=\"display:flex;align-items:center;gap:8px;padding:3px 0;flex-wrap:wrap\">'\n"
        "        + '<span style=\"color:#6b7280\">'+esc(a.name)+' <span style=\"color:#b6bec9\">↔</span> '+esc(b.name)+'</span>'\n"
        "        + '<span style=\"flex:1\"></span>'\n"
        "        + _fxUnkeepBtn('fxDupUnkeep(\\''+a.key.replace(/'/g,\"\\\\'\")+'\\',\\''+b.key.replace(/'/g,\"\\\\'\")+'\\')')\n"
        "        + '</div>';\n"
        "    });\n"
        "    return '<div style=\"background:#fff;border:1px solid #d6deea;margin-bottom:12px\">'\n"
        "      + '<div style=\"padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#14305c\">중복 거래처 후보 '",
        1, 'DUPKEPTROWS')

    # ── (3) 업체명 불일치: 그대로 두기 ──
    old_nm = s[s.index("  var _fxNmOpen=false;\n  function _fxNameMismatch(region){"):s.index("  window.fxNmToggle = function(){ _fxNmOpen=!_fxNmOpen; _fxRenderArBody(); };")+len("  window.fxNmToggle = function(){ _fxNmOpen=!_fxNmOpen; _fxRenderArBody(); };\n")]
    s = rep(s, old_nm, NM_NEW + NM_KEEPFNS, 1, 'NMFN')

    # 전체 맞추기 / 패널은 '그대로 두기' 하지 않은 것만 대상
    s = rep(s,
        "  function _fxNmPanelHtml(){\n"
        "    var list=_fxNameMismatch(_fxRegion);\n"
        "    if(!list.length) return '';",
        "  function _fxNmPanelHtml(){\n"
        "    var all=_fxNameMismatch(_fxRegion, true);\n"
        "    var list=all.filter(function(m){ return !m.kept; });\n"
        "    var kept=all.filter(function(m){ return m.kept; });\n"
        "    if(!all.length) return '';",
        1, 'NMPANELHEAD')

    s = rep(s,
        "        +   '<button type=\"button\" class=\"btn\" onclick=\"fxNmFix(\\''+ro+'\\',\\''+rn+'\\')\" style=\"font-size:11px;padding:2px 10px;border:1px solid #1B3A6B;color:#14305c;background:#fff\">맞추기</button>'\n"
        "        + '</td></tr>';",
        "        +   '<button type=\"button\" class=\"btn\" onclick=\"fxNmFix(\\''+ro+'\\',\\''+rn+'\\')\" style=\"font-size:11px;padding:2px 10px;border:1px solid #1B3A6B;color:#14305c;background:#fff;margin-right:4px\">맞추기</button>'\n"
        "        +   _fxKeepBtn('fxNmKeepIt(\\''+ro+'\\',\\''+rn+'\\',\\''+m.vbiz+'\\')')   // r176\n"
        "        + '</td></tr>';",
        1, 'NMROW')

    s = rep(s,
        "      + '<div style=\"padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#b45309;display:flex;align-items:center;gap:8px;flex-wrap:wrap\">업체명 불일치 '+list.length+'곳'",
        "      + '<div style=\"padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:'+(list.length?'#b45309':'#6b7280')+';display:flex;align-items:center;gap:8px;flex-wrap:wrap\">업체명 불일치 '+list.length+'곳'",
        1, 'NMHEADCOLOR')

    # 전체 맞추기 버튼은 대상이 있을 때만
    s = rep(s,
        "      +   '<button type=\"button\" class=\"btn\" onclick=\"fxNmFixAll()\" style=\"font-size:11px;padding:2px 10px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B;font-weight:400\">전체 맞추기</button>'\n"
        "      + '</div>'\n"
        "      + '<div style=\"max-height:300px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\">'\n"
        "      + '<thead><tr><th style=\"'+TH+';text-align:left\">매입매출에 찍힌 이름</th><th style=\"'+TH+'\"></th><th style=\"'+TH+';text-align:left\">업체 목록 이름</th><th style=\"'+TH+'\">적용</th></tr></thead>'\n"
        "      + '<tbody>'+rows+'</tbody></table></div></div>';\n"
        "  }",
        "      +   (list.length ? '<button type=\"button\" class=\"btn\" onclick=\"fxNmFixAll()\" style=\"font-size:11px;padding:2px 10px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B;font-weight:400\">전체 맞추기</button>' : '')\n"
        "      + '</div>'\n"
        "      + (list.length\n"
        "          ? ('<div style=\"max-height:300px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\">'\n"
        "             + '<thead><tr><th style=\"'+TH+';text-align:left\">매입매출에 찍힌 이름</th><th style=\"'+TH+'\"></th><th style=\"'+TH+';text-align:left\">업체 목록 이름</th><th style=\"'+TH+'\">적용 / 넘어가기</th></tr></thead>'\n"
        "             + '<tbody>'+rows+'</tbody></table></div>')\n"
        "          : '<div style=\"padding:10px 14px;font-size:12px;color:#8a94a6\">확인이 필요한 후보가 없습니다.</div>')\n"
        "      + _fxKeptFootHtml(keptRows, 'fxNmUnkeepAll')   // r176\n"
        "      + '</div>';\n"
        "  }",
        1, 'NMFOOT')

    s = rep(s,
        "    return '<div style=\"background:#fff;border:1px solid #d6deea;margin-bottom:12px\">'\n"
        "      + '<div style=\"padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:'+(list.length?'#b45309':'#6b7280')+';",
        "    var keptRows=kept.map(function(m){\n"
        "      var ro=String(m.old).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,\"\\\\'\");\n"
        "      var rn=String(m.neu).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,\"\\\\'\");\n"
        "      return '<div style=\"display:flex;align-items:center;gap:8px;padding:3px 0;flex-wrap:wrap\">'\n"
        "        + '<span style=\"color:#6b7280\">'+esc(m.old)+' <span style=\"color:#b6bec9\">→</span> '+esc(m.neu)+'</span>'\n"
        "        + '<span style=\"flex:1\"></span>'\n"
        "        + _fxUnkeepBtn('fxNmUnkeep(\\''+ro+'\\',\\''+rn+'\\',\\''+m.vbiz+'\\')')\n"
        "        + '</div>';\n"
        "    });\n"
        "    return '<div style=\"background:#fff;border:1px solid #d6deea;margin-bottom:12px\">'\n"
        "      + '<div style=\"padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:'+(list.length?'#b45309':'#6b7280')+';",
        1, 'NMKEPTROWS')

    # ── (4) 칩: 활성 후보 기준으로 세되, 전부 그대로 두었어도 칩은 남긴다(패널을 열 통로) ──
    s = rep(s,
        "        var nDup=_fxDupCandidates(_fxRegion).length;\n"
        "        if(nDup) h+='<span onclick=\"fxDupToggle()\" style=\"cursor:pointer\" title=\"이름이 사실상 같은 거래처가 원장에 따로 잡혀 있을 수 있습니다. 클릭하면 후보 목록이 열립니다\">'+_fxChip('중복 거래처 후보', nDup+'쌍'+(_fxDupOpen?' ▲':' ▼'), false)+'</span>';\n"
        "        // r175: 업체 목록과 이름이 어긋난 거래처\n"
        "        var nNm=_fxNameMismatch(_fxRegion).length;\n"
        "        if(nNm) h+='<span onclick=\"fxNmToggle()\" style=\"cursor:pointer\" title=\"사업자번호는 같은데 계산서·입금에 찍힌 이름이 업체 목록과 다릅니다. 클릭하면 목록이 열립니다\">'+_fxChip('업체명 불일치', nNm+'곳'+(_fxNmOpen?' ▲':' ▼'), false)+'</span>';",
        "        // r176: '그대로 두기'한 것은 건수에서 빼되, 칩 자체는 남긴다 — 안 그러면 되돌릴 통로가 사라진다.\n"
        "        var dupAll=_fxDupActive(_fxRegion, true), nDup=dupAll.filter(function(p){ return !_fxKeepHas(_fxDupKey(p)); }).length;\n"
        "        if(dupAll.length) h+='<span onclick=\"fxDupToggle()\" style=\"cursor:pointer\" title=\"이름이 사실상 같은 거래처가 원장에 따로 잡혀 있을 수 있습니다. 클릭하면 후보 목록이 열립니다\">'\n"
        "          +_fxChip(nDup?'중복 거래처 후보':'중복 거래처 (그대로 둠)', (nDup||(dupAll.length-nDup))+'쌍'+(_fxDupOpen?' ▲':' ▼'), false)+'</span>';\n"
        "        // r175: 업체 목록과 이름이 어긋난 거래처\n"
        "        var nmAll=_fxNameMismatch(_fxRegion, true), nNm=nmAll.filter(function(m){ return !m.kept; }).length;\n"
        "        if(nmAll.length) h+='<span onclick=\"fxNmToggle()\" style=\"cursor:pointer\" title=\"사업자번호는 같은데 계산서·입금에 찍힌 이름이 업체 목록과 다릅니다. 클릭하면 목록이 열립니다\">'\n"
        "          +_fxChip(nNm?'업체명 불일치':'업체명 (그대로 둠)', (nNm||(nmAll.length-nNm))+'곳'+(_fxNmOpen?' ▲':' ▼'), false)+'</span>';",
        1, 'CHIPS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r176(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r175 2026-09-03 -->') == 1
            s = s.replace('<!-- test build r175 2026-09-03 -->', '<!-- test build r176 2026-09-04 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
