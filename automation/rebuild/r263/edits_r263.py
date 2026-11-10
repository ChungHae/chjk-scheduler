# -*- coding: utf-8 -*-
# r263 — 같은 품번인데 견적 ℹ️ 에는 구매 링크가 뜨고 원장관리에는 안 뜨던 문제
#   원인: 구매 링크가 세 군데(info.link · info.makerUrl · info.srcUrl)에 들어갈 수 있는데
#         견적 ℹ️ 창만 셋 다 보고, 원장관리(표의 ✎ 버튼·링크 창)는 info.link 만 봤다.
#         원장 엑셀의 '메이커'·'구매처' 칸에 하이퍼링크가 걸려 있으면 makerUrl/srcUrl 로만 저장된다.
#   사용자 보고(2026-11-10): 솔브레인엘티케이 / SGNAA-500-500-2
#   실제 자료 확인: 그 거래처 원장 475행 중 161행이 'URL 은 있는데 info.link 는 없음'(srcUrl 144 · makerUrl 20)
#  사용:  python3 edits_r263.py <index.html> [--test]
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

for forb in ['_qInfoUrl', '_qInfoUrlFrom']:
    assert forb not in s, 'FORBIDDEN(이미 r263 적용됨): ' + forb

# ① 공통 헬퍼
rep(
"""  function _qInfoPopup(info, specLabel){""",
"""  // r263: 추가 정보의 '구매 링크' 는 세 군데에 들어 있을 수 있다.
  //   · info.link     — 규격 추가/수정 창이나 원장관리에서 직접 넣은 주소
  //   · info.makerUrl — 원장 엑셀 '메이커(브랜드)' 칸에 걸려 있던 하이퍼링크
  //   · info.srcUrl   — 원장 엑셀 '구매처' 칸에 걸려 있던 하이퍼링크
  //  견적 ℹ️ 창은 예전부터 셋 다 봤는데 원장관리는 info.link 만 봐서, 같은 품번인데
  //  견적에는 [바로가기]가 뜨고 원장에는 빈칸으로 보였다(2026-11-10 사용자 보고).
  //  이제 두 화면이 이 함수 하나를 같이 쓴다.
  function _qInfoUrl(info){ var i=info||{}; return String(i.link||i.makerUrl||i.srcUrl||'').trim(); }
  // 직접 넣은 주소가 아니라 엑셀 칸에 걸려 있던 링크면, 어디서 온 값인지 한 줄로 알려 준다.
  function _qInfoUrlFrom(info){
    var i=info||{};
    if(i.link) return '';
    if(i.makerUrl) return '엑셀 메이커 칸에 걸려 있던 링크입니다. 저장하면 구매 링크로 옮겨 적습니다.';
    if(i.srcUrl)   return '엑셀 구매처 칸에 걸려 있던 링크입니다. 저장하면 구매 링크로 옮겨 적습니다.';
    return '';
  }

  function _qInfoPopup(info, specLabel){""", 1, '① _qInfoUrl 헬퍼 추가')

rep("""    var _pl=i.link||i.makerUrl||i.srcUrl||'';""",
    """    var _pl=_qInfoUrl(i);   // r263: 원장관리와 같은 규칙""", 1, '① 견적 ℹ️ 창도 헬퍼 사용')

# ② 원장관리 표의 링크 버튼
rep("""      var _mk=_if.maker||'', _src=_if.src||'', _rm=_if.remark||'', _lk=String(_if.link||'').trim();""",
    """      var _mk=_if.maker||'', _src=_if.src||'', _rm=_if.remark||'', _lk=_qInfoUrl(_if);   // r263: 엑셀 칸에 걸린 링크도 포함""",
    1, '② 원장 표 링크 버튼')

# ③ 원장관리 링크 창
rep("""    var cur=(r.info&&r.info.link)?String(r.info.link):'';""",
    """    var cur=_qInfoUrl(r.info);                 // r263
    var _from=_qInfoUrlFrom(r.info);           // r263: 엑셀 칸에서 온 링크면 안내""",
    1, '③ 링크 창 현재값')

rep("""        +'<div style="font-size:12px;color:#9ca3af">'+esc(r.spec||'(빈 규격)')+'</div>'
        +'<input id="qlmLinkIn" value="'+esc(cur)+'" placeholder="https://..." style="width:100%;box-sizing:border-box;padding:7px 10px;border:1px solid #c8d2de;border-radius:0;font-size:13px;font-family:inherit;outline:none">'""",
    """        +'<div style="font-size:12px;color:#9ca3af">'+esc(r.spec||'(빈 규격)')+'</div>'
        +'<input id="qlmLinkIn" value="'+esc(cur)+'" placeholder="https://..." style="width:100%;box-sizing:border-box;padding:7px 10px;border:1px solid #c8d2de;border-radius:0;font-size:13px;font-family:inherit;outline:none">'
        +(_from?('<div style="font-size:11px;color:#9ca3af;line-height:1.6">'+esc(_from)+'</div>'):'')
        +'<div style="font-size:11px;color:#9ca3af;line-height:1.6">비우고 저장하면 이 규격의 구매 링크를 지웁니다.</div>'""",
    1, '③ 링크 창 안내 문구')

