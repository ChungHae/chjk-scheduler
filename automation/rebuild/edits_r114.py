# -*- coding: utf-8 -*-
# r114: 견적 규격 자동완성 첫 사용 지연 개선 — 전체 원장 색인을 견적 탭 진입
#       즉시 백그라운드로 미리 구축. (기존에는 거래처 선택 후에야 시작 →
#       거래처 선택 직후 바로 규격을 붙여넣으면 색인이 아직 없어 "불러오는 중"이던 문제)

OLD = """    if (page === 'estimate'){
      _qCurId=''; _qRows=[];
      var _vs=document.getElementById('qVendorSearch'); if(_vs) _vs.value='';
      var _qs=document.getElementById('qSpec'); if(_qs) _qs.value='';
      renderEstimatePage();
    }"""
NEW = """    if (page === 'estimate'){
      _qCurId=''; _qRows=[];
      var _vs=document.getElementById('qVendorSearch'); if(_vs) _vs.value='';
      var _qs=document.getElementById('qSpec'); if(_qs) _qs.value='';
      // r114: 전체 원장 색인 선구축 — 거래처 고르는 동안 미리 로드해 규격 첫 검색/붙여넣기 즉시 반응
      if(!_qAllReady && !_qAllLoading){ _qAllLoading=true; _qEnsureAllIdx().then(function(){ _qAllLoading=false; }).catch(function(){ _qAllLoading=false; }); }
      renderEstimatePage();
    }"""

def apply_r114(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R114 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r114(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r113 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r113 2026-08-20 -->', '<!-- test build r114 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
