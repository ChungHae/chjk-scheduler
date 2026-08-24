# -*- coding: utf-8 -*-
# r141: [교차 입금 — 다른 사업장 거래처로 배정(사업장 이동)]
#  사례: 화성 거래처의 수금이 서울 계좌로 입금됨.
#  - r139의 "타사업장 계산서 거래처" 경고를 클릭 가능하게: 클릭 → 확인창 →
#    입금의 사업장을 그 거래처의 사업장으로 이동 후 배정 (업체 미등록이면 등록까지)
#  - 원래 계좌 사업장은 obiz 로 보존, 원장·엑셀 적요에 "○○ 계좌" 표기
#  - 입금 id 불변 → 같은 은행 파일 재업로드 시 중복 방지 그대로 유효

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R141 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r141(s, path):
    # (1) 힌트에 사업자번호 포함
    s = rep(s, "      if(!seenB[e.vendor]){ seenB[e.vendor]=1; hints.push({type:'other', inv:e.vendor, other:other}); }",
            "      if(!seenB[e.vendor]){ seenB[e.vendor]=1; hints.push({type:'other', inv:e.vendor, vbiz:e.vbiz||'', other:other}); }", 1, 'HINTV')

    # (2) 경고 행 → 클릭 가능 (사업장 이동 배정)
    s = rep(s, r"""        } else if(h.type==='other'){
          html += '<div style="padding:8px 12px;border-top:1px solid #f0d9b8;font-size:11.5px;color:#b45309;background:#fff8ef">'
            + '⚠️ "'+esc(h.inv)+'" 은(는) <b>'+h.other+'</b> 계산서 거래처입니다 — 이 입금은 '+esc(e.biz)+' 소속이라 여기 안 뜹니다. 은행 파일의 사업장 선택을 확인하세요.</div>';
        }""",
            r"""        } else if(h.type==='other'){
          var rn2=String(h.inv).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
          var rb2=String(h.vbiz||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");
          html += '<div onclick="fxPickCrossVend('+i+',\''+rn2+'\',\''+rb2+'\',\''+h.other+'\')" style="padding:8px 12px;border-top:1px solid #f0d9b8;font-size:11.5px;color:#b45309;background:#fff8ef;cursor:pointer" onmouseover="this.style.background=\'#fdefdb\'" onmouseout="this.style.background=\'#fff8ef\'">'
            + '⚠️ "'+esc(h.inv)+'" 은(는) <b>'+h.other+'</b> 계산서 거래처입니다 (이 입금은 '+esc(e.biz)+' 계좌).<br>'
            + '<b>클릭하면 이 입금을 '+h.other+' 소속으로 바꿔 배정합니다</b> — 계좌 선택이 잘못된 거라면 배정하지 말고 은행 파일을 사업장을 바꿔 다시 올리세요.</div>';
        }""", 1, 'HINTUI')

    # (3) 사업장 이동 배정 핸들러
    s = rep(s, "  window.fxUnDdRender = function(i){",
            r"""  window.fxPickCrossVend = function(i, name, vbiz, other){
    if(_isViewer()){ showInfoModal('매입매출','조회 전용 계정은 지정할 수 없습니다.'); return; }
    var d=_fxUnList[i]; if(!d) return;
    fxUnDdHide();
    showConfirmModal('사업장 이동 배정',
      d.date+' · '+_fxFmt(d.amount)+'원 · 입금자 "'+(d.payer||'')+'"\n\n'
      + d.biz+' 계좌로 들어온 입금이지만 '+other+' 거래처 "'+name+'" 의 수금입니다.\n'
      + '이 입금의 사업장을 '+other+'(으)로 바꿔 배정할까요?\n'
      + '(원장·엑셀에는 "'+d.biz+' 계좌" 표기가 남습니다)',
      function(){
        d.obiz=d.biz;
        d.biz=other;
        fxPickNewVend(i, name, vbiz);
      }, other+'(으)로 배정', '#b45309');
  };
  window.fxUnDdRender = function(i){""", 1, 'HANDLER')

    # (4) 원장·엑셀 적요에 원계좌 표기
    s = rep(s, "    L.deps.forEach(function(e){ rows.push({date:e.date, type:(e.kind==='note'?'어음':'입금'), desc:(e.bank||'')+(e.bank?' · ':'')+(e.payer||''), chg:-e.amount, did:e.id}); });",
            "    L.deps.forEach(function(e){ rows.push({date:e.date, type:(e.kind==='note'?'어음':'입금'), desc:(e.bank||'')+(e.bank?' · ':'')+(e.payer||'')+((e.obiz&&e.obiz!==e.biz)?' · '+e.obiz+' 계좌':''), chg:-e.amount, did:e.id}); });", 1, 'DESC')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r141(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r140 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r140 2026-08-24 -->', '<!-- test build r141 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
