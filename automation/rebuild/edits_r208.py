# -*- coding: utf-8 -*-
# r208(업체): 일정 > 업체 검색을 상세정보 전체로 확장
#  종전에는 업체명과 사업자번호(숫자)만 검색됐다.
#  사용자 요청: "검색창 입력시에 대표자 이름이나 주소, 전화번호, 메일, 팩스 번호 등을 입력해도 검색이 가능하게"
#  처리:
#   (1) _clxMatch(c,q,qd) 추가 — 업체명·사업자번호에 더해
#       종사업장번호 / 지점 / 대표자 / 주소(우편번호·주소·상세주소) / 업태 / 종목 /
#       계산서메일 / 대표전화 / FAX / 은행 / 계좌번호 / 예금주 / 메모 /
#       담당자(부서·직급·이름·전화·휴대전화·이메일) 까지 본다.
#       전화·팩스·계좌·우편번호처럼 숫자로 찾는 칸은 하이픈을 떼고 비교한다(숫자 2자리 이상일 때만).
#   (2) 목록에 없는 칸(계산서메일·업태·종목·은행·계좌·예금주·메모·담당자)에서 걸린 경우
#       업체명 아래에 '어디서 걸렸는지'를 작은 글씨로 보여준다.
#       (대표자·주소·전화·FAX 는 이미 표에 열이 있어 따로 표시하지 않는다)
#   (3) 검색창 안내문구를 '업체명/사업자번호 검색…' → '업체명·대표자·주소·전화·메일 검색…' 으로 바꾼다.
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

# ── (1) 검색 대상 확장 + 어디서 걸렸는지 라벨 ─────────────────────────
OLD1 = """    var q=_clxQ, qd=q.replace(/\\D/g,'');
    var list=all.filter(function(c){
      if(_clxExp!==null && _clxExp!=='' && _cliKey(c)===_clxExp) return true;   // 펼친 업체는 항상 표시
      if(!q) return true;
      if(String(c[0]).toLowerCase().indexOf(q)>=0) return true;
      if(qd && String(c[1]||'').replace(/\\D/g,'').indexOf(qd)>=0) return true;
      return false;
    });
"""
NEW1 = """    var q=_clxQ, qd=q.replace(/\\D/g,'');
    // r208: 상세정보 전체로 검색 확대. 히트가 난 칸의 라벨을 _clxHit 에 남긴다.
    var _clxHit={};
    var list=all.filter(function(c){
      if(_clxExp!==null && _clxExp!=='' && _cliKey(c)===_clxExp) return true;   // 펼친 업체는 항상 표시
      if(!q) return true;
      var h=_clxMatch(c, q, qd);
      if(h===null) return false;
      if(h) _clxHit[_cliKey(c)]=h;
      return true;
    });
"""

# ── (2) _clxMatch 정의 (_clxInfo 바로 뒤에 넣는다) ───────────────────
OLD2 = """  function _clxInfoKey(nm, br){
"""
NEW2 = """  // r208: 업체 검색 — 상세정보 칸까지 전부 본다.
  //  반환값: null = 안 걸림 / '' = 목록에 보이는 칸에서 걸림 / '라벨' = 안 보이는 칸에서 걸림
  function _clxMatch(c, q, qd){
    var has=function(v){ return String(v==null?'':v).toLowerCase().indexOf(q)>=0; };
    //  전화·팩스·계좌처럼 숫자로 찾는 칸은 하이픈을 떼고 비교(2자리 이상일 때만)
    var dig=function(v){ return (qd.length>=2) && String(v==null?'':v).replace(/\\D/g,'').indexOf(qd)>=0; };
    if(has(c[0])) return '';
    if(qd && String(c[1]||'').replace(/\\D/g,'').indexOf(qd)>=0) return '';
    var inf=_clxInfo(c)||{};
    if(has(inf.ceo)) return '';
    if(has(inf.addr) || has(inf.addr2) || has(inf.zip) || dig(inf.zip)) return '';
    if(has(inf.tel) || dig(inf.tel)) return '';
    if(has(inf.fax) || dig(inf.fax)) return '';
    var _sb=_cliSb(c);
    if(has(_sb) || dig(_sb)) return '종사업장번호 '+_sb;
    if(has(inf.taxEmail)) return '계산서메일 '+inf.taxEmail;
    if(has(inf.uptae)) return '업태 '+inf.uptae;
    if(has(inf.jongmok)) return '종목 '+inf.jongmok;
    if(has(inf.bank)) return '은행 '+inf.bank;
    if(has(inf.account) || dig(inf.account)) return '계좌 '+inf.account;
    if(has(inf.holder)) return '예금주 '+inf.holder;
    var cts=(inf.contacts&&inf.contacts.length)?inf.contacts:[];
    for(var i=0;i<cts.length;i++){
      var t=cts[i]||{};
      if(has(t.name) || has(t.dept) || has(t.rank)
         || has(t.phone) || dig(t.phone) || has(t.phone2) || dig(t.phone2) || has(t.email)){
        var _nm=[t.dept,t.rank,t.name].filter(Boolean).join(' ');
        var _co=[t.phone,t.phone2,t.email].filter(Boolean).join(' / ');
        return '담당자 '+(_nm||'')+(_co?(' · '+_co):'');
      }
    }
    if(has(inf.memo)){
      var _m=String(inf.memo||'').replace(/\\s+/g,' ');
      var _at=_m.toLowerCase().indexOf(q);
      var _st=Math.max(0, _at-20);
      return '메모 '+(_st?'…':'')+_m.slice(_st, _st+70)+((_st+70)<_m.length?'…':'');
    }
    return null;
  }
  function _clxInfoKey(nm, br){
"""

# ── (3) 업체명 아래에 히트 라벨 ───────────────────────────────────
OLD3 = """            + '<td style="'+TD+';font-weight:700;color:#14305c" title="'+esc(nm)+'">'+esc(nm)+'</td>'
"""
NEW3 = """            + '<td style="'+TD+';font-weight:700;color:#14305c" title="'+esc(nm)+'">'+esc(nm)
            +   ((_clxHit[_key])   // r208: 목록에 없는 칸에서 걸렸으면 어디서 걸렸는지 보여준다
                  ? ('<div style="font-weight:400;font-size:11px;color:#8a94a6;overflow:hidden;text-overflow:ellipsis" title="'+esc(_clxHit[_key])+'">'+esc(_clxHit[_key])+'</div>')
                  : '')
            + '</td>'
"""

# ── (4) 검색창 안내문구 ──────────────────────────────────────────
OLD4 = 'placeholder="업체명/사업자번호 검색…"'
NEW4 = 'placeholder="업체명·대표자·주소·전화·메일 검색…"'

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD1, NEW1, 1, 'r208 필터 (%s)' % path)
    s = rep(s, OLD2, NEW2, 1, 'r208 _clxMatch (%s)' % path)
    s = rep(s, OLD3, NEW3, 1, 'r208 히트 라벨 (%s)' % path)
    s = rep(s, OLD4, NEW4, 1, 'r208 placeholder (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r208 2026-09-29 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
