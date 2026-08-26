# -*- coding: utf-8 -*-
# r152: [매입매출 첫 진입 로딩 단축 — 블롭 6개 동시 요청 + 불필요한 깊은복사 제거]
#
#  배경: r151 로 화면 계산은 28ms 까지 줄었지만, 매입매출에 처음 들어갈 때 뜨는
#        "자료 불러오는 중…" 은 계산이 아니라 Firebase 블롭 6개를 받아오는 시간이다.
#        (_fxLoaded 는 한 번 true 가 되면 되돌아가지 않으므로 이 로딩은 세션당 1회)
#
#  실측(매출 15,700 / 매입 12,500 / 입금 10,800건 기준 = JSON 합계 약 6.3MB):
#    sales_서울 1,478KB · sales_화성 1,100KB · purch_서울 1,150KB
#    purch_화성   903KB · dep_서울   1,107KB · dep_화성     732KB
#    JSON 파싱 13ms / 캐시 깊은복사 50ms / concat 0ms  -> CPU 는 거의 무관.
#    즉 로딩의 대부분은 네트워크이고, 그 중 상당 부분이 "순차 대기"였다.
#
#  원인:
#   (1) _fxEnsureData 가 블롭 6개를 for + await 로 하나씩 순서대로 받는다.
#       왕복 지연(RTT)이 6번 그대로 쌓인다. RTT 300ms 면 대기만 1.8초.
#   (2) _fxBlobGet 이 받은 자료를 캐시에 넣으려고 JSON.parse(JSON.stringify(d)) 로
#       통째로 한 번 더 복사한다(6개 합계 약 50ms). 그런데 이 캐시를 읽는 곳은
#       _fxEnsureData(force) 뿐이고, force 는 진입 즉시 해당 키를 delete 하므로
#       사실상 읽히지 않는다 = 순수 낭비.
#
#  수정:
#   A. 6개 블롭을 Promise.all 로 동시 요청. 쌓이던 왕복 지연 6번이 1번으로 줄고,
#      받는 순서와 무관하게 ks 순서대로 다시 정렬해 담으므로 결과는 완전히 동일.
#      ※ 동시 호출 안전성: _fbFetch 는 호출마다 독립(_fbIdToken -> fetch)이고,
#        저장 경로(_fxSaveBig)가 이미 _fxBlobPut 6개를 동시에 던지고 있다.
#   B. _fxBlobGet 의 캐시 저장을 깊은복사 -> 참조 보관으로 변경(약 50ms 절약).
#      캐시 히트 시 깊은복사해서 돌려주는 동작은 그대로 두어 호출부 계약은 유지.
#
#  주의: 받아오는 자료·순서·결과는 하나도 바뀌지 않음. "어떤 순서로 기다리느냐"만 바뀜.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R152 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r152(s, path):
    # A. 블롭 6개 동시 요청
    s = rep(s,
        """      var got={};
      for(var i=0;i<ks.length;i++){ got[ks[i]] = (await _fxBlobGet(ks[i])) || []; }""",
        r"""      // r152: 하나씩 순서대로 기다리던 것을 동시 요청으로. 왕복 지연 6번 -> 1번.
      //  응답 도착 순서와 상관없이 ks 순서대로 담으므로 결과는 기존과 완전히 동일.
      var got={};
      var _got = await Promise.all(ks.map(function(k){ return _fxBlobGet(k); }));
      ks.forEach(function(k, i){ got[k] = _got[i] || []; });""", 1, 'PARALLEL')

    # B. 캐시 저장 시 통째 깊은복사 제거
    s = rep(s,
        """      var d=await r.json();
      if(d!=null){ try{ _fxBlobCache[key]=JSON.parse(JSON.stringify(d)); }catch(_e){} }
      return d;
    }catch(_e){ return null; }
  }
  async function _fxEnsureData(force){""",
        r"""      var d=await r.json();
      // r152: 캐시에 넣으려고 통째로 한 번 더 깊은복사하던 것 제거(6개 합계 약 50ms).
      //  이 캐시는 _fxEnsureData(force) 에서만 읽히는데 force 는 해당 키를 먼저 지우므로
      //  참조 보관으로 충분하다. (히트 시 깊은복사해 돌려주는 계약은 그대로 유지)
      if(d!=null) _fxBlobCache[key]=d;
      return d;
    }catch(_e){ return null; }
  }
  async function _fxEnsureData(force){""", 1, 'NOCLONE')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r152(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r151 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r151 2026-08-26 -->', '<!-- test build r152 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
