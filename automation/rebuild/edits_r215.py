# -*- coding: utf-8 -*-
# r215(회계): ① 회계 탭 순서 변경 ② 내용증명 인쇄본을 A4 한 장에 꽉 차게 자동 맞춤
#
# ── ① 탭 순서 (사용자 지시)
#  "회계 탭순서를 집계, 입출금, 미수현황, 카드매출, 자료 업로드 순서로 해줘"
#  전: 입출금 · 미수현황 · 집계 · 자료 업로드 · 카드매출
#  후: 집계 · 입출금 · 미수현황 · 카드매출 · 자료 업로드
#  (회계 상단 탭을 눌렀을 때 처음 열리는 화면은 종전대로 '입출금' 그대로 둔다)
#
# ── ② 인쇄본 높이 (사용자: "PDF는 아직 좀 더 간격을 늘려야할 것 같아. 아직도 A4용지 아래가
#    비어있어. 워드는 A4용지 1장분량 꽉차있고.")
#  r214 에서 줄높이 계수를 글꼴 기본 줄높이 × 1.22917 로 계산했지만, 워드가 실제로 그리는 높이와는
#  여전히 차이가 있었다(워드가 더 넓게 그린다). 계수를 또 눈대중으로 올리는 대신 **결과로 맞춘다**:
#    문서를 만들기 전에 화면 밖 틀(폭 17cm = A4 - 좌우 여백)에 두 번 그려 높이를 재고,
#    A4 한 장의 본문 높이(297 - 11 - 9 = 277mm = 785.2pt)에 꽉 차도록 계수를 역산한다.
#  높이는 계수에 정확히 비례하지 않지만(스페이서·표 최소높이·그림은 고정),
#    높이 = 고정분 + 가변분 × 계수  의 1차식이므로 두 점만 재면 정확히 풀린다.
#    줄높이만 바꾸고 폭은 그대로라 줄바꿈 수가 변하지 않기 때문에 이 1차식이 성립한다.
#  마지막에 785.2pt 를 넘지 않는지 확인하고, 넘으면 3%씩 줄여 두 장이 되지 않게 한다.
#  그림(명판·인감)에 height 를 함께 지정한다 — 재는 시점에 아직 안 불러와도 자리를 정확히 차지하게.
#  목표 773pt(여유 1.5%), 계수 상한은 측정값의 2.6배.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

# ── ① 탭 순서 ───────────────────────────────────────────────────────
OLD_NAV = """  <button class="sub-tab" data-page="armatch">입출금</button>
  <button class="sub-tab" data-page="fx">미수현황</button>
  <button class="sub-tab" data-page="fxsum">집계</button>
  <button class="sub-tab" id="acctTabFxUp" data-page="fxup">자료 업로드</button>
  <button class="sub-tab" data-page="cardsales">카드매출</button>
"""
NEW_NAV = """  <button class="sub-tab" data-page="fxsum">집계</button>
  <button class="sub-tab" data-page="armatch">입출금</button>
  <button class="sub-tab" data-page="fx">미수현황</button>
  <button class="sub-tab" data-page="cardsales">카드매출</button>
  <button class="sub-tab" id="acctTabFxUp" data-page="fxup">자료 업로드</button>
"""

# ── ② 인쇄본 자동 맞춤 ──────────────────────────────────────────────
# (a) html 을 계수 f 로 만드는 함수로 감싼다
OLD_MK = """    var _nyLF=_nyLineFactor();
    var LH=function(pt){ return (Math.round(pt*_nyLF*100)/100)+'pt'; };   // 워드 줄높이
"""
NEW_MK = """    var _mk=function(_nyLF){   // r215: 계수를 바꿔가며 여러 번 만들 수 있게 함수로 감쌌
    var LH=function(pt){ return (Math.round(pt*_nyLF*100)/100)+'pt'; };   // 워드 줄높이
"""

