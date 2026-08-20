# -*- coding: utf-8 -*-
# r109: 카드매출 수집 상태 배너 — 평일 오전 9시 이후, 오늘 자료가 아직 안 들어온
#       지점이 있으면 달력 위에 빨간 경고, 전부 들어왔으면 초록 완료 표시.
#       (주말·오전 9시 이전에는 표시하지 않음 — 수집은 평일 아침 8시 실행)

R109_EDITS = [

# (1) 배너 자리 (달력 바로 위)
("""    <div id="csCalendar"></div>""",
 """    <div id="csSyncStatus" style="display:none;margin:0 0 8px;padding:8px 12px;border-radius:8px;font-size:12.5px;font-weight:700"></div>
    <div id="csCalendar"></div>""", 1),

# (2) _csRenderAll 끝에 상태 판정 추가
("""      metaEl.textContent = syncTexts.length ? ('마지막 동기화 · '+syncTexts.join(' / ')) : '';
    }
  }""",
 """      metaEl.textContent = syncTexts.length ? ('마지막 동기화 · '+syncTexts.join(' / ')) : '';
    }
    // r109: 오늘 수집 성공/실패 배너 (평일 09시 이후에만 판정 — 자동 수집은 평일 08시)
    var stEl=document.getElementById('csSyncStatus');
    if(stEl){
      var _now=new Date();
      var _dow=_now.getDay();
      var _checkable=(_dow>=1&&_dow<=5)&&(_now.getHours()>=9);
      if(!_csMetaCache || !_checkable){ stEl.style.display='none'; }
      else{
        var _t0=new Date(_now.getFullYear(),_now.getMonth(),_now.getDate());
        var _bad=[], _ok=[];
        ['seoul','hwaseong'].forEach(function(b){
          var mt=_csMetaCache[b];
          var d=(mt&&mt.lastSyncedAt)?new Date(mt.lastSyncedAt):null;
          if(d&&!isNaN(d.getTime())&&d>=_t0) _ok.push(_CS_BRANCH_LABEL[b]);
          else _bad.push(_CS_BRANCH_LABEL[b]);
        });
        stEl.style.display='';
        if(_bad.length){
          stEl.style.background='#fef2f2'; stEl.style.border='1.5px solid #fca5a5'; stEl.style.color='#b91c1c';
          stEl.innerHTML='&#9888;&#65039; 오늘 카드매출 자료가 아직 수집되지 않았습니다: <b>'+_bad.join(', ')+'</b> &mdash; GitHub Actions(카드매출 동기화) 실행 결과를 확인해주세요.';
        } else {
          stEl.style.background='#f0fdf4'; stEl.style.border='1.5px solid #86efac'; stEl.style.color='#15803d';
          stEl.innerHTML='&#10004; 오늘 카드매출 자료 수집 완료 ('+_ok.join(' · ')+')';
        }
      }
    }
  }""", 1),
]

def apply_r109(s, path):
    for i,(old,new,exp) in enumerate([(o,n,e) for o,n,e in R109_EDITS]):
        c = s.count(old)
        if c != exp: raise SystemExit('R109 FAIL %s edit %d count %d (expect %d)' % (path, i, c, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r109(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r108 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r108 2026-08-20 -->', '<!-- test build r109 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
