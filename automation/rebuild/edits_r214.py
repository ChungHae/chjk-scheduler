# -*- coding: utf-8 -*-
# r214(회계): ① 내용증명 인쇄 줄간격을 실측값으로 ② 회계 탭 구조 개편
#
# ── ① 인쇄 줄간격 (사용자: "PDF로 저장할 때 간격을 좀 더 WORD랑 비슷하게 늘려줄 수 없나?")
#  r212 에서 맑은 고딕의 기본 줄높이를 1.2153em(usWinAscent+Descent/2048)으로 계산했는데,
#  사용자 PC(Whale)에서 실제로 재 보니 **1.3421em** 이었다. 폰트가 보고하는 값과 브라우저가 쓰는 값이 다르다.
#    실측: 9.5pt 맑은 고딕, line-height:normal → 한 줄 17px = 12.75pt → 12.75/9.5 = 1.3421
#  워드 줄높이 = 기본 줄높이 × (w:line 295 / 240 = 1.22917)
#    → 9.5 × 1.3421 × 1.22917 = 15.67pt   (r212 값 14.19pt 보다 줄마다 1.48pt 좁았다)
#  고치는 방법: 계수를 또 하드코딩하지 않고 **문서를 만들 때 그 브라우저에서 직접 잰다**(_nyLineFactor).
#    맑은 고딕이 없는 PC(맥 등)에서도 그 PC의 글꼴 기준으로 맞는다. 측정이 이상하면 1.6497(=1.3421×1.22917) 로 둔다.
#
# ── ② 회계 탭 구조 (사용자 지시)
#  "매입,매출 집계를 집계로 이름 바꿔주고 위의 카테고리로 올려줘. 자료업로드는 이름 그대로 위 카테고리로
#   올려주고, 매입매출을 미수현황으로 이름 바꿔주고 아래의 미수현황 카테고리는 없애줘."
#  전:  회계 > [입출금 | 매입매출 | 카드매출]   +  매입매출 안에 [미수 현황 | 매입·매출 집계 | 자료 업로드]
#  후:  회계 > [입출금 | 미수현황 | 집계 | 자료 업로드 | 카드매출]   (아래 소카테고리 줄은 없앰)
#  - 세 화면 모두 같은 #pageFx 를 쓰고, 페이지 이름(fx / fxsum / fxup)으로 _fxTab 을 정한다.
#  - '자료 업로드' 는 종전대로 마스터(chjk) 전용 — 상위 탭에서 버튼 자체를 숨긴다(_fxSyncAcctNav).
#  - fxSwitchTab 은 남겨두되 switchPage 로 넘기는 호환 래퍼로 바꾼다(옛 호출이 있어도 동작).
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

# ── ① 줄간격 ────────────────────────────────────────────────────────
OLD_LH = """    // r212: 수치를 docx 와 똑같게 맞춘다 (위 주석 참고)
    var LH=function(pt){ return (Math.round(pt*1.4939*100)/100)+'pt'; };   // 워드 줄높이
"""
NEW_LH = """    // r212: 수치를 docx 와 똑같게 맞춘다 (위 주석 참고)
    // r214: 계수를 박지 않고 이 브라우저에서 직접 재서 쓴다
    var _nyLF=_nyLineFactor();
    var LH=function(pt){ return (Math.round(pt*_nyLF*100)/100)+'pt'; };   // 워드 줄높이
"""

OLD_FN = """  function _nyDateStr(d){
"""
NEW_FN = """  // r214: 워드 줄높이 계수 = (글꼴 기본 줄높이) × 1.22917(docx w:line 295/240)
  //  글꼴 기본 줄높이는 브라우저·PC 마다 다르므로 그때그때 재서 쓴다.
  //  (사용자 PC 실측: 맑은 고딕 기본 줄높이 = 1.3421em → 계수 1.6497)
  var _nyLFCache=null;
  function _nyLineFactor(){
    if(_nyLFCache) return _nyLFCache;
    var v=1.6497;
    try{
      var d=document.createElement('div');
      d.style.cssText='position:absolute;left:-9999px;top:0;visibility:hidden;width:500px;'
        + 'font-family:"맑은 고딕","Malgun Gothic",sans-serif;font-size:100px;line-height:normal;white-space:pre';
      d.textContent='가\\n가\\n가\\n가\\n가\\n가';   // 6줄
      document.body.appendChild(d);
      var per=d.getBoundingClientRect().height/6/100;   // em 당 줄높이
      d.parentNode.removeChild(d);
      if(per>0.8 && per<2.5) v=Math.round(per*1.22917*10000)/10000;
    }catch(_e){}
    _nyLFCache=v; return v;
  }
  function _nyDateStr(d){
"""

