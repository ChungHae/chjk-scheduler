# -*- coding: utf-8 -*-
# r59: 로컬 파일(file://)에서 주소 검색 시 안내 — 선택 결과가 전달되지 않는 환경임을 알림
R59_EDITS = [
("""  window.clxAddrSearch = function(){
    var wrap=document.getElementById('clxPostWrap'); if(!wrap) return;""",
 """  window.clxAddrSearch = function(){
    var wrap=document.getElementById('clxPostWrap'); if(!wrap) return;
    if(location.protocol==='file:' && !window.__clxFileWarned){
      window.__clxFileWarned=true;
      showInfoModal('주소 검색','로컬 파일로 연 화면에서는 주소를 선택해도 적용되지 않습니다.\\n주소 검색은 배포된 테스트/본 페이지에서 사용해주세요.');
    }"""),
]
def apply_r59(s, path):
    for i,(old,new) in enumerate(R59_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R59 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r59(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r58 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r58 2026-08-13 -->', '<!-- test build r59 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
