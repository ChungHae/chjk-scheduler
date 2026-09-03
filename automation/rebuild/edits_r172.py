# -*- coding: utf-8 -*-
# r172: (A) 은행 업로드 결과에 '건너뛴 행·읽은 시트' 안내  (B) 조정 날짜를 연/월/일 세 칸으로
#
#  (A) 사용자 질문: "은행 내역을 올리면 전체가 다 들어오는 거지?"
#      실측으로 확인한 파싱은 정상이었지만, 조용히 넘어가는 경로가 셋 있어 확인할 방법이 없었다:
#        ① 거래일시를 못 읽는 행 → 그냥 continue. 건수도 안 세고 아무 표시도 없음.
#           (_fxD 는 엑셀 날짜값과 YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD 만 인식.
#            '20220314' 같은 구분자 없는 8자리, 두 자리 연도는 못 읽는다)
#        ② 엑셀의 첫 시트만 읽는다(wb.SheetNames[0]) → 연도별로 시트가 나뉜 파일은 나머지가 통째로 무시.
#        ③ 중복키(사업장|은행|거래일시|금액|입금자)로 합쳐진 행은 '중복 N건' 으로만 나와 내용을 알 수 없음.
#      수정: 파일마다 ①의 건수와 엑셀 행번호(앞 5개), ②의 시트 개수/읽은 시트명, ③의 행번호를
#        업로드 결과에 표시한다. 파싱 규칙 자체는 건드리지 않는다(판정 결과 불변).
#        ※ 완전히 빈 줄(날짜·금액·입금자 모두 빈칸)은 파일 끝의 여백이므로 세지 않는다.
#
#  (B) 사용자 요청: 조정 추가의 날짜 칸에서 좌우 화살표·Tab 으로 연/월/일 이동이 되게.
#      input[type=date] 는 칸 이동 방식이 브라우저마다 다르고(실측: 화살표로 칸이 안 넘어가고
#      연도 칸에 숫자가 계속 쌓여 '260415-09-03' 같은 값이 됨), Tab 은 아예 칸 밖으로 나간다.
#      수정: 연(4)/월(2)/일(2) 세 칸으로 직접 만든다.
#        · Tab / Shift+Tab — 칸 사이 이동(브라우저 기본 동작)
#        · ←  칸 맨 앞에서 이전 칸,  → 칸 맨 뒤에서 다음 칸
#        · 숫자를 다 채우면 자동으로 다음 칸,  빈 칸에서 Backspace 면 이전 칸
#        · ↑↓ 값 증감(월 1~12, 일 1~31 순환),  Enter 저장
#        · 저장할 때 실제 달력으로 검증(2월 30일 같은 값 차단)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R172 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r172(s, path):
    # ─────────── (A) 업로드 결과 안내 ───────────
    # 파일별 집계 변수
    s = rep(s,
        "      var nDep=0, nNote=0, nDup=0, nAuto=0, nUn=0, nAx=0, errs=[], lines=[];",
        "      var nDep=0, nNote=0, nDup=0, nAuto=0, nUn=0, nAx=0, errs=[], lines=[];\n"
        "      var nSkipD=0, warns=[];   // r172: 조용히 넘어가던 행을 눈에 보이게",
        1, 'UPVARS')

    # 시트 정보 기록
    s = rep(s,
        "          var rows=XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {header:1, raw:true, defval:null});\n"
        "          // 1) 어음 형식 판별",
        "          var rows=XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {header:1, raw:true, defval:null});\n"
        "          // r172: 첫 시트만 읽는다 — 시트가 여러 개면 나머지는 무시되므로 반드시 알린다\n"
        "          if(wb.SheetNames.length > 1){\n"
        "            warns.push(esc(f.name)+': 시트가 '+wb.SheetNames.length+'개인데 첫 시트(\"'+esc(String(wb.SheetNames[0]))+'\")만 읽었습니다. '\n"
        "              + '나머지 시트('+esc(wb.SheetNames.slice(1).join(', '))+')는 반영되지 않았습니다 — 시트별로 따로 올려주세요.');\n"
        "          }\n"
        "          // 1) 어음 형식 판별",
        1, 'UPSHEET')

    # 은행 행 루프: 날짜 못 읽는 행·중복 행의 엑셀 행번호를 모은다
    s = rep(s,
        "          var fN3=0, fU3=0, fD3=0;\n"
        "          for(var r6=hIdx+1;r6<rows.length;r6++){\n"
        "            var row6=rows[r6]||[];\n"
        "            var rawDt=_fxCell(row6[iDate]);\n"
        "            var d6=_fxD(row6[iDate]), amt6=_fxN(row6[iIn]), payer=_fxCell(row6[iPay]);\n"
        "            if(!d6 || !amt6 || amt6<=0) continue;\n"
        "            var id6='B|'+biz+'|'+bank+'|'+(rawDt||d6)+'|'+amt6+'|'+payer;\n"
        "            if(seen[id6]){ nDup++; fD3++; continue; }",
        "          var fN3=0, fU3=0, fD3=0, fSkipD=0, skipRows=[], dupRows=[];\n"
        "          for(var r6=hIdx+1;r6<rows.length;r6++){\n"
        "            var row6=rows[r6]||[];\n"
        "            var rawDt=_fxCell(row6[iDate]);\n"
        "            var d6=_fxD(row6[iDate]), amt6=_fxN(row6[iIn]), payer=_fxCell(row6[iPay]);\n"
        "            // r172: 날짜를 못 읽어 버려지는 행을 센다. 단 완전히 빈 줄(파일 끝 여백)은 제외.\n"
        "            if(!d6){\n"
        "              if(rawDt || payer || _fxCell(row6[iIn])){ fSkipD++; if(skipRows.length<5) skipRows.push(r6+1); }\n"
        "              continue;\n"
        "            }\n"
        "            if(!amt6 || amt6<=0) continue;   // 출금행 등 — 정상적으로 건너뜀\n"
        "            var id6='B|'+biz+'|'+bank+'|'+(rawDt||d6)+'|'+amt6+'|'+payer;\n"
        "            if(seen[id6]){ nDup++; fD3++; if(dupRows.length<5) dupRows.push((r6+1)+'행 '+(payer||'')); continue; }",
        1, 'UPLOOP')

    # 파일별 결과 줄
    s = rep(s,
        "          lines.push(esc(f.name)+' → '+bank+' · 입금 '+fN3+'건'+(fU3?(' · 미배정 '+fU3):'')+(fD3?(' · 중복 '+fD3):''));",
        "          // r172: 몇 행이 왜 빠졌는지 숫자로 남긴다\n"
        "          nSkipD += fSkipD;\n"
        "          lines.push(esc(f.name)+' → '+bank+' · 입금 '+fN3+'건'+(fU3?(' · 미배정 '+fU3):'')+(fD3?(' · 중복 '+fD3):'')\n"
        "            + ' <span style=\"color:#9ca3af\">(읽은 시트: '+esc(String(wb.SheetNames[0]))+(wb.SheetNames.length>1?(' / 전체 '+wb.SheetNames.length+'개'):'')+')</span>');\n"
        "          if(fSkipD){\n"
        "            warns.push(esc(f.name)+': 거래일시를 읽지 못해 <b>'+fSkipD+'행</b>을 건너뛰었습니다'\n"
        "              + ' (엑셀 '+skipRows.join(', ')+(fSkipD>skipRows.length?' 외':'')+'행).'\n"
        "              + ' 날짜는 2026-08-31 / 2026.08.31 / 2026/08/31 형식만 읽습니다.');\n"
        "          }\n"
        "          if(fD3){\n"
        "            warns.push(esc(f.name)+': 같은 은행·같은 거래일시·같은 금액·같은 입금자라서 <b>'+fD3+'행</b>을 중복으로 제외했습니다'\n"
        "              + ' (엑셀 '+esc(dupRows.join(' / '))+(fD3>dupRows.length?' 외':'')+').'\n"
        "              + ' 실제로 다른 거래라면 은행에서 거래시각까지 나오는 형식으로 다시 받아 올려주세요.');\n"
        "          }",
        1, 'UPLINE')

    # 결과 안내에 경고 묶음 추가
    s = rep(s,
        "      if(lines.length) html+='<br><span style=\"color:#6b7280\">'+lines.join('<br>')+'</span>';\n"
        "      if(errs.length) html+='<br><span style=\"color:#dc2626\">오류 '+errs.length+'건: '+esc(errs.slice(0,5).join(' / '))+'</span>';\n"
        "      _fxUpLog(html);\n"
        "      _fxRenderUnasg();",
        "      if(nSkipD) html+='<br><b style=\"color:#dc2626\">건너뛴 행 '+nSkipD+'행</b> — 아래 내용을 확인해 주세요.';\n"
        "      if(lines.length) html+='<br><span style=\"color:#6b7280\">'+lines.join('<br>')+'</span>';\n"
        "      // r172: 조용히 넘어가던 것들을 여기 모아 보여준다\n"
        "      if(warns.length) html+='<div style=\"margin-top:8px;padding:8px 12px;background:#fff8ef;border:1px solid #f0d9b8;color:#b45309;line-height:1.7\">'\n"
        "        + '&#9888;&#65039; ' + warns.join('<br>&#9888;&#65039; ') + '</div>';\n"
        "      if(errs.length) html+='<br><span style=\"color:#dc2626\">오류 '+errs.length+'건: '+esc(errs.slice(0,5).join(' / '))+'</span>';\n"
        "      _fxUpLog(html);\n"
        "      _fxRenderUnasg();",
        1, 'UPMSG')

    # ─────────── (B) 조정 날짜 연/월/일 세 칸 ───────────
    s = rep(s,
        "  window.fxDepUnassign = function(id){",
        "  // ── r172: 조정 날짜 입력 (연/월/일 세 칸) ──\n"
        "  //  input[type=date] 는 브라우저마다 칸 이동이 달라 좌우 화살표·Tab 이 먹지 않는다(사용자 보고).\n"
        "  //  세 칸으로 나누면 Tab 은 기본 동작으로, 화살표는 아래 규칙으로 자연스럽게 이동한다.\n"
        "  function _fxAdjDateHtml(dt, DI){\n"
        "    var p2=function(n){ return (n<10?'0':'')+n; };\n"
        "    var S=DI+';text-align:center;padding:0 3px';\n"
        "    return '<span id=\"fxAdjDate\" style=\"display:inline-flex;align-items:center;gap:3px\">'\n"
        "      + '<input type=\"text\" class=\"fxdt\" data-p=\"y\" maxlength=\"4\" inputmode=\"numeric\" autocomplete=\"off\" value=\"'+dt.getFullYear()+'\" title=\"연\" style=\"'+S+';width:50px\">'\n"
        "      + '<span style=\"color:#c8d2de\">-</span>'\n"
        "      + '<input type=\"text\" class=\"fxdt\" data-p=\"m\" maxlength=\"2\" inputmode=\"numeric\" autocomplete=\"off\" value=\"'+p2(dt.getMonth()+1)+'\" title=\"월\" style=\"'+S+';width:32px\">'\n"
        "      + '<span style=\"color:#c8d2de\">-</span>'\n"
        "      + '<input type=\"text\" class=\"fxdt\" data-p=\"d\" maxlength=\"2\" inputmode=\"numeric\" autocomplete=\"off\" value=\"'+p2(dt.getDate())+'\" title=\"일\" style=\"'+S+';width:32px\">'\n"
        "      + '</span>';\n"
        "  }\n"
        "  function _fxAdjDateBind(){\n"
        "    var box=document.getElementById('fxAdjDate'); if(!box || box.__dtb) return; box.__dtb=1;\n"
        "    var els=[].slice.call(box.querySelectorAll('.fxdt'));\n"
        "    els.forEach(function(el, idx){\n"
        "      // 칸에 들어오면 전체 선택 — 그래야 클릭 후 바로 숫자를 치면 갈아끼워진다.\n"
        "      //  마우스로 누를 때는 기본 동작(캐럿 놓기 + mouseup 해제)이 선택을 풀어버리므로\n"
        "      //  mousedown 을 막고 직접 focus 를 준다(그래야 select 가 유지된다).\n"
        "      el.addEventListener('mousedown', function(ev){ if(document.activeElement!==this){ ev.preventDefault(); this.focus(); } });\n"
        "      el.addEventListener('focus', function(){ try{ this.select(); }catch(_e){} });\n"
        "      el.addEventListener('input', function(){\n"
        "        var mx=parseInt(this.getAttribute('maxlength'),10)||2;\n"
        "        this.value=this.value.replace(/\\D/g,'').slice(0,mx);\n"
        "        if(this.value.length>=mx && idx<els.length-1) els[idx+1].focus();   // 다 채우면 다음 칸\n"
        "      });\n"
        "      el.addEventListener('keydown', function(ev){\n"
        "        var k=ev.key;\n"
        "        // ←/→ 는 늘 칸 사이를 옮긴다(달력 입력칸과 같은 느낌). 칸 안은 어차피 숫자뿐이라\n"
        "        //  글자 단위 이동은 쓸 일이 없고, 칸에 들어가면 전체 선택이라 바로 고쳐 쓰면 된다.\n"
        "        if(k==='ArrowLeft'){ if(idx>0){ ev.preventDefault(); els[idx-1].focus(); } return; }\n"
        "        if(k==='ArrowRight'){ if(idx<els.length-1){ ev.preventDefault(); els[idx+1].focus(); } return; }\n"
        "        if(k==='Backspace' && !this.value && idx>0){ ev.preventDefault(); els[idx-1].focus(); return; }\n"
        "        if(k==='ArrowUp' || k==='ArrowDown'){\n"
        "          ev.preventDefault();\n"
        "          var p=this.dataset.p, n=parseInt(this.value||'0',10)||0;\n"
        "          n += (k==='ArrowUp'?1:-1);\n"
        "          if(p==='m'){ if(n<1) n=12; if(n>12) n=1; this.value=(n<10?'0':'')+n; }\n"
        "          else if(p==='d'){ if(n<1) n=31; if(n>31) n=1; this.value=(n<10?'0':'')+n; }\n"
        "          else { if(n<1900) n=1900; if(n>2999) n=2999; this.value=String(n); }\n"
        "          try{ this.select(); }catch(_e){}\n"
        "          return;\n"
        "        }\n"
        "        if(k==='Enter'){ ev.preventDefault(); fxAdjSave(); }\n"
        "      });\n"
        "      el.addEventListener('blur', function(){\n"
        "        var p=this.dataset.p, n=parseInt(this.value||'',10);\n"
        "        if(!n) return;\n"
        "        if(p==='m'){ n=Math.min(12,Math.max(1,n)); this.value=(n<10?'0':'')+n; }\n"
        "        else if(p==='d'){ n=Math.min(31,Math.max(1,n)); this.value=(n<10?'0':'')+n; }\n"
        "      });\n"
        "    });\n"
        "  }\n"
        "  //  세 칸을 합쳐 'YYYY-MM-DD' 로. 달력에 없는 날(2월 30일 등)이면 빈 값을 돌려준다.\n"
        "  function _fxAdjDateVal(){\n"
        "    var box=document.getElementById('fxAdjDate'); if(!box) return '';\n"
        "    var g=function(p){ var e=box.querySelector('.fxdt[data-p=\"'+p+'\"]'); return e?String(e.value||'').replace(/\\D/g,''):''; };\n"
        "    var y=g('y'), m=g('m'), d=g('d');\n"
        "    if(y.length!==4 || !m || !d) return '';\n"
        "    var yi=parseInt(y,10), mi=parseInt(m,10), di=parseInt(d,10);\n"
        "    if(!(mi>=1 && mi<=12)) return '';\n"
        "    var last=new Date(yi, mi, 0).getDate();\n"
        "    if(!(di>=1 && di<=last)) return '';\n"
        "    return y+'-'+(mi<10?'0':'')+mi+'-'+(di<10?'0':'')+di;\n"
        "  }\n"
        "  window.fxDepUnassign = function(id){",
        1, 'ADJDATE')

    # 폼 마크업 교체
    s = rep(s,
        "        + '<input type=\"date\" id=\"fxAdjDate\" value=\"'+dk(new Date())+'\" style=\"'+DI+'\">'",
        "        + _fxAdjDateHtml(new Date(), DI)",
        1, 'ADJFORM')

    # 저장 시 값 읽기 + 안내 문구
    s = rep(s,
        "    var d=(document.getElementById('fxAdjDate')||{}).value;",
        "    var d=_fxAdjDateVal();",
        1, 'ADJREAD')

    s = rep(s,
        "    if(!d || !amt){ showInfoModal('조정','일자와 금액을 입력하세요. (음수 = 미수 차감/상계, 양수 = 미수 증가)'); return; }",
        "    if(!d){ showInfoModal('조정','일자를 올바르게 입력하세요. (연 4자리 / 월 1~12 / 일은 그 달에 있는 날짜)'); return; }\n"
        "    if(!amt){ showInfoModal('조정','금액을 입력하세요. (음수 = 미수 차감/상계, 양수 = 미수 증가)'); return; }",
        1, 'ADJVALID')

    # 원장을 다시 그릴 때마다 날짜칸 이벤트를 붙인다
    s = rep(s,
        "      + '<tbody>'+rows+'</tbody></table>' + _fxArPagerHtml(_arTotal, _fxArPageSize, _fxArPage) + '</div>';\n"
        "  }",
        "      + '<tbody>'+rows+'</tbody></table>' + _fxArPagerHtml(_arTotal, _fxArPageSize, _fxArPage) + '</div>';\n"
        "    try{ _fxAdjDateBind(); }catch(_e){}   // r172: 조정 폼이 떠 있으면 날짜칸 키 이동을 붙인다\n"
        "  }",
        1, 'ADJBIND')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r172(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r171 2026-08-31 -->') == 1
            s = s.replace('<!-- test build r171 2026-08-31 -->', '<!-- test build r172 2026-08-31 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
