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
- r83: live e22fb633 / test f5c48325 (2026-08-18 배포, 현재 배포본)
- r97: live 95ce02e6 / test 3e01e5f4
- r98: live e82bc173 / test ded12fb7
- r99: live 92a73def / test 1afd85c1
- r100: live 18a86cff / test a4552fec
- r101: live 72707e31 / test 52adc8a6
- r102: live a78d8122 / test d3a49c3b
- r103: live 432b532c / test 6b1904e6
- r104: live 3f7c81e5 / test dd5b7621
- r105: live 7f2a9845 / test 9459125b (2026-08-20 작업본, PC test 파일 = r105, 미배포)

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