# ④ 링크를 비우면 엑셀 칸 링크까지 같이 지운다 (안 그러면 지운 뒤에도 다시 보인다)
rep("""    if(field==='maker'||field==='src'||field==='remark'||field==='link'){   // 추가정보(info) 안의 값들
      var v=String(val==null?'':val).trim();
      if(!r.info) r.info={};
      if(v) r.info[field]=v; else delete r.info[field];
      if(!Object.keys(r.info).length) delete r.info;
      _lmSave(); return;
    }""",
    """    if(field==='maker'||field==='src'||field==='remark'||field==='link'){   // 추가정보(info) 안의 값들
      var v=String(val==null?'':val).trim();
      if(!r.info) r.info={};
      if(v) r.info[field]=v; else delete r.info[field];
      // r263: 구매 링크를 비웠으면 엑셀 칸에 걸려 있던 링크(makerUrl·srcUrl)도 같이 지운다.
      //  안 그러면 지운 뒤에도 그쪽 값이 남아 링크가 계속 보인다.
      if(field==='link' && !v){ delete r.info.makerUrl; delete r.info.srcUrl; }
      if(!Object.keys(r.info).length) delete r.info;
      _lmSave(); return;
    }""", 1, '④ 링크 비우기')

# ⑤ 원장 검색에 링크도 포함
rep("""    return _qNorm(r.spec).indexOf(q)>=0 || _qNorm(r.name).indexOf(q)>=0 || _qNorm(r.disc).indexOf(q)>=0
        || _qNorm(f.maker).indexOf(q)>=0 || _qNorm(f.src).indexOf(q)>=0 || _qNorm(f.remark).indexOf(q)>=0;""",
    """    return _qNorm(r.spec).indexOf(q)>=0 || _qNorm(r.name).indexOf(q)>=0 || _qNorm(r.disc).indexOf(q)>=0
        || _qNorm(f.maker).indexOf(q)>=0 || _qNorm(f.src).indexOf(q)>=0 || _qNorm(f.remark).indexOf(q)>=0
        || _qNorm(_qInfoUrl(f)).indexOf(q)>=0;   // r263: 구매 링크 주소로도 찾기""",
    1, '⑤ 원장 검색에 링크 포함')

# ⑥ 규격 추가/수정 창의 '구매 링크' 칸도 같은 규칙으로 채운다
rep("""<input id="qsLink" value="'+esc(info.link||'')+'" placeholder="https://..." """,
    """<input id="qsLink" value="'+esc(_qInfoUrl(info))+'" placeholder="https://..." """,
    1, '⑥ 규격 수정 창 링크 칸')

rep("""    if(_qsMode==='edit'&&_qsRid){ var _pr=_qRows.find(function(x){return x._rid===_qsRid;}); if(_pr&&_pr.info){ if(_pr.info.makerUrl&&_info.maker===_pr.info.maker) _info.makerUrl=_pr.info.makerUrl; if(_pr.info.srcUrl&&_info.src===_pr.info.src) _info.srcUrl=_pr.info.srcUrl; } }""",
    """    // r263: 링크 칸을 비우고 저장했으면 엑셀 칸 링크(makerUrl·srcUrl)도 가져오지 않는다 — 그래야 실제로 지워진다.
    if(_lk && _qsMode==='edit'&&_qsRid){ var _pr=_qRows.find(function(x){return x._rid===_qsRid;}); if(_pr&&_pr.info){ if(_pr.info.makerUrl&&_info.maker===_pr.info.maker) _info.makerUrl=_pr.info.makerUrl; if(_pr.info.srcUrl&&_info.src===_pr.info.src) _info.srcUrl=_pr.info.srcUrl; } }""",
    1, '⑥ 규격 수정 저장 — 링크 비우면 엑셀 링크도 제거')

if IS_TEST:
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'test marker not found'
    s = s.replace(m.group(0), '<!-- test build r263 2026-11-10 -->')
    print('  ok  test marker %s -> r263' % m.group(0))

for k in ['_qInfoUrl', '_qInfoUrlFrom', '_qInfoUrl(_if)', '_qInfoUrl(r.info)', '_qInfoUrl(info)']:
    assert k in s, 'NEED missing: ' + k
for k in ['qLedgerLink', '_qInfoPopup', '_lmRowHtml', 'qsSave']:
    assert k in s, 'KEEP missing: ' + k

io.open(path, 'w', encoding='utf-8').write(s)
print('r263 적용 완료: %d -> %d' % (orig, len(s)))