# ── ② 탭 구조 ───────────────────────────────────────────────────────
OLD_NAV = """<nav class="sub-nav" id="acctSubNav" style="display:none">
  <button class="sub-tab" data-page="armatch">입출금</button>
  <button class="sub-tab" data-page="fx">매입매출</button>
  <button class="sub-tab" data-page="cardsales">카드매출</button>
</nav>
<nav class="sub-nav" id="fxSubNav" style="display:none">
  <button class="file-grp-tab active" data-fxtab="ar" onclick="fxSwitchTab('ar')">미수 현황</button>
  <button class="file-grp-tab" data-fxtab="sum" onclick="fxSwitchTab('sum')">매입·매출 집계</button>
  <button class="file-grp-tab" data-fxtab="up" onclick="fxSwitchTab('up')">자료 업로드</button>
</nav>
"""
NEW_NAV = """<nav class="sub-nav" id="acctSubNav" style="display:none">
  <button class="sub-tab" data-page="armatch">입출금</button>
  <button class="sub-tab" data-page="fx">미수현황</button>
  <button class="sub-tab" data-page="fxsum">집계</button>
  <button class="sub-tab" id="acctTabFxUp" data-page="fxup">자료 업로드</button>
  <button class="sub-tab" data-page="cardsales">카드매출</button>
</nav>
"""

OLD_ACCT = """    var _ACCT=['armatch','fx','cardsales'];
"""
NEW_ACCT = """    var _ACCT=['armatch','fx','fxsum','fxup','cardsales'];   // r214: 집계·자료 업로드를 상위 탭으로
"""

OLD_FXNAV = """    var _fxnav=document.getElementById('fxSubNav'); if(_fxnav) _fxnav.style.display = (page==='fx') ? 'flex' : 'none';
"""
NEW_FXNAV = """    try{ _fxSyncAcctNav(); }catch(_e){}   // r214: '자료 업로드' 는 마스터만
"""

OLD_MAP = """armatch:'pageArmatch', fx:'pageFx', links:'pageLinks', cardsales:'pageCardSales' };"""
NEW_MAP = """armatch:'pageArmatch', fx:'pageFx', fxsum:'pageFx', fxup:'pageFx', links:'pageLinks', cardsales:'pageCardSales' };"""

OLD_GO = """    if (page === 'fx'){ if(typeof renderFxPage==='function') renderFxPage(); }
"""
NEW_GO = """    if (page === 'fx' || page === 'fxsum' || page === 'fxup'){   // r214: 한 화면을 세 탭이 나눠 쓴다
      _fxTab = (page==='fxsum') ? 'sum' : (page==='fxup' ? 'up' : 'ar');
      _fxArPage = 1;
      if(typeof renderFxPage==='function') renderFxPage();
    }
"""

OLD_SW = """  window.fxSwitchTab = function(t){
    if(t==='up' && !_fxUpAllowed()){ showInfoModal('권한','자료 업로드는 마스터 관리자(chjk) 계정만 사용할 수 있습니다.'); return; }
    _fxTab = t; _fxArPage=1; renderFxPage();
  };
"""
NEW_SW = """  // r214: 상위 탭 에서 '자료 업로드' 버튼은 마스터에게만 보인다
  window._fxSyncAcctNav = function(){
    var b=document.getElementById('acctTabFxUp');
    if(b) b.style.display = _fxUpAllowed() ? '' : 'none';
  };
  // r214: 예전 호출이 남아 있어도 동작하도록 switchPage 로 넘긴다
  window.fxSwitchTab = function(t){
    if(t==='up' && !_fxUpAllowed()){ showInfoModal('권한','자료 업로드는 마스터 관리자(chjk) 계정만 사용할 수 있습니다.'); return; }
    switchPage(t==='sum' ? 'fxsum' : (t==='up' ? 'fxup' : 'fx'));
  };
"""

OLD_RND = """    if(_fxTab==='up' && !_fxUpAllowed()) _fxTab='ar';   // r166: 업로드 탭은 마스터 전용
    var nv=document.getElementById('fxSubNav');
    if(nv){ var _ub=nv.querySelector('[data-fxtab="up"]'); if(_ub) _ub.style.display = _fxUpAllowed() ? '' : 'none'; }
    if(nv) nv.querySelectorAll('.file-grp-tab').forEach(function(b){ b.classList.toggle('active', b.dataset.fxtab===_fxTab); });
"""
NEW_RND = """    if(_fxTab==='up' && !_fxUpAllowed()) _fxTab='ar';   // r166: 업로드 탭은 마스터 전용
    try{ _fxSyncAcctNav(); }catch(_e){}   // r214: 소카테고리 줄은 없애고 상위 탭을 맞춘다
"""

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD_FN,    NEW_FN,    1, 'r214 _nyLineFactor (%s)' % path)
    s = rep(s, OLD_LH,    NEW_LH,    1, 'r214 LH (%s)' % path)
    s = rep(s, OLD_NAV,   NEW_NAV,   1, 'r214 탭 markup (%s)' % path)
    s = rep(s, OLD_ACCT,  NEW_ACCT,  1, 'r214 _ACCT (%s)' % path)
    s = rep(s, OLD_FXNAV, NEW_FXNAV, 1, 'r214 fxSubNav 제거 (%s)' % path)
    s = rep(s, OLD_MAP,   NEW_MAP,   1, 'r214 pageMap (%s)' % path)
    s = rep(s, OLD_GO,    NEW_GO,    1, 'r214 switchPage (%s)' % path)
    s = rep(s, OLD_SW,    NEW_SW,    1, 'r214 fxSwitchTab (%s)' % path)
    s = rep(s, OLD_RND,   NEW_RND,   1, 'r214 renderFxPage (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r214 2026-09-30 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
