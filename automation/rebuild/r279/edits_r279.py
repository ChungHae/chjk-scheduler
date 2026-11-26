# -*- coding: utf-8 -*-
# r279 — ① 매입처를 상단 탭에서 빼고 업무 하위 탭(사이트 ↔ 감사 사이)으로 옮김
#        ② 감사 안내문을 꼭 필요한 말만 남기고 줄임 + 툴바 설명 문구 삭제
#        ③ 엑셀을 끌어다 놓아도(드래그&드롭) 올라가게 함
#   사용자 지시(2026-11-26)
#  사용:  python3 edits_r279.py <index.html> [--test]
import io, sys, re

path = sys.argv[1]
IS_TEST = ('--test' in sys.argv)
s = io.open(path, encoding='utf-8').read()
orig = len(s)

def rep(old, new, cnt, label):
    global s
    n = s.count(old)
    assert n == cnt, 'ANCHOR %s: expected %d, found %d' % (label, cnt, n)
    s = s.replace(old, new)
    print('  ok  %s' % label)

assert '_asBindDrop' not in s, 'FORBIDDEN(이미 r279 적용됨)'

# ① 상단 탭에서 매입처 제거
rep('''  <button class="page-tab" id="tabEtc">업무</button><!-- r252: 구 '기타' · r276: 이름 정리 -->
  <button class="page-tab" data-page="purchase">매입처</button>
  <button class="page-tab" data-page="inventory">재고</button>''',
    '''  <button class="page-tab" id="tabEtc">업무</button><!-- r252: 구 '기타' · r276: 이름 정리 · r279: 매입처가 이 아래로 -->
  <button class="page-tab" data-page="inventory">재고</button>''',
    1, '① 상단 탭에서 매입처 제거')

# ① 업무 하위 탭에 매입처 — 사이트와 감사 사이
rep('''  <button class="sub-tab" data-page="links">사이트</button><!-- r276: 이름 정리 -->
  <button class="sub-tab" data-page="audit">감사</button><!-- r278 -->''',
    '''  <button class="sub-tab" data-page="links">사이트</button><!-- r276: 이름 정리 -->
  <button class="sub-tab" data-page="purchase">매입처</button><!-- r279: 상단 탭에서 옮겨 옴 -->
  <button class="sub-tab" data-page="audit">감사</button><!-- r278 -->''',
    1, '① 업무 하위 탭에 매입처')

rep("    var _ETC=['links','audit'];   // r278",
    "    var _ETC=['links','purchase','audit'];   // r278 · r279: 매입처를 업무 아래로",
    1, '① _ETC 에 purchase 추가')

# ② 감사 툴바 CSS — r278 이 #pageAudit 몫을 빼먹어 툴바가 flex 가 아니었다(라벨이 버튼에 붙어 보임)
rep("""    #pageLinks .inv-flat-div { width:1px; height:18px; background:#e5e5e5; flex-shrink:0; margin:0 4px; }""",
    """    #pageLinks .inv-flat-div { width:1px; height:18px; background:#e5e5e5; flex-shrink:0; margin:0 4px; }
    /* r279: 감사 툴바 — 링크·매입처 툴바와 동일 스타일(r278 에서 빠져 있었다) */
    #pageAudit .inv-toolbar { display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin: calc(var(--mpy)*-1) calc(var(--mpx)*-1) 14px; min-height:var(--snh,36px); padding:4px var(--mpx); background:#fff; border:0; border-bottom:1px solid #e5e5e5; box-shadow:0 2px 6px rgba(15,23,42,.06); box-sizing:border-box; }
    #pageAudit .inv-flat-label { font-size:12.5px; font-weight:700; color:#14305c; white-space:nowrap; flex-shrink:0; margin-right:6px; }""",
    1, '② 감사 툴바 CSS 추가')

# ② 툴바 설명 문구 삭제
rep("""      + '<span style="font-size:12px;color:#6b7280">SMC 유저특가 엑셀 → 거래명세표 (양식 용지에 글자만 인쇄)</span>'\n""",
    "", 1, '② 툴바 설명 문구 삭제')