OLD_END = """    _nyPrintHtml(html);
  };
"""
NEW_END = """    return html;
    };
    _nyPrintHtml(await _nyFitHtml(_mk));   // r215: A4 한 장에 꽉 차게 맞춘다
  };
  // r215: 화면 밖 틀에 두 번 그려 높이를 재고, A4 본문 높이에 맞는 줄높이 계수를 역산한다.
  //  높이 = 고정분(스페이서·표 최소높이·그림) + 가변분 × 계수  — 폭이 고정이라 줄바꿈 수가 안 변하며, 그래서 1차식이 정확히 성립한다.
  var _NY_PAGE_PT = 785.2;   // A4 297mm - 위 11mm - 아래 9mm = 277mm
  var _NY_TARGET_PT = 773;   // 꽉 채우되 두 장이 되지 않게 약간의 여유
  async function _nyFitHtml(mk){
    var f0=_nyLineFactor();
    var probe=document.getElementById('nyFitFrame');
    if(probe && probe.parentNode) probe.parentNode.removeChild(probe);
    probe=document.createElement('iframe');
    probe.id='nyFitFrame';
    //  폭을 본문 폭(17cm)으로 맞춰야 줄바꿈이 인쇄본과 같다
    probe.setAttribute('style','position:fixed;left:-10000px;top:0;width:170mm;height:2000mm;border:0;opacity:0');
    document.body.appendChild(probe);
    var measure=function(f){
      try{
        var d=probe.contentWindow.document;
        d.open(); d.write(mk(f)); d.close();
        return d.body.getBoundingClientRect().height*72/96;   // px → pt
      }catch(_e){ return 0; }
    };
    var f=f0;
    try{
      var h0=measure(f0);
      var f1=f0*1.35, h1=measure(f1);
      if(h0>0 && h1>h0){
        f = f0 + (f1-f0)*(_NY_TARGET_PT-h0)/(h1-h0);
        if(!(f>0)) f=f0;
        f = Math.max(f0, Math.min(f0*2.6, f));
        for(var i=0;i<8 && measure(f)>_NY_PAGE_PT; i++) f*=0.97;   // 두 장이 되지 않게
      }
    }catch(_e2){ f=f0; }
    try{ probe.parentNode.removeChild(probe); }catch(_e3){}
    return mk(Math.round(f*10000)/10000);
  }
"""

# (b) 그림에 height 를 함께 지정 — 재는 시점에 아직 안 불러와도 자리를 차지하게
OLD_IMG1 = """'<img src="data:image/png;base64,'+st.b64+'" style="width:6cm;display:inline-block">'"""
NEW_IMG1 = """'<img src="data:image/png;base64,'+st.b64+'" style="width:6cm;height:'+(Math.round(600*st.h/st.w)/100)+'cm;display:inline-block">'"""
OLD_IMG2 = """'<img src="data:image/png;base64,'+sl.b64+'" style="width:1.5cm;display:inline-block">'"""
NEW_IMG2 = """'<img src="data:image/png;base64,'+sl.b64+'" style="width:1.5cm;height:'+(Math.round(150*sl.h/sl.w)/100)+'cm;display:inline-block">'"""

# 창을 닫을 때 재기용 틀도 정리
OLD_CL = """    var f=document.getElementById('nyPrintFrame'); if(f && f.parentNode) f.parentNode.removeChild(f);   // r211
"""
NEW_CL = """    var f=document.getElementById('nyPrintFrame'); if(f && f.parentNode) f.parentNode.removeChild(f);   // r211
    var f2=document.getElementById('nyFitFrame'); if(f2 && f2.parentNode) f2.parentNode.removeChild(f2);   // r215
"""

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD_NAV,  NEW_NAV,  1, 'r215 탭 순서 (%s)' % path)
    s = rep(s, OLD_MK,   NEW_MK,   1, 'r215 _mk 시작 (%s)' % path)
    s = rep(s, OLD_END,  NEW_END,  1, 'r215 _nyFitHtml (%s)' % path)
    s = rep(s, OLD_IMG1, NEW_IMG1, 1, 'r215 명판 height (%s)' % path)
    s = rep(s, OLD_IMG2, NEW_IMG2, 1, 'r215 인감 height (%s)' % path)
    s = rep(s, OLD_CL,   NEW_CL,   1, 'r215 창 닫을 때 정리 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r215 2026-09-30 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
