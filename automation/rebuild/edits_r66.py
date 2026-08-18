# -*- coding: utf-8 -*-
# r66: window.clxAddrSearch 복원.
# r62 모듈의 슬라이스 치환(START=_clxRender, END=전화번호 주석)이 사이에 있던
# clxAddrSearch 정의(r51 원본 + r59 file:// 경고)를 통째로 삭제했음.
# ※ 재구축 체인에서 edits_r62.py 적용 이후에는 반드시 이 모듈을 적용할 것.

CLX_ADDR = '''  // 카카오(다음) 우편번호 검색 — 무료·키 불필요. 폼 안 레이어에 임베드해 각진 디자인 유지.
  window.clxAddrSearch = function(){
    var wrap=document.getElementById('clxPostWrap'); if(!wrap) return;
    if(location.protocol==='file:' && !window.__clxFileWarned){
      window.__clxFileWarned=true;
      showInfoModal('주소 검색','로컬 파일로 연 화면에서는 주소를 선택해도 적용되지 않습니다.\\n주소 검색은 배포된 테스트/본 페이지에서 사용해주세요.');
    }
    if(wrap.style.display==='block'){ wrap.style.display='none'; wrap.innerHTML=''; return; }
    function run(){
      wrap.innerHTML=''; wrap.style.display='block';
      try{
        new daum.Postcode({
          oncomplete: function(data){
            var f=document.getElementById('clxForm'); if(!f) return;
            var z=f.querySelector('.clx-f[data-k="zip"]'), a=f.querySelector('.clx-f[data-k="addr"]'), a2=f.querySelector('.clx-f[data-k="addr2"]');
            if(z) z.value=data.zonecode||'';
            if(a) a.value=data.roadAddress||data.jibunAddress||'';
            wrap.style.display='none'; wrap.innerHTML='';
            if(a2){ try{ a2.focus(); }catch(_e){} }
          },
          width:'100%', height:'100%'
        }).embed(wrap);
      }catch(_e){ wrap.style.display='none'; showInfoModal('주소 검색','주소 검색 화면을 여는 데 실패했습니다. 다시 시도해주세요.'); }
    }
    if(window.daum && window.daum.Postcode){ run(); return; }
    var sc=document.createElement('script');
    sc.src='https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js';
    sc.onload=run;
    sc.onerror=function(){ showInfoModal('주소 검색','주소 검색 스크립트를 불러오지 못했습니다. 인터넷 연결을 확인해주세요.'); };
    document.head.appendChild(sc);
  };
'''

ANCHOR = "  // 전화번호 하이픈 자동 삽입"

def apply_r66(s, path):
    assert s.count("window.clxAddrSearch = function") == 0, path + ': already present'
    n = s.count(ANCHOR)
    if n != 1: raise SystemExit('R66 FAIL %s anchor count %d' % (path, n))
    return s.replace(ANCHOR, CLX_ADDR + ANCHOR)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r66(s, path)
        assert s.count("window.clxAddrSearch = function") == 1
        if 'testpage' in path:
            assert s.count('<!-- test build r65 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r65 2026-08-13 -->', '<!-- test build r66 2026-08-14 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