# ② 안내문을 짧게 + 끌어다 놓는 자리로
rep("""      h += '<div style="border:1px solid #e5e7eb;background:#fafbfc;padding:22px;font-size:13px;color:#374151;line-height:1.9">'
        + '<b style="color:#1B3A6B">쓰는 방법</b><br>'
        + '① SMC UbiCom 에서 <b>유저특가 조회 → 엑셀</b> 로 받은 파일을 [엑셀 올리기] 로 넣습니다.<br>'
        + '② 엑셀의 <b>유저명</b>에 우리 업체를 한 번 이어 주면 그 뒤로는 자동으로 연결됩니다.<br>'
        + '③ <b>물류출하일</b>마다 거래명세표가 한 묶음씩 생기고, 발행일은 <b>물류출하일 + 2영업일</b>(토·일·공휴일 건너뜀)로 잡힙니다.<br>'
        + '④ 품명은 그 업체 <b>원장</b>에서 품번으로 찾아 "품목 품번" 으로 적습니다. 못 찾으면 직접 넣을 수 있고, 넣은 값은 원장에도 등록됩니다.<br>'
        + '⑤ [저장하고 인쇄] 를 누르면 누적 저장되고, <b>양식 용지</b>에 글자만 찍힙니다.'
        + '</div>';""",
    """      h += '<div id="asDrop" style="border:2px dashed #c8d2de;background:#fafbfc;padding:40px 22px;text-align:center;line-height:1.9">'
        + '<div style="font-size:14.5px;font-weight:700;color:#1B3A6B">엑셀을 여기에 끌어다 놓으세요</div>'
        + '<div style="font-size:12.5px;color:#6b7280;margin-top:4px">SMC 유저특가 조회에서 받은 파일 · 위 [엑셀 올리기] 와 같습니다</div>'
        + '<div style="font-size:12px;color:#8a94a6;margin-top:10px">물류출하일마다 한 장 · 발행일은 출하일 + 2영업일</div>'
        + '</div>';""",
    1, '② 안내문 간략화 + 끌어다 놓는 자리')

# ② [인쇄 보정]이 마스터에게도 보이게 (_isAdmin 은 role==='admin' 과 이름 'chjk' 만 본다)
rep("""    var adm = (typeof _isAdmin==='function') ? _isAdmin() : ((_authUser&&(_authUser.role==='master'||_authUser.role==='admin'))||false);""",
    """    var adm = (_authUser && (_authUser.role==='master' || _authUser.role==='admin')) || ((typeof _isAdmin==='function') ? _isAdmin() : false);   // r279: 마스터도 보정 가능""",
    1, '② 인쇄 보정 — 마스터 포함')

