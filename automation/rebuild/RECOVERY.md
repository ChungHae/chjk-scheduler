# 작업공간 롤백 복구 가이드 (2026-08-19 갱신)

Claude 클라우드 작업공간은 세션이 쉬는 동안 예전 스냅샷으로 롤백될 수 있다.
사이트·저장소·Firebase·PC 파일은 영향 없음. 아래 절차로 작업 파일만 복구한다.

## 복구 절차
1. `git clone --depth 1 https://github.com/ChungHae/chjk-scheduler.git`
   → 배포본(live: index.html, test: test/index.html)이 곧 기준 상태.
2. 클론한 두 파일을 /mnt/user-data/outputs/index.html, testpage/index.html 로 복사.
3. 배포본 이후 진행된 수정(rNN)은 automation/rebuild/ 의 edits_rNN.py 를
   번호 순서대로 적용 (90b, 95b 같은 보조 모듈은 해당 번호 바로 뒤).
   각 모듈은 old/new 문자열 count==1 검증을 내장 — 순서가 틀리면 즉시 실패한다.
4. `git hash-object` 로 아래 해시와 대조해 바이트 단위 일치 확인.

## 해시 기록
- r77: live a62e33a6 / test b0bf625f (배포됨)
- r83: live e22fb633 / test f5c48325 (2026-08-18 배포)
- r97: live 95ce02e6 / test 3e01e5f4
- r98: live e82bc173 / test ded12fb7
- r99: live 92a73def / test 1afd85c1
- r100: live 18a86cff / test a4552fec
- r101: live 72707e31 / test 52adc8a6
- r102: live a78d8122 / test d3a49c3b
- r103: live 432b532c / test 6b1904e6
- r104: live 3f7c81e5 / test dd5b7621
- r105: live 7f2a9845 / test 9459125b
- r106: live 041617f1 / test a233ec1e
  ※ r106 = 일정 등록 기능 숨김 1단계. TEST 확인 후 완전 삭제(2단계) 예정.
- r107: live eed7d41f / test f892eb7f
- r108: live d1c46bd4 / test 4996c022
- r109: live 4900cfc0 / test dd280329
- r110: live bb85a24d / test c5d2ae8e
- r111: live 77ba5419 / test d418ceb5
- r112: live 4e0199ff / test 5c4c3320
- r113: live 5740329b / test d994b68b
- r114: live 12776761 / test 9409c4e3
- r115: live 6eac5a3b / test dbe1d176
- r116: live 18819c2e / test 7a07884c (전체 백업: automation/rebuild/backup_r116/)
- r117: live 676658ef / test 907bd19d (일정 삭제 1단계: 팀원 일정·업무 배정·팀 목표/이슈)
- r118: live 9a1109d6 / test a900452f (일정 삭제 2단계: 등록 모달·개인 목록·메모/미완료)
- r119: live a96318e7 / test 6a258fa4 (일정 삭제 3단계: 업체별 일정·분류 설정·달력 잔재)
  (미배포)
- r120: live 6eca11a7 / test f0382e16 (프로젝트 숨김 기능)
- r121: live 879fe9e8 / test b314aa2f (2026-08-21 배포, 현재 배포본)
- r122: live b3ad590e / test 4ee1a3f1 (매입매출 탭 골격)
- r123: live 4f2cec1d / test d97c65ff (누적본 이관 + _fx 블롭 분리 저장)
- r124: live 7c573131 / test db221743 (2026-08-21 작업본, PC test 파일 = r124, 미배포 — 미수 현황 원장 화면)
  ※ r117~r119 는 마커 기반 슬라이스 삭제 모듈 — r116 이후 순서대로 적용.
    복구 지름길: backup_r116/ 파일 복사 후 117→118→119 재생.
    데이터 선언·동기화 키(assignments/comments/categories/issues/team_goal 등)는
    데이터 보호·구버전 호환 위해 코드에 유지됨.

## 주의
- edits_r62 는 _clxRender~전화포맷터 구간 슬라이스 치환이라 그 사이에 있던
  clxAddrSearch 를 삭제한다 → r62 이후 재구축 시 반드시 r66 을 다시 적용할 것.
- r67~r77 모듈은 유실 (해당 변경분은 배포본 r83에 포함되어 있어 문제 없음).
- 새 rNN 모듈을 만들면 즉시(배포를 기다리지 말고) automation/rebuild/ 에 올릴 것.
- test 파일 마커: `<!-- test build rNN 날짜 -->` (test 전용, live 에는 없음)
- 디자인 규칙: 공통 동작 버튼은 표준 아이콘(수정=연필 #5b7ba6, 삭제=휴지통 #dc2626,
  툴바 추가=+ qic)으로 통일. 임의 아이콘 금지. (r84에서 규칙화)

## 배포 방식
GitHub 웹 업로드(Whale): upload/main (live), upload/main/test (test)
→ 커밋 후 Pages 반영 ~90초 → github.io 에서 fetch 로 서빙 바이트 검증.
GitHub 커넥터는 읽기 전용(쓰기 403, Anthropic 측 알려진 제한).

## 인수인계
- 전체 프로젝트 인수인계 문서: HANDOVER.md (환경·규칙·이력·매입매출 신규 시스템 스펙 전부).
  새 세션은 HANDOVER.md 를 먼저 읽을 것.
