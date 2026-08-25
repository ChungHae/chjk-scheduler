# -*- coding: utf-8 -*-
# r149: [업체 목록 렌더링이 조용히 멈추는 문제 — allClients() 방어 처리]
#
#  증상: 업체 목록 화면에서 개수("N개 업체")조차 표시되지 않고 목록도 비어보임
#  (r148 페이지네이션 적용 여부와 무관하게 발생 가능).
#
#  원인 추정: clientList 배열에 null/undefined 같은 손상된 항목이 하나라도 섞이면
#  _clxRender() 맨 앞의 `allClients().slice().sort(function(a,b){ return
#  String(a[0])... })` 에서 즉시 TypeError(Cannot read properties of null (reading
#  '0'))가 발생 → catch 되지 않아 함수 전체가 그 자리에서 멈추고, 그 아래 있는
#  "N개 업체" 표시·목록 렌더링 코드는 아예 실행되지 않음. (Firebase 배열 동기화
#  특성상 중간 항목이 index 삭제되면 해당 자리가 null로 채워져 재구성될 수 있음 —
#  실제로 이런 손상 항목이 들어갔을 가능성이 있음.)
#
#  수정: allClients() 자체에서 이름이 없는/손상된 항목을 걸러내도록 방어 처리.
#  이 함수는 업체 목록·드롭다운 매칭·중복 거래처 진단 등 앱 전체에서 공통으로
#  쓰이므로, 한 곳만 고치면 같은 문제로 다른 화면이 조용히 멈추는 것도 함께 예방됨.
#  걸러진 항목이 있으면 콘솔에 경고를 남겨 추후 원인 데이터 확인이 가능하도록 함.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R149 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r149(s, path):
    s = rep(s,
            "  function allClients(){ return (clientList && clientList.length) ? clientList : CLIENT_DATA.concat(customClients); }",
            r"""  function allClients(){
    var _src = (clientList && clientList.length) ? clientList : CLIENT_DATA.concat(customClients);
    var _out = _src.filter(function(c){ return c && c[0]!=null && String(c[0]).trim()!==''; });
    if(_out.length!==_src.length){
      try{ console.warn('[allClients] 손상된 업체 항목 '+(_src.length-_out.length)+'건을 건너뛰었습니다.'); }catch(_e){}
    }
    return _out;
  }""", 1, 'ALLCLIENTS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r149(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r148 2026-08-25 -->') == 1
            s = s.replace('<!-- test build r148 2026-08-25 -->', '<!-- test build r149 2026-08-25 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