# ③ 파일 읽기를 함수로 빼고, 버튼·드롭이 같이 쓴다
rep("""  window.asPick = function(){ var i=document.getElementById('asFile'); if(i) i.click(); };
  window.asOnFile = async function(ev){
    var f = ev.target.files && ev.target.files[0]; ev.target.value='';
    if(!f) return;
    try{""",
    """  window.asPick = function(){ var i=document.getElementById('asFile'); if(i) i.click(); };
  window.asOnFile = async function(ev){
    var f = ev.target.files && ev.target.files[0]; ev.target.value='';
    await _asTakeFile(f);
  };
  // r279: 끌어다 놓기 — 화면 어디에 놓아도 받는다
  function _asHasFile(ev){
    try{ var dt=ev.dataTransfer; if(!dt) return false;
      var t=dt.types; if(!t) return false;
      for(var i=0;i<t.length;i++){ if(t[i]==='Files') return true; }
      return false;
    }catch(e){ return false; }
  }
  function _asDropOn(on){
    var el=document.getElementById('pageAudit'); if(!el) return;
    el.style.outline = on ? '3px dashed #1B3A6B' : '';
    el.style.outlineOffset = on ? '-6px' : '';
    var z=document.getElementById('asDrop');
    if(z){ z.style.borderColor = on ? '#1B3A6B' : '#c8d2de'; z.style.background = on ? '#eaf1fb' : '#fafbfc'; }
  }
  function _asBindDrop(){
    var el=document.getElementById('pageAudit');
    if(!el || el.__asDrop) return;
    el.__asDrop = 1;
    el.addEventListener('dragenter', function(ev){ if(!_asHasFile(ev)) return; ev.preventDefault(); _asDropOn(true); });
    el.addEventListener('dragover',  function(ev){ if(!_asHasFile(ev)) return; ev.preventDefault(); try{ ev.dataTransfer.dropEffect='copy'; }catch(e){} _asDropOn(true); });
    el.addEventListener('dragleave', function(ev){ if(!el.contains(ev.relatedTarget)) _asDropOn(false); });
    el.addEventListener('drop', function(ev){
      if(!_asHasFile(ev)) return;
      ev.preventDefault(); _asDropOn(false);
      var f = ev.dataTransfer.files && ev.dataTransfer.files[0];
      _asTakeFile(f);
    });
  }
  async function _asTakeFile(f){
    if(!f) return;
    if(!/\\.(xls|xlsx|htm|html)$/i.test(f.name||'')){ showInfoModal('엑셀 읽기','SMC 유저특가 조회에서 받은 엑셀 파일(.xls)을 올려 주세요.'); return; }
    try{""",
    1, '③ 드래그&드롭 + 파일 읽기 분리')

rep("""      _asRender();
    }catch(e){ showInfoModal('엑셀 읽기', String(e && e.message || e)); }
  };
  window.asLink = async function(di){""",
    """      _asRender();
    }catch(e){ showInfoModal('엑셀 읽기', String(e && e.message || e)); }
  }
  window.asLink = async function(di){""",
    1, '③ 함수 닫기 고침')

rep("""      el.innerHTML = h + '</div>';
      return;""",
    """      el.innerHTML = h + '</div>';
      _asBindDrop();   // r279 — 엑셀 올리기 전 화면에서도 끌어다 놓을 수 있게
      return;""",
    1, '③ 빈 화면에도 드롭 연결')

rep("""    h += '<datalist id="asClients">'+opts+'</datalist></div>';
    el.innerHTML = h;
  }""",
    """    h += '<datalist id="asClients">'+opts+'</datalist></div>';
    el.innerHTML = h;
    _asBindDrop();   // r279
  }""",
    1, '③ 렌더 뒤 드롭 연결')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r279 2026-11-26 -->')
    print('  ok  test marker %s -> r279' % m.group(0))

# NEED
for k in ['<button class="sub-tab" data-page="purchase">매입처</button>',
          "var _ETC=['links','purchase','audit']",
          'id="asDrop"', '엑셀을 여기에 끌어다 놓으세요',
          '_asBindDrop', '_asTakeFile', '_asHasFile', '_asDropOn',
          '#pageAudit .inv-toolbar', '#pageAudit .inv-flat-label']:
    assert k in s, 'NEED missing: ' + k
# KEEP
for k in ['id="pagePurchase"', 'renderAuditPage', 'window.asOnFile', 'window.asPick',
          'id="tabEtc"', '<button class="sub-tab" data-page="audit">감사</button>']:
    assert k in s, 'KEEP missing: ' + k
# FORBIDDEN
assert '<button class="page-tab" data-page="purchase">' not in s, 'FORBIDDEN: 상단 매입처 탭이 남아 있다'
assert 'SMC 유저특가 엑셀 → 거래명세표 (양식 용지에 글자만 인쇄)</span>' not in s, 'FORBIDDEN: 툴바 설명 문구가 남아 있다'
assert '쓰는 방법' not in s, 'FORBIDDEN: 옛 안내문이 남아 있다'

io.open(path, 'w', encoding='utf-8').write(s)
print('r279 적용 완료: %d -> %d' % (orig, len(s)))
