# -*- coding: utf-8 -*-
# r168: 카드매출 수집 상태 배너가 "옛 자료"로 잘못 판정되던 문제 + 진단 정보 표시
#
#  증상(사용자 보고 2026-08-26): 본페이지 카드매출에서
#  "오늘 카드매출 자료가 아직 수집되지 않았습니다: 서울, 화성" 이 뜬다.
#  그런데 그날 08:24 자동 실행에서 서울(머니온)은 3건을 정상 기록했다
#  (Actions 로그 확인) → 서울까지 미수집으로 나올 이유가 없다.
#
#  원인: _csLoadAllData(force) 가 첫 줄에서
#      if(_csCache && !force) return;
#  로 빠지는데, force=true 로 부르는 곳이 한 군데도 없고 _csCache 를 다시
#  null 로 되돌리는 곳도 없다. 즉 카드매출 자료와 _meta(마지막 동기화 시각)는
#  "페이지를 새로 연 그 순간" 한 번만 읽고 그 뒤로는 절대 갱신되지 않는다.
#  브라우저를 아침 동기화(08시) 전에 열어 두었거나 탭을 계속 켜 두면
#  _csMetaCache 는 어제 값 그대로라 배너가 종일 빨갛게 남는다.
#
#  수정:
#   (1) _csLoadMeta(): _meta 두 개만 다시 읽는 가벼운 함수(거래 자료는 건드리지 않음).
#       renderCardSalesPage 가 카드매출 화면에 들어올 때마다 호출한다.
#       → 탭을 계속 켜 둔 채로도 화면을 다시 열면 최신 상태로 판정된다.
#   (2) 거래 자료도 오래되면 다시 읽는다: 마지막으로 읽은 시각이 10분보다
#       오래됐으면 _csLoadAllData(true) 로 통째 갱신(자주 부르지 않게 시간 제한).
#   (3) 빨간 배너에 지점별 "마지막 동기화" 시각을 함께 보여준다.
#       (기록 없음/며칠 전인지가 바로 보여야 원인을 헷갈리지 않는다)

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R168 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r168(s, path):
    # (1) 마지막 로드 시각 기록용 변수
    s = rep(s,
        "  let _csCache = null;\n  let _csMetaCache = null;",
        "  let _csCache = null;\n  let _csMetaCache = null;\n"
        "  let _csLoadedAt = 0;        // r168: 거래 자료를 마지막으로 읽은 시각(ms)\n"
        "  const _CS_STALE_MS = 10*60*1000;   // 10분 지나면 화면 진입 시 다시 읽는다",
        1, 'CSVARS168')

    # (2) 로드 시각 기록 + _meta 단독 갱신 함수
    s = rep(s,
        "  async function _csLoadAllData(force){\n    if(_csCache && !force) return;",
        "  // r168: _meta(마지막 동기화 시각)만 가볍게 다시 읽는다.\n"
        "  //  거래 자료는 그대로 두고 판정 근거만 최신화하므로 화면 진입 때마다 불러도 부담이 없다.\n"
        "  async function _csLoadMeta(){\n"
        "    if(!_fbDbUrl) return;\n"
        "    var branches=['seoul','hwaseong'];\n"
        "    var metas = await Promise.all(branches.map(function(b){\n"
        "      return _fbFetch(`${_fbDbUrl}/teamdata_test_cardsales/_meta/${b}.json`).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; });\n"
        "    }));\n"
        "    if(!_csMetaCache) _csMetaCache={};\n"
        "    branches.forEach(function(b,i){ if(metas[i]!==null || _csMetaCache[b]===undefined) _csMetaCache[b]=metas[i]; });\n"
        "  }\n\n"
        "  async function _csLoadAllData(force){\n    if(_csCache && !force) return;",
        1, 'CSLOADMETA')

    s = rep(s,
        "    _csCache={}; _csMetaCache={};\n    branches.forEach(function(b,i){",
        "    _csCache={}; _csMetaCache={}; _csLoadedAt=Date.now();\n    branches.forEach(function(b,i){",
        1, 'CSLOADEDAT')

    # (3) 화면 진입 때마다 최신 상태로 판정
    s = rep(s,
        """    try{
      await _csLoadAllData();
      if(_csMonth===undefined){ _csPickInitialSelection(); }
      _csRenderAll();""",
        """    try{
      // r168: 자료가 오래됐으면 통째로 다시 읽고, 아니면 _meta 만 갱신한다.
      //  (예전에는 페이지를 처음 연 순간 한 번만 읽어서, 탭을 켜 둔 채 아침 동기화가
      //   끝나도 "오늘 미수집" 빨간 배너가 종일 남아 있었다)
      var _stale = (!_csCache) || (Date.now() - _csLoadedAt > _CS_STALE_MS);
      await _csLoadAllData(_stale);
      if(!_stale) await _csLoadMeta();
      if(_csMonth===undefined){ _csPickInitialSelection(); }
      _csRenderAll();""",
        1, 'CSRENDERENTRY')

    # (4) 빨간 배너에 지점별 마지막 동기화 시각 표시
    s = rep(s,
        """        var _t0=new Date(_now.getFullYear(),_now.getMonth(),_now.getDate());
        var _bad=[], _ok=[];
        ['seoul','hwaseong'].forEach(function(b){
          var mt=_csMetaCache[b];
          var d=(mt&&mt.lastSyncedAt)?new Date(mt.lastSyncedAt):null;
          if(d&&!isNaN(d.getTime())&&d>=_t0) _ok.push(_CS_BRANCH_LABEL[b]);
          else _bad.push(_CS_BRANCH_LABEL[b]);
        });""",
        """        var _t0=new Date(_now.getFullYear(),_now.getMonth(),_now.getDate());
        var _bad=[], _ok=[];
        // r168: 안 된 지점은 "마지막으로 언제 됐는지"를 같이 보여준다(원인 판단이 쉬워짐)
        var _p2=function(n){ return (n<10?'0':'')+n; };
        ['seoul','hwaseong'].forEach(function(b){
          var mt=_csMetaCache[b];
          var d=(mt&&mt.lastSyncedAt)?new Date(mt.lastSyncedAt):null;
          if(d&&!isNaN(d.getTime())&&d>=_t0) _ok.push(_CS_BRANCH_LABEL[b]);
          else{
            var _when = (d&&!isNaN(d.getTime()))
              ? (_p2(d.getMonth()+1)+'-'+_p2(d.getDate())+' '+_p2(d.getHours())+':'+_p2(d.getMinutes()))
              : '기록 없음';
            _bad.push(_CS_BRANCH_LABEL[b]+'(마지막 '+_when+')');
          }
        });""",
        1, 'CSBADWHEN')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r168(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r167 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r167 2026-08-26 -->', '<!-- test build r168 2026-08-26 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
