# -*- coding: utf-8 -*-
# r230 (사용자 요청 2026-10-14): 회계 > 자료 업로드 맨 위에 **적재 현황 표**.
#   "각 은행과 매출·매입 계산서의 최신 업로드 날짜를 따로 보고 싶다 — 언제부터 올려야 할지 알기 어렵다."
#   사용자 결정: ① 자료의 **마지막 거래일** 기준(올린 시각이 아니라) ② 서울·화성 나눠서 ③ 자료 업로드 탭 맨 위 표.
#   적재된 자료에서 바로 계산하므로 기존 자료도 당장 보인다. 업로드가 끝나면 _fxMetaRefresh() 를 타고 자동 갱신.
import io, sys

FUNC = r"""  // r230: 자료 업로드 탭 맨 위 '적재 현황' — 원천별(계산서·은행·어음) × 사업장별 마지막 거래일
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
    slot('1A','매출 계산서','계산서'); slot('1B','매입 계산서','계산서');   // 매출 먼저
    (fxSalesInv||[]).forEach(function(e){ put('1A','매출 계산서','계산서', e.biz, e.date); });
    (fxPurchInv||[]).forEach(function(e){ put('1B','매입 계산서','계산서', e.biz, e.date); });
    (fxDeposits||[]).forEach(function(e){
      var isNote=(e.kind==='note');
      var nm=e.bank||(isNote?'어음':'기타');
      put((isNote?'3':'2')+nm, nm, isNote?'어음':'은행 입금', e.biz, e.date);
    });
    rows.sort(function(a,b){ return a.key<b.key?-1:(a.key>b.key?1:0); });
    var today=new Date(); today.setHours(12,0,0,0);
    function cell(s){
      if(!s.d) return '<span style="color:#cfd6e0">—</span>';
      var dt=new Date(s.d+'T12:00:00');
      var ago=Math.round((today-dt)/86400000);
      var col=(ago>45)?'#dc2626':'#8a94a6';
      return '<span style="font-weight:700;color:#14305c">'+s.d+'</span>'
        + '<span style="font-size:11px;color:'+col+';margin-left:6px">'+(ago<=0?'오늘':(ago+'일 전'))+'</span>'
        + '<div style="font-size:11px;color:#9ca3af;margin-top:2px">'+_fxFmt(s.n)+'건</div>';
    }
    var TH='padding:8px 10px;background:#fafafa;color:#888;font-weight:500;font-size:11.5px;text-align:center;border-bottom:2px solid #d3dce6;border-right:1px solid #e3e9f0;white-space:nowrap';
    var TD='padding:8px 10px;border-bottom:1px solid #eef2f7;border-right:1px solid #eef2f7;font-size:12.5px;text-align:center;vertical-align:top';
    var body='', lastGrp='';
    rows.forEach(function(r){
      if(r.grp!==lastGrp){
        lastGrp=r.grp;
        body += '<tr><td colspan="3" style="padding:6px 10px;background:#f4f8fe;border-bottom:1px solid #e3e9f0;font-size:11.5px;font-weight:700;color:#1B3A6B">'+r.grp+'</td></tr>';
      }
      body += '<tr>'
        + '<td style="'+TD+';text-align:left;font-weight:700;color:#14305c">'+esc(r.label)+'</td>'
        + '<td style="'+TD+'">'+cell(r.c['서울'])+'</td>'
        + '<td style="'+TD+'">'+cell(r.c['화성'])+'</td>'
        + '</tr>';
    });
    host.innerHTML =
      '<div style="background:#fff;border:1px solid #d6deea;padding:14px 16px;margin-bottom:12px">'
      + '<div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin-bottom:10px">'
      +   '<span style="font-size:13px;font-weight:700;color:#14305c">적재 현황</span>'
      +   '<span style="font-size:11.5px;color:#8a94a6">자료가 들어 있는 <b>마지막 거래일</b> — 이 날짜 다음부터 올리면 됩니다 (겹쳐 올려도 중복은 자동으로 걸러집니다)</span>'
      + '</div>'
      + '<div style="overflow:auto"><table style="width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;min-width:420px">'
      + '<colgroup><col><col style="width:36%"><col style="width:36%"></colgroup>'
      + '<thead><tr><th style="'+TH+'">구분</th><th style="'+TH+'">서울</th><th style="'+TH+'">화성</th></tr></thead>'
      + '<tbody>'+body+'</tbody></table></div>'
      + '</div>';
  }
"""

OPS = [
 # ① 적재 현황 자리 + 함수 삽입
 ["  function _fxMetaRefresh(){\n"
  "    var meta=document.getElementById('fxMeta');\n"
  "    if(meta) meta.textContent='매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건';\n"
  "  }\n",
  FUNC
  + "  function _fxMetaRefresh(){\n"
    "    var meta=document.getElementById('fxMeta');\n"
    "    if(meta) meta.textContent='매출 '+fxSalesInv.length+'건 · 매입 '+fxPurchInv.length+'건 · 입금 '+fxDeposits.length+'건';\n"
    "    try{ _fxUpStat(); }catch(_e){}   // r230: 업로드가 끝나면 적재 현황도 같이 갱신\n"
    "  }\n",
  1, "FUNC"],
 # ② 자료 업로드 탭 맨 위에 자리 잡기
 ["    body.innerHTML =\n"
  "      '<div style=\"display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px\">'\n"
  "      + _upCard('홈택스 세금계산서',",
  "    body.innerHTML =\n"
  "      '<div id=\"fxUpStat\"></div>'   // r230: 적재 현황 (자료가 로드된 뒤 채움)\n"
  "      + '<div style=\"display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px\">'\n"
  "      + _upCard('홈택스 세금계산서',",
  1, "SLOT"],
 # ③ 자료 로드 후 그리기
 ["    _fxEnsureData().then(function(){\n"
  "      if(_fxTab!=='up') return;\n"
  "      _fxMetaRefresh();\n"
  "      _fxRenderUnasg();\n"
  "    });",
  "    _fxEnsureData().then(function(){\n"
  "      if(_fxTab!=='up') return;\n"
  "      _fxMetaRefresh();   // r230: 안에서 _fxUpStat() 도 그린다\n"
  "      _fxRenderUnasg();\n"
  "    });",
  1, "DRAW"],
]

MARKER = ["<!-- test build r229 2026-10-13 -->", "<!-- test build r230 2026-10-14 -->"]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R230 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def apply_r230(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    for w in ['_fxUpStat', 'fxUpStat', '적재 현황']:
        if w not in s: raise SystemExit('R230 FAIL %s 가 없음' % w)
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r230(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r230 applied:', path)
