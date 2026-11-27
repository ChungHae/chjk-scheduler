#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r289 — 저장된 명세표 쪽 이동 · 중복 팝업 문구 · 미리보기 팝업 · 카테고리는 첫 화면부터

사용자 지시(2026-11-27)
  · 저장된 명세표는 한 쪽에 15건
  · 이전/다음 사이에 쪽 번호를 넣어 중간으로도 가고, [처음]·[끝] 단추도 넣을 것
  · 쪽이 많으면 번호는 5개만, 보고 있는 쪽을 가운데에 두고 보일 것
  · 이전·다음 단추는 글자만 (◀ ▶ 기호 제거)
  · 중복 팝업은 건수 한 줄 + [그대로 올리기] 설명 / 줄바꿈 / [취소] 설명 — 세부 내역은 빼기
  · 미리보기는 새 창이 아니라 지금 화면의 팝업으로
  · 상단 카테고리와 하위 카테고리를 누르면 마지막에 보던 화면이 아니라 첫 화면이 나오게

사용법:  python3 edits_r289.py <입력 index.html> <출력 index.html> [--test]
"""
import sys

N = [0]

def main():
    if len(sys.argv) < 3:
        print('usage: edits_r289.py <in> <out> [--test]'); return 1
    src, dst = sys.argv[1], sys.argv[2]
    is_test = '--test' in sys.argv[3:]
    with open(src, encoding='utf-8') as f:
        s = f.read()

    def rep(old, new, cnt, label):
        nonlocal s
        got = s.count(old)
        assert got == cnt, 'anchor %s: expected %d, found %d' % (label, cnt, got)
        N[0] += 1
        s = s.replace(old, new)

    for k in ['var _AS_PER = 20;', 'window.asPreview = function(di){', 'function switchPage(page) {']:
        assert k in s, 'NEED %s' % k

    # ── ① 한 쪽에 15건 ─────────────────────────────────────────
    rep('var _AS_PER = 20;', 'var _AS_PER = 15;', 1, 'per-page')

    # ── ②③ 쪽 이동 줄: [처음][이전] 번호 5개 [다음][끝] · 기호 없음 ──
    OLD_PAGER = """    if(pages>1){
      h += '<div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-top:14px;font-size:12.5px">'
        + _asBtn('◀ 이전','asLGo('+(_asLPage-1)+')')
        + '<span style="color:#6b7280">'+(_asLPage+1)+' / '+pages+'</span>'
        + _asBtn('다음 ▶','asLGo('+(_asLPage+1)+')')
        + '</div>';
    }"""
    NEW_PAGER = """    if(pages>1){
      var _NW = _AS_PAGE_NUMS;                                  // r289: 한 번에 보이는 쪽 번호 개수
      var _a = Math.max(0, Math.min(_asLPage - Math.floor(_NW/2), pages - _NW));
      var _b = Math.min(pages, _a + _NW);
      var _nums = '';
      for(var _p=_a; _p<_b; _p++){
        _nums += (_p===_asLPage)
          ? '<b style="display:inline-block;min-width:30px;padding:5px 9px;text-align:center;border:1px solid #1B3A6B;background:#1B3A6B;color:#fff;font-size:12.5px">'+(_p+1)+'</b>'
          : _asBtn(String(_p+1), 'asLGo('+_p+')');
      }
      h += '<div style="display:flex;align-items:center;justify-content:center;gap:6px;margin-top:14px;font-size:12.5px;flex-wrap:wrap">'
        + _asBtn('처음','asLGo(0)')
        + _asBtn('이전','asLGo('+(_asLPage-1)+')')
        + _nums
        + _asBtn('다음','asLGo('+(_asLPage+1)+')')
        + _asBtn('끝','asLGo('+(pages-1)+')')
        + '<span style="margin-left:6px;color:#6b7280">'+(_asLPage+1)+' / '+pages+'</span>'
        + '</div>';
    }"""
    rep(OLD_PAGER, NEW_PAGER, 1, 'pager')
    rep('  var _AS_PER = 15;', '  var _AS_PER = 15;\n  var _AS_PAGE_NUMS = 5;                       // r289: 쪽 번호를 한 번에 몇 개 보일지', 1, 'page-nums')

    # ── ④ 중복 팝업 문구 ───────────────────────────────────────
    OLD_DUP = """        showConfirmModal('중복 확인 — 그대로 올릴까요?',
          '올린 자료 가운데 이미 저장된 거래명세표와 같은 내용이 ' + dups.length + '건 있습니다.\\n'
          + dups.slice(0,6).map(function(x){ return '  · '+(x.d.date||'')+' 번호 '+(x.d.dup.no||'')+' · '+(x.dr.vname||'')+' ('+(x.d.rows.length)+'품목)'; }).join('\\n')
          + (dups.length>6?('\\n  … 모두 '+dups.length+'건'):'')
          + '\\n\\n[그대로 올리기] 를 고르면 화면에 그대로 띄웁니다. [취소] 하면 이 파일을 버립니다.',
          function(){ _commit(); }, '그대로 올리기', '#b45309');"""
    NEW_DUP = """        showConfirmModal('중복 확인 — 그대로 올릴까요?',
          '이미 저장된 거래명세표와 같은 내용이 ' + dups.length + '건 있습니다.\\n\\n'
          + '[그대로 올리기] 를 고르면 화면에 그대로 띄웁니다.\\n'
          + '[취소] 하면 이 파일을 버립니다.',
          function(){ _commit(); }, '그대로 올리기', '#b45309');"""
    rep(OLD_DUP, NEW_DUP, 1, 'dup-text')

    # ── ⑤ 미리보기를 지금 화면의 팝업으로 ───────────────────────
    OLD_PREV = """  window.asPreview = function(di){
    var dr=_asDrafts[di];
    var w=window.open('','_blank'); if(!w){ showInfoModal('미리보기','팝업이 막혀 있습니다.'); return; }
    w.document.write(_asDocHtml(dr, dr.docs, 'form')); w.document.close();
  };"""
    NEW_PREV = """  // r289: 새 창이 아니라 지금 화면 위의 팝업으로 보여 준다
  function _asOpenPreview(html, title){
    var ov=_asOverlay('asPrevOv');
    ov.innerHTML='<div style="width:100%;max-width:1040px;height:92vh;background:#fff;border:1px solid #c8d2de;display:flex;flex-direction:column">'
      + '<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:2px solid #1B3A6B">'
      +   '<b style="font-size:15px;color:#1B3A6B">'+esc(title||'미리보기')+'</b>'
      +   '<div style="display:flex;gap:8px">' + _asBtn('인쇄','asPrevPrint()','primary')
      +     '<button class="btn" onclick="document.getElementById(\\'asPrevOv\\').style.display=\\'none\\'" style="padding:4px 10px">닫기</button></div>'
      + '</div>'
      + '<iframe id="asPrevFrame" style="flex:1;width:100%;border:0;background:#e9eef5"></iframe></div>';
    ov.style.display='flex';
    var fr=document.getElementById('asPrevFrame');
    var fd=fr.contentWindow.document; fd.open(); fd.write(html); fd.close();
  }
  window.asPrevPrint = function(){
    var fr=document.getElementById('asPrevFrame'); if(!fr) return;
    try{ fr.contentWindow.focus(); fr.contentWindow.print(); }catch(e){}
  };
  window.asPreview = function(di){
    var dr=_asDrafts[di];
    _asOpenPreview(_asDocHtml(dr, dr.docs, 'form'), '미리보기 — '+(dr.vname||''));
  };"""
    rep(OLD_PREV, NEW_PREV, 1, 'preview')

    # ── ⑥ 카테고리를 누르면 첫 화면부터 ─────────────────────────
    rep('  function switchPage(page) {\n',
        '  // r289: 탭을 누르면 그 자리의 첫 화면으로 되돌린다 (마지막에 보던 화면 기억 안 함)\n'
        '  function _navReset(page){\n'
        "    try{ if(page==='estimate' && typeof qSetSubTab==='function') qSetSubTab('quote'); }catch(_e){}\n"
        "    try{ if(page==='files' && typeof setFileGroup==='function') setFileGroup('충해전기'); }catch(_e){}\n"
        "    try{ if(page==='audit' && typeof window._asResetView==='function') window._asResetView(); }catch(_e){}\n"
        '  }\n'
        '  function switchPage(page, fresh) {\n', 1, 'switchPage-sig')

    rep("    document.getElementById(pageMap[page] || 'pageWeekly').classList.add('active');",
        "    document.getElementById(pageMap[page] || 'pageWeekly').classList.add('active');\n"
        "    if(fresh) _navReset(page);   // r289", 1, 'switchPage-reset')

    rep("    tab.addEventListener('click', () => switchPage(tab.dataset.page));",
        "    tab.addEventListener('click', () => switchPage(tab.dataset.page, true));", 1, 'tab-click')
    rep("if(ts) ts.addEventListener('click', function(){ switchPage('memo'); });",
        "if(ts) ts.addEventListener('click', function(){ switchPage('memo', true); });", 1, 'tab-sched')
    rep("if(te) te.addEventListener('click', function(){ switchPage('links'); });",
        "if(te) te.addEventListener('click', function(){ switchPage('links', true); });", 1, 'tab-etc')
    rep("if(ta) ta.addEventListener('click', function(){ switchPage('fxsum'); });",
        "if(ta) ta.addEventListener('click', function(){ switchPage('fxsum', true); });", 1, 'tab-acct')

    # 감사 쪽 되돌리기
    rep('  window.asLGo = function(n){',
        '  // r289: 감사 탭을 다시 누르면 [명세표 만들기] 부터 — 올려 둔 파일은 건드리지 않는다\n'
        '  window._asResetView = function(){ _asTab=\'new\'; _asLPage=0; _asLOpen={}; _asLSel={}; };\n'
        '  window.asLGo = function(n){', 1, 'audit-reset')

    # FORBIDDEN / KEEP
    assert '◀ 이전' not in s, 'FORBIDDEN old pager arrow remains'
    assert "window.open('','_blank')" not in s or s.count("window.open('','_blank')") < 1, 'FORBIDDEN asPreview window.open remains'
    assert '올린 자료 가운데 이미 저장된' not in s, 'FORBIDDEN old dup text remains'
    for k in ['_AS_PAGE_NUMS', '_asOpenPreview', '_navReset', 'window._asResetView', 'var _AS_PER = 15;']:
        assert k in s, 'KEEP %s' % k

    if is_test:
        old = '<!-- test build r288 2026-11-26 -->'
        assert s.count(old) == 1, 'test marker r288 not found'
        s = s.replace(old, '<!-- test build r289 2026-11-27 -->')
        N[0] += 1

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(s)
    print('r289 edits applied: %d' % N[0])
    return 0

if __name__ == '__main__':
    sys.exit(main())
