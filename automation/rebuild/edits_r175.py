# -*- coding: utf-8 -*-
# r175: 이미 어긋나 있는 거래처명을 업체 목록 기준으로 맞추는 도구
#
#  사용자 보고: r174 를 배포했는데도 미수현황에 여전히 '삼광엔지어링' 으로 나온다.
#  원인(논리적으로 명확): r174 는 "이름을 바꾸는 그 순간" 매입매출 자료도 같이 바꾼다.
#    그런데 이 업체는 r174 배포 '전에' 이미 바꿔 놓은 상태다. 즉 옛 이름(삼광엔지어링)은
#    업체 목록 어디에도 없고 매입매출 자료에만 남아 있다. 지금 와서 다시 이름을 바꿔도
#    (삼광엔지니어링 -> X -> 삼광엔지니어링) 옛 이름과는 무관한 변경이라 영영 안 따라온다.
#    => 이미 어긋난 것을 찾아서 맞춰 주는 별도 수단이 필요하다.
#
#  방식: 사업자번호를 기준으로 자동 감지한다.
#    미수 원장의 각 거래처(사업자번호로 묶인 줄)에 대해
#      · 그 사업자번호로 업체 목록에 등록된 이름을 찾고(_findClientByBiz)
#      · 원장에 찍힌 이름과 다르면 '어긋남' 후보
#      · 단 원장 이름 자체가 업체 목록에 있는 이름이면 제외한다(다른 업체일 수 있으므로)
#    미수현황 상단 칩에 "업체명 불일치 N곳" 이 뜨고, 누르면 옛 이름 → 새 이름 목록이 열린다.
#    행마다 [맞추기], 머리에 [전체 맞추기]. 실제 변경은 r174 의 _fxRenameVendor 를 그대로 쓴다
#    (사업자번호·금액·배정 상태는 불변, 저장 전 _fxEnsureData 보장).
#
#  이 도구는 앞으로도 쓸모가 있다: 다른 사람이 옛 버전에서 이름을 바꿨거나,
#  홈택스 상호가 바뀐 경우에도 같은 방식으로 잡힌다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R175 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r175(s, path):
    # (1) 감지 + 패널
    s = rep(s,
        "  window.fxMergeDup = function(rgn, keepKey, dropKey){",
        "  // ── r175: 업체 목록과 이름이 어긋난 거래처 찾기 ──\n"
        "  //  사업자번호는 같은데 원장에 찍힌 이름이 업체 목록의 이름과 다른 경우.\n"
        "  //  (옛 버전에서 이름을 바꿨거나, 홈택스 상호가 바뀐 경우 등)\n"
        "  var _fxNmOpen=false;\n"
        "  function _fxNameMismatch(region){\n"
        "    var out=[], seen={};\n"
        "    var cliNames={}, byBiz={};\n"
        "    try{\n"
        "      (allClients()||[]).forEach(function(c){\n"
        "        if(!c || !c[0]) return;\n"
        "        var nm=String(c[0]).trim(); if(!nm) return;\n"
        "        cliNames[nm]=1;\n"
        "        var bd=String(c[1]||'').replace(/[^0-9]/g,'');\n"
        "        if(bd.length!==10) return;\n"
        "        if(!byBiz[bd]) byBiz[bd]=[];\n"
        "        if(byBiz[bd].indexOf(nm)<0) byBiz[bd].push(nm);   // 같은 사업자번호에 이름이 여러 개면 확정 불가\n"
        "      });\n"
        "    }catch(_e){ return out; }\n"
        "    _fxLedgers(region).forEach(function(x){\n"
        "      var nm=String(x.name||'').trim();\n"
        "      if(!nm || !x.vbiz || !/\\d{3}-\\d{2}-\\d{5}/.test(x.vbiz)) return;\n"
        "      if(cliNames[nm]) return;                     // 원장 이름이 업체 목록에 있으면 그대로 둔다\n"
        "      var cand=byBiz[String(x.vbiz).replace(/[^0-9]/g,'')];\n"
        "      if(!cand || cand.length!==1) return;          // 등록이 없거나 이름이 둘 이상이면 손대지 않는다\n"
        "      var reg=cand[0];\n"
        "      if(reg===nm) return;\n"
        "      var k=nm+'|'+reg;\n"
        "      if(seen[k]) return;\n"
        "      seen[k]=1;\n"
        "      out.push({ old:nm, neu:reg, vbiz:x.vbiz, rgn:x.rgn, bal:x.bal });\n"
        "    });\n"
        "    return out;\n"
        "  }\n"
        "  window.fxNmToggle = function(){ _fxNmOpen=!_fxNmOpen; _fxRenderArBody(); };\n"
        "  window.fxNmFix = function(oldName, newName){\n"
        "    if(!_isAdmin()) return;\n"
        "    _fxRenameVendorAfter(oldName, newName);\n"
        "  };\n"
        "  window.fxNmFixAll = function(){\n"
        "    if(!_isAdmin()) return;\n"
        "    var list=_fxNameMismatch(_fxRegion);\n"
        "    if(!list.length) return;\n"
        "    showConfirmModal('업체명 맞추기',\n"
        "      list.length+'곳의 매입매출 거래처명을 업체 목록의 이름으로 바꿉니다.\\n\\n'\n"
        "      + list.slice(0,8).map(function(m){ return '· '+m.old+'  →  '+m.neu; }).join('\\n')\n"
        "      + (list.length>8?('\\n… 외 '+(list.length-8)+'곳'):'')\n"
        "      + '\\n\\n사업자번호로 묶는 방식은 그대로라 미수 잔액과 배정은 바뀌지 않습니다.',\n"
        "      function(){ _fxNmFixSeq(list.slice()); }, '맞추기', '#1B3A6B');\n"
        "  };\n"
        "  //  한 번에 여러 곳을 고칠 때는 하나씩 순서대로 — 동시에 저장하면 서로 덮어쓴다.\n"
        "  async function _fxNmFixSeq(list){\n"
        "    var done=0, fail=0;\n"
        "    for(var i=0;i<list.length;i++){\n"
        "      try{\n"
        "        var c=await _fxRenameVendor(list[i].old, list[i].neu);\n"
        "        if(c && !c.ambiguous) done++; else fail++;\n"
        "      }catch(_e){ fail++; }\n"
        "    }\n"
        "    _fxNmOpen=false;\n"
        "    try{ renderFxPage(); }catch(_e2){}\n"
        "    showInfoModal('업체명 맞추기',\n"
        "      done+'곳의 매입매출 거래처명을 업체 목록 이름으로 바꿨습니다.'\n"
        "      + (fail?('\\n'+fail+'곳은 바꾸지 않았습니다 — 같은 이름이 업체 목록에 아직 남아 있어 어느 쪽 자료인지 확정할 수 없는 경우입니다.'):'')\n"
        "      + '\\n\\n미수 잔액과 배정은 바뀌지 않았습니다.');\n"
        "  }\n"
        "  function _fxNmPanelHtml(){\n"
        "    var list=_fxNameMismatch(_fxRegion);\n"
        "    if(!list.length) return '';\n"
        "    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;white-space:nowrap';\n"
        "    var TD='padding:7px 10px;border-bottom:1px solid #eef2f7;font-size:12px;vertical-align:middle';\n"
        "    var rows=list.map(function(m){\n"
        "      var ro=String(m.old).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,\"\\\\'\");\n"
        "      var rn=String(m.neu).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,\"\\\\'\");\n"
        "      return '<tr>'\n"
        "        + '<td style=\"'+TD+'\">'+(_fxRegion==='all'?_fxBizBadge(m.rgn):'')+'<b>'+esc(m.old)+'</b>'\n"
        "        +   ' <span style=\"color:#9ca3af\">'+m.vbiz+' · 잔액 '+_fxFmt(m.bal)+'</span></td>'\n"
        "        + '<td style=\"'+TD+';text-align:center;color:#9ca3af\">→</td>'\n"
        "        + '<td style=\"'+TD+'\"><b style=\"color:#14305c\">'+esc(m.neu)+'</b> <span style=\"color:#9ca3af\">업체 목록</span></td>'\n"
        "        + '<td style=\"'+TD+';text-align:center\">'\n"
        "        +   '<button type=\"button\" class=\"btn\" onclick=\"fxNmFix(\\''+ro+'\\',\\''+rn+'\\')\" style=\"font-size:11px;padding:2px 10px;border:1px solid #1B3A6B;color:#14305c;background:#fff\">맞추기</button>'\n"
        "        + '</td></tr>';\n"
        "    }).join('');\n"
        "    return '<div style=\"background:#fff;border:1px solid #d6deea;margin-bottom:12px\">'\n"
        "      + '<div style=\"padding:9px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#b45309;display:flex;align-items:center;gap:8px;flex-wrap:wrap\">업체명 불일치 '+list.length+'곳'\n"
        "      +   '<span style=\"font-weight:400;color:#8a94a6\">— 사업자번호는 같은데 계산서·입금에 찍힌 이름이 업체 목록과 다릅니다. 맞추면 표시 이름만 바뀌고 잔액·배정은 그대로입니다.</span>'\n"
        "      +   '<span style=\"flex:1\"></span>'\n"
        "      +   '<button type=\"button\" class=\"btn\" onclick=\"fxNmFixAll()\" style=\"font-size:11px;padding:2px 10px;border:1px solid #1B3A6B;color:#fff;background:#1B3A6B;font-weight:400\">전체 맞추기</button>'\n"
        "      + '</div>'\n"
        "      + '<div style=\"max-height:300px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\">'\n"
        "      + '<thead><tr><th style=\"'+TH+';text-align:left\">매입매출에 찍힌 이름</th><th style=\"'+TH+'\"></th><th style=\"'+TH+';text-align:left\">업체 목록 이름</th><th style=\"'+TH+'\">적용</th></tr></thead>'\n"
        "      + '<tbody>'+rows+'</tbody></table></div></div>';\n"
        "  }\n"
        "  window.fxMergeDup = function(rgn, keepKey, dropKey){",
        1, 'NMPANEL')

    # (2) 상단 칩에 추가
    s = rep(s,
        "        var nDup=_fxDupCandidates(_fxRegion).length;\n"
        "        if(nDup) h+='<span onclick=\"fxDupToggle()\" style=\"cursor:pointer\" title=\"이름이 사실상 같은 거래처가 원장에 따로 잡혀 있을 수 있습니다. 클릭하면 후보 목록이 열립니다\">'+_fxChip('중복 거래처 후보', nDup+'쌍'+(_fxDupOpen?' ▲':' ▼'), false)+'</span>';",
        "        var nDup=_fxDupCandidates(_fxRegion).length;\n"
        "        if(nDup) h+='<span onclick=\"fxDupToggle()\" style=\"cursor:pointer\" title=\"이름이 사실상 같은 거래처가 원장에 따로 잡혀 있을 수 있습니다. 클릭하면 후보 목록이 열립니다\">'+_fxChip('중복 거래처 후보', nDup+'쌍'+(_fxDupOpen?' ▲':' ▼'), false)+'</span>';\n"
        "        // r175: 업체 목록과 이름이 어긋난 거래처\n"
        "        var nNm=_fxNameMismatch(_fxRegion).length;\n"
        "        if(nNm) h+='<span onclick=\"fxNmToggle()\" style=\"cursor:pointer\" title=\"사업자번호는 같은데 계산서·입금에 찍힌 이름이 업체 목록과 다릅니다. 클릭하면 목록이 열립니다\">'+_fxChip('업체명 불일치', nNm+'곳'+(_fxNmOpen?' ▲':' ▼'), false)+'</span>';",
        1, 'NMCHIP')

    # (3) 패널 렌더 연결
    s = rep(s,
        "    var noteHtml = (_fxNotesOpen ? _fxNotesPanelHtml() : '') + (_fxExclOpen ? _fxExclPanelHtml() : '') + (_isAdmin()&&_fxDupOpen ? _fxDupPanelHtml() : '');",
        "    var noteHtml = (_fxNotesOpen ? _fxNotesPanelHtml() : '') + (_fxExclOpen ? _fxExclPanelHtml() : '') + (_isAdmin()&&_fxDupOpen ? _fxDupPanelHtml() : '')\n"
        "      + (_isAdmin()&&_fxNmOpen ? _fxNmPanelHtml() : '');   // r175",
        1, 'NMRENDER')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r175(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r174 2026-09-03 -->') == 1
            s = s.replace('<!-- test build r174 2026-09-03 -->', '<!-- test build r175 2026-09-03 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
