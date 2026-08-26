# -*- coding: utf-8 -*-
# r167: 카드매출 수집 상태 배너 — "완료(초록)" 는 하루에 한 번만 잠깐, "실패(빨강)" 는 계속
#
#  사용자 요청: 문제가 생겼을 때의 빨간 박스는 계속 떠 있는 게 맞지만,
#  수집 완료 안내는 처음 한 번만 잠깐 보여주고 그 다음부터는 안 보이게.
#
#  설계:
#   - 초록 안내를 띄운 날짜를 localStorage(sched_cs_ok_banner_day)에 남긴다.
#     같은 날 다시 들어오면 아예 표시하지 않는다(브라우저별 기록 — 다른 PC에서는 그 PC에서 한 번).
#   - 처음 뜰 때는 6초 뒤 부드럽게 사라진다(사용자가 못 보고 지나치지 않게 잠깐은 보여줌).
#   - 빨강은 종전대로 항상, 사라지지 않는다. 그리고 빨강이 뜨면 "봤음" 기록을 지운다
#     → 나중에 수집이 정상화되면 완료 안내를 한 번 다시 보여주기 위함.
#   - 자동 숨김 타이머가 도는 중에 화면이 다시 그려져 빨강으로 바뀔 수 있으므로,
#     타이머는 data-csok 표식을 확인하고 초록일 때만 숨긴다(빨강을 지우지 않게).
#   - 저장 키는 앱의 save/load 를 쓰므로 TEST(stage)에서는 'stg:' 프리픽스가 자동으로 붙어
#     정식과 기록이 섞이지 않는다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R167 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r167(s, path):
    # (1) 상태 변수
    s = rep(s,
        "  let _csCache = null;\n  let _csMetaCache = null;",
        "  let _csCache = null;\n  let _csMetaCache = null;\n"
        "  // r167: 수집 '완료' 안내는 하루 한 번만 잠깐 보여준다(사용자 요청).\n"
        "  const _CS_OK_SEEN_KEY = 'sched_cs_ok_banner_day';   // 값 = 'YYYY-M-D'\n"
        "  let _csOkHideTimer = null;",
        1, 'CSVARS')

    # (2) 배너 표시 로직
    s = rep(s,
        """        stEl.style.display='';
        if(_bad.length){
          stEl.style.background='#fef2f2'; stEl.style.border='1.5px solid #fca5a5'; stEl.style.color='#b91c1c';
          stEl.innerHTML='&#9888;&#65039; 오늘 카드매출 자료가 아직 수집되지 않았습니다: <b>'+_bad.join(', ')+'</b> &mdash; GitHub Actions(카드매출 동기화) 실행 결과를 확인해주세요.';
        } else {
          stEl.style.background='#f0fdf4'; stEl.style.border='1.5px solid #86efac'; stEl.style.color='#15803d';
          stEl.innerHTML='&#10004; 오늘 카드매출 자료 수집 완료 ('+_ok.join(' · ')+')';
        }""",
        """        var _csDayKey=_t0.getFullYear()+'-'+(_t0.getMonth()+1)+'-'+_t0.getDate();
        if(_csOkHideTimer){ clearTimeout(_csOkHideTimer); _csOkHideTimer=null; }
        if(_bad.length){
          // 문제 안내는 계속 떠 있어야 한다(사라지지 않음).
          stEl.dataset.csok='0';
          stEl.style.display=''; stEl.style.opacity=''; stEl.style.transition='';
          stEl.style.background='#fef2f2'; stEl.style.border='1.5px solid #fca5a5'; stEl.style.color='#b91c1c';
          stEl.innerHTML='&#9888;&#65039; 오늘 카드매출 자료가 아직 수집되지 않았습니다: <b>'+_bad.join(', ')+'</b> &mdash; GitHub Actions(카드매출 동기화) 실행 결과를 확인해주세요.';
          // 수집이 정상화되면 완료 안내를 한 번 다시 보여주기 위해 '봤음' 기록을 지운다
          try{ save(_CS_OK_SEEN_KEY, ''); }catch(e){}
        } else {
          // r167: 완료 안내는 그날 처음 한 번만, 6초 동안만.
          var _csSeen=''; try{ _csSeen=load(_CS_OK_SEEN_KEY)||''; }catch(e){}
          if(_csSeen===_csDayKey){ stEl.style.display='none'; stEl.dataset.csok='0'; }
          else{
            stEl.dataset.csok='1';
            stEl.style.display=''; stEl.style.opacity=''; stEl.style.transition='';
            stEl.style.background='#f0fdf4'; stEl.style.border='1.5px solid #86efac'; stEl.style.color='#15803d';
            stEl.innerHTML='&#10004; 오늘 카드매출 자료 수집 완료 ('+_ok.join(' · ')+')';
            try{ save(_CS_OK_SEEN_KEY, _csDayKey); }catch(e){}
            _csOkHideTimer=setTimeout(function(){
              _csOkHideTimer=null;
              var el=document.getElementById('csSyncStatus');
              if(!el || el.dataset.csok!=='1') return;   // 그 사이 빨강으로 바뀌었으면 건드리지 않는다
              el.style.transition='opacity .45s'; el.style.opacity='0';
              setTimeout(function(){
                if(el.dataset.csok!=='1') return;
                el.style.display='none'; el.style.opacity=''; el.style.transition='';
              }, 480);
            }, 6000);
          }
        }""",
        1, 'CSBANNER')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r167(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r166 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r166 2026-08-26 -->', '<!-- test build r167 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
