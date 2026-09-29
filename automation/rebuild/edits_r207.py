# -*- coding: utf-8 -*-
# r207(회계): 카드매출 '수집 안 됨' 헛경고 — 판정 시각 09시 → 11시
#  증상: 정상인 날에도 아침에 회계 > 카드매출에 "오늘 카드매출 자료가 아직 수집되지 않았습니다"
#        빨간 경고가 떠 있다.
#  원인: 배너는 평일 09시가 지나면 판정하는데(r109), GitHub Actions 예약 실행이 실제로는
#        08시가 아니라 10시 전후에 시작된다. 예약 지연은 GitHub 무료 러너 쪽 사정이라 제어할 수 없다.
#        실측(카드매출 동기화 최근 14회 시작 시각, KST):
#          09-28 10:25 / 09-25 10:09 / 09-24 10:08 / 09-23 10:15 / 09-22 10:27 / 09-21 09:51 /
#          09-18 10:03 / 09-17 10:05 / 09-16 10:07 / 09-15 10:11 / 09-14 09:46 / 09-11 09:50 /
#          09-10 09:52 / 09-09 10:03      → 가장 늦은 시작이 10:27
#        즉 매일 09:00~10:30 사이에는 정상인데도 경고가 떠 있었다.
#  처리: 판정 기준을 11시로 늦춘다. 가장 늦은 실측 시작(10:27) + 실행시간(약 2~3분) 에도 충분한 여유가 있고,
#        진짜로 수집이 안 된 날은 11시에도 그대로 뜨므로 놓치지 않는다.
#  사용자 지시: "그래 그렇게 바꿔줘 헛경고 없애는게 낫지"
import io, re

def rep(s, old, new, cnt, label):
    n = s.count(old)
    if n != cnt:
        raise SystemExit('[FAIL] %s : expected %d, found %d' % (label, cnt, n))
    return s.replace(old, new)

OLD = """    // r109: 오늘 수집 성공/실패 배너 (평일 09시 이후에만 판정 — 자동 수집은 평일 08시)
    var stEl=document.getElementById('csSyncStatus');
    if(stEl){
      var _now=new Date();
      var _dow=_now.getDay();
      var _checkable=(_dow>=1&&_dow<=5)&&(_now.getHours()>=9);
"""
NEW = """    // r109: 오늘 수집 성공/실패 배너 (평일에만 판정)
    // r207: 판정 시각을 09시 → 11시로 늦춘다.
    //  예약은 08시지만 GitHub Actions 예약 실행이 실제로는 10시 전후에 시작한다
    //  (최근 14회 실측 09:46~10:27). 그래서 정상인 날에도 아침내내 빨간 경고가 떴 있었다.
    //  진짜로 안 된 날은 11시에도 그대로 뜨므로 놓치지 않는다.
    var stEl=document.getElementById('csSyncStatus');
    if(stEl){
      var _now=new Date();
      var _dow=_now.getDay();
      var _checkable=(_dow>=1&&_dow<=5)&&(_now.getHours()>=11);   // r207
"""

def apply(path, is_test):
    s = io.open(path, encoding='utf-8').read()
    s = rep(s, OLD, NEW, 1, 'r207 판정시각 (%s)' % path)
    if is_test:
        s2 = re.sub(r'<!-- test build r\d+ [^>]*-->', '<!-- test build r207 2026-09-29 -->', s, count=1)
        if s2 == s: raise SystemExit('[FAIL] test marker not bumped')
        s = s2
    io.open(path, 'w', encoding='utf-8').write(s)
    print('[ok]', path)

apply('/mnt/user-data/outputs/index.html', False)
apply('/mnt/user-data/outputs/testpage/index.html', True)
