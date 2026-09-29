# -*- coding: utf-8 -*-
# r211(회계): 내용증명 — 인쇄를 새 탭 미리보기 대신 '바로 인쇄창'으로, 작성 창 위치를 아래로
#  사용자 지시: "내용증명의 미리보기 방식이 별로야. 그냥 바로 인쇄창을 띄우던지 아니면 팝업을 띄우던지
#              하는게 낫지 않을까? 그리고 내용증명 작성 팝업창이 너무 상단이야. 조금 아래로 내리면 좋겠어."
#  처리:
#   (1) fxNyPrint — window.open 으로 새 탭을 띄우고 안내바를 보여주던 방식을 버리고,
#       화면 밖 iframe 에 문서를 그린 뒤 그림·글꼴이 다 준비되면 바로 print() 를 부른다.
#       팝업 차단에 걸리지 않고, 클릭 한 번에 인쇄창(→ 'PDF로 저장')이 뜬다.
#       안내바(.noprint)와 자리차지 여백은 이제 필요 없으므로 문서에서 뺀다.
#       iframe 은 인쇄가 끝난 뒤(afterprint) 정리하고, 창을 닫을 때도 지운다.
#   (2) 작성 창을 위에서 조금 내린다 — padding-top 40px → clamp(48px, 12vh, 150px).
#       화면이 낮으면 48px 로 붙어 잘리지 않는다.
#   (3) 버튼 이름을 '미리보기 · 인쇄(PDF)' → '인쇄 · PDF 저장' 으로.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

# (2) 창 위치
OLD1 = """position:fixed;inset:0;background:rgba(10,20,40,.45);z-index:100080;display:flex;align-items:flex-start;justify-content:center;overflow:auto;padding:40px 16px"""
NEW1 = """position:fixed;inset:0;background:rgba(10,20,40,.45);z-index:100080;display:flex;align-items:flex-start;justify-content:center;overflow:auto;padding:clamp(48px,12vh,150px) 16px 40px"""

# (3) 버튼 이름
OLD2 = """미리보기 · 인쇄(PDF)</button>"""
NEW2 = """인쇄 · PDF 저장</button>"""

# (1) 안내바 제거
OLD3 = """      + '@media print{.noprint{display:none}}</style></head><body>'
      + '<div class="noprint" style="position:fixed;top:0;left:0;right:0;background:#1B3A6B;color:#fff;padding:8px 14px;font-size:12px;z-index:9">'
      +   '이 창에서 인쇄(Ctrl+P) → 대상을 “PDF로 저장”으로 고르면 PDF가 됩니다. '
      +   '<button onclick="window.print()" style="margin-left:10px;padding:3px 12px;border:1px solid #fff;background:transparent;color:#fff;cursor:pointer">인쇄</button></div>'
      + '<div class="noprint" style="height:38px"></div>'
      + '<div class="t">내 용 증 명 서</div>'
"""
NEW3 = """      + '</style></head><body>'
      + '<div class="t">내 용 증 명 서</div>'
"""

# (1) 새 탭 대신 화면 밖 iframe → 바로 인쇄
OLD4 = """    var w=window.open('', '_blank');
    if(!w){ showInfoModal('내용증명','팝업이 차단되었습니다. 이 사이트의 팝업을 허용해 주세요.'); return; }
    w.document.open(); w.document.write(html); w.document.close();
  };
"""
NEW4 = """    _nyPrintHtml(html);
  };
  // r211: 화면 밖 iframe 에 그려서 바로 인쇄창을 띄운다 (새 탭 미리보기 없음 · 팝업 차단 영향 없음)
  function _nyPrintHtml(html){
    var old=document.getElementById('nyPrintFrame'); if(old) old.parentNode.removeChild(old);
    var ifr=document.createElement('iframe');
    ifr.id='nyPrintFrame';
    //  visibility:hidden 으로 숨기면 빈 페이지가 인쇄되는 브라우저가 있어 화면 밖으로 보낸다.
    ifr.setAttribute('style','position:fixed;left:-10000px;top:0;width:210mm;height:297mm;border:0;opacity:0');
    document.body.appendChild(ifr);
    var d=ifr.contentWindow.document;
    d.open(); d.write(html); d.close();
    var done=false;
    var go=function(){
      if(done) return; done=true;
      try{
        ifr.contentWindow.focus();
        try{ ifr.contentWindow.onafterprint=function(){ setTimeout(function(){ try{ ifr.parentNode.removeChild(ifr); }catch(_e){} }, 300); }; }catch(_e2){}
        ifr.contentWindow.print();
      }catch(e){ try{ ifr.parentNode.removeChild(ifr); }catch(_e3){} }
    };
    //  그림(명판·인감)과 글꼴이 준비된 뒤에 인쇄창을 띄운다 — 안 그러면 도장이 빠진 채 인쇄된다.
    var imgs=Array.prototype.slice.call(d.images||[]);
    Promise.all(imgs.map(function(im){
      return (im.complete && im.naturalWidth) ? Promise.resolve()
           : new Promise(function(r){ im.onload=r; im.onerror=r; setTimeout(r, 1500); });
    })).then(function(){
      try{ return (d.fonts && d.fonts.ready) ? d.fonts.ready : null; }catch(_e){ return null; }
    }).catch(function(){}).then(function(){ setTimeout(go, 120); });
    setTimeout(go, 2500);   // 어떤 이유로든 준비 신호가 안 오면 그냥 인쇄한다
  }
"""

# 창을 닫을 때 인쇄용 iframe 도 정리
OLD5 = """  window.fxNyClose = function(){ var h=document.getElementById('nyWrap'); if(h) h.innerHTML=''; _nyOpen=null; };
"""
NEW5 = """  window.fxNyClose = function(){
    var h=document.getElementById('nyWrap'); if(h) h.innerHTML='';
    var f=document.getElementById('nyPrintFrame'); if(f && f.parentNode) f.parentNode.removeChild(f);   // r211
    _nyOpen=null;
  };
"""

# 주석 머리말
OLD6 = "  // ── 미리보기 · 인쇄(PDF) ─"
NEW6 = "  // ── 인쇄 · PDF 저장 (r211: 바로 인쇄창) ─"

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD1, NEW1, 1, 'r211 창 위치 (%s)' % path)
    s = rep(s, OLD2, NEW2, 1, 'r211 버튼 이름 (%s)' % path)
    s = rep(s, OLD3, NEW3, 1, 'r211 안내바 제거 (%s)' % path)
    s = rep(s, OLD4, NEW4, 1, 'r211 바로 인쇄 (%s)' % path)
    s = rep(s, OLD5, NEW5, 1, 'r211 닫을 때 정리 (%s)' % path)
    s = rep(s, OLD6, NEW6, 1, 'r211 주석 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r211 2026-09-29 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
