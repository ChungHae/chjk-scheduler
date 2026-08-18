# 작업공간 롤백 복구 가이드 (2026-08-18 갱신)

Claude 클라우드 작업공간은 세션이 쉬는 동안 예전 스냅샷으로 롤백될 수 있다.
사이트·저장소·Firebase·PC 파일은 영향 없음. 아래 절차로 작업 파일만 복구한다.

## 복구 절차
1. `git clone --depth 1 https://github.com/ChungHae/chjk-scheduler.git`
   → 배포본(live: index.html, test: test/index.html)이 곧 최신 기준 상태.
2. 클론한 두 파일을 /mnt/user-data/outputs/index.html, testpage/index.html 로 복사.
3. 배포 이후에 진행 중이던 수정(rNN)이 있으면 automation/rebuild/ 의 edits_rNN.py 를
   번호 순서대로 적용. 각 모듈은 old/new 문자열 count==1 검증을 내장하고 있어
   순서가 틀리면 즉시 실패한다.
4. `git hash-object` 로 기록된 해시와 대조해 바이트 단위 일치 확인.

## 해시 기록 (배포 시점)
- r77: live a62e33a6 / test b0bf625f
- r83: live e22fb633 / test f5c48325  ← 2026-08-18 배포 (현재 배포본)

## 주의
- edits_r62 는 _clxRender~전화포맷터 구간 슬라이스 치환이라 그 사이에 있던
  clxAddrSearch 를 삭제한다 → r62 이후 재구축 시 반드시 r66 을 다시 적용할 것.
- r67~r77 모듈은 롤백으로 유실 (해당 변경분은 배포본에 포함되어 있어 문제 없음).
- 새 rNN 모듈을 만들면 다음 배포 때 automation/rebuild/ 에도 같이 올릴 것.
- test 파일 마커: `<!-- test build rNN 날짜 -->` (test 전용, live 에는 없음)

## 배포 방식
GitHub 웹 업로드(Whale): upload/main (live), upload/main/test (test)
→ 커밋 후 Pages 반영 ~90초 → github.io 에서 fetch 로 서빙 바이트 검증.
