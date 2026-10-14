# -*- coding: utf-8 -*-
# r231 (사용자 요청 2026-10-14): r230 의 '적재 현황' 표가 화면을 너무 차지한다 → **칩 세 줄**로 간소화.
#   · 큰 표(13행) → 원천당 칩 하나, 칩 안에 서울·화성 날짜를 같이. 계산서 / 입금 / 어음 세 줄.
#   · 날짜는 MM-DD (올해가 아니면 앞에 'YY). 건수·"N일 전"·전체 날짜는 칩 title(마우스 올리면)로.
#   · 45일 넘게 멈춘 곳만 빨간색 — 밀린 데를 바로 찾는 게 목적.
import io, sys

NEW = r"""  // r230→r231: 자료 업로드 맨 위 '적재 현황' — 원천별 × 사업장별 마지막 거래일 (칩 세 줄, 최소 높이)
  function _fxUpStat(){
    var host=document.getElementById('fxUpStat'); if(!host) return;
    var BZ=['서울','화성'], rows=[], idx={};
    function slot(key, label, grp){
      if(!idx[key]){ idx[key]={key:key, label:label, grp:grp, c:{'서울':{d:'',n:0}, '화성':{d:'',n:0}}}; rows.push(idx[key]); }
      return idx[key];
    }
    function put(key, label, grp, biz, date){
      if(BZ.indexOf(biz)<0) return;
      var s=slot(key, label, grp).c[biz];
      s.n++; if(date && date>s.d) s.d=date;
    }
    slot('1A','매출','계산서'); slot('1B','매입','계산서');
    (fxSalesInv||[]).forEach(function(e){ put('1A','매출','계산서', e.biz, e.date); });
    (fxPurchInv||[]).forEach(function(e){ put('1B','매입','계산서', e.biz, e.date); });
    (fxDeposits||[]).forEach(function(e){
      var isNote=(e.kind==='note');
      var nm=e.bank||(isNote?'어음':'기타');
      put((isNote?'3':'2')+nm, nm, isNote?'어음':'입금', e.biz, e.date);
    });
    rows.sort(function(a,b){ return a.key<b.key?-1:(a.key>b.key?1:0); });
    var today=new Date(); today.setHours(12,0,0,0);
    var thisY=String(today.getFullYear());
    function agoOf(d){ return Math.round((today-new Date(d+'T12:00:00'))/86400000); }
    function shortD(d){ var y=d.slice(0,4); return (y===thisY?'':("'"+y.slice(2)+" "))+d.slice(5).replace('-','-'); }
    function part(r, biz){
      var s=r.c[biz];
      if(!s.d) return '';
      var ago=agoOf(s.d), old=(ago>45);
      return '<span title="'+esc(r.label)+' · '+biz+' — '+s.d+' · '+(ago<=0?'오늘':(ago+'일 전'))+' · '+_fxFmt(s.n)+'건" style="margin-left:6px;white-space:nowrap">'
        + '<span style="color:#9ca3af">'+biz.slice(0,2)+'</span> '
        + '<span style="color:'+(old?'#dc2626':'#14305c')+';font-weight:'+(old?'700':'600')+'">'+shortD(s.d)+'</span>'
        + '</span>';
    }
    function chip(r){
      var p=part(r,'서울')+part(r,'화성');
      if(!p) return '';
      return '<span style="display:inline-flex;align-items:baseline;border:1px solid #e3e9f0;background:#fff;padding:2px 8px;margin:0 4px 4px 0;font-size:11.5px;line-height:1.5">'
        + '<b style="color:#14305c">'+esc(r.label)+'</b>'+p+'</span>';
    }
    var GRP=['계산서','입금','어음'], line='';
    GRP.forEach(function(g){
      var html=rows.filter(function(r){ return r.grp===g; }).map(chip).join('');
      if(!html) return;
      line += '<div style="display:flex;align-items:flex-start;gap:6px;margin-top:3px">'
        + '<span style="flex:0 0 42px;font-size:11px;color:#8a94a6;padding-top:4px">'+g+'</span>'
        + '<span style="flex:1;min-width:0">'+html+'</span></div>';
    });
    host.innerHTML =
      '<div style="border:1px solid #d6deea;background:#fbfcfe;padding:7px 10px 4px;margin-bottom:10px">'
      + '<div style="font-size:11px;color:#8a94a6">적재 현황 · 자료가 들어 있는 <b style="color:#14305c">마지막 거래일</b> — 다음 날짜부터 올리면 됩니다 (겹쳐도 중복은 자동 제외)</div>'
      + line
      + '</div>';
  }
"""

START = "  // r230: 자료 업로드 탭 맨 위 '적재 현황' — 원천별(계산서·은행·어음) × 사업장별 마지막 거래일\n"
END = "  function _fxMetaRefresh(){\n"

MARKER = ["<!-- test build r230 2026-10-14 -->", "<!-- test build r231 2026-10-14 -->"]


def splice(s, a, b, new, label):
    if s.count(a) != 1: raise SystemExit('R231 FAIL %s startAnchor %d' % (label, s.count(a)))
    if s.count(b) != 1: raise SystemExit('R231 FAIL %s endAnchor %d' % (label, s.count(b)))
    i = s.index(a); j = s.index(b, i)
    if j < i: raise SystemExit('R231 FAIL %s order' % label)
    return s[:i] + new + s[j:]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R231 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def apply_r231(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    s = splice(s, START, END, NEW, 'RENDER')
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    if '<table' in s[s.index('function _fxUpStat'):s.index('function _fxMetaRefresh')]:
        raise SystemExit('R231 FAIL 표가 아직 남아 있음')
    for w in ['_fxUpStat', 'fxUpStat', '적재 현황']:
        if w not in s: raise SystemExit('R231 FAIL %s 가 없음' % w)
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r231(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r231 applied:', path)
