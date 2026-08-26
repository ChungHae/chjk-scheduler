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
- r124: live 7c573131 / test db221743 (미수 현황 원장 화면)
- r125: live b89b332c / test fc67dec3 (매입·매출 집계 화면)
- r126: live 0bc35768 / test b8d0bbbe (업로드 파서: 홈택스/은행6종/어음3종 + 미배정 입금 패널)
- r127: live d06379e6 / test e0af815f (원장/미수현황/집계 엑셀 + 기초이월 병합 수정)
- r128: live 718f1b9c / test 91435a15 (디자인 통일: sub-nav 스트립·inv-toolbar·qic + 원장 차변/대변)
- r129: live 2a8c392b / test 8e540813 (전체 필터·표 전체폭·기간조회·연령분석·어음 만기)
- r130: live 93ada619 / test 7f307cae (거래 자료 초기화 + N|이름 슬롯 병합 보강)
- r131: live 2d0e5580 / test 61876369 (초기화 '별칭만 유지' + 규칙 편집 UI + 원장 엑셀 키 수정)
- r132: live f19b29f9 / test c8268819 (미배정 선택창 앱 공통 드롭다운)
- r133: live 8ebea432 / test de2ad23d (미배정 매칭 업체목록 기준 + 별칭표 관리)
- r134: live bd6f4371 / test 9593245b (규칙 5종 동기화 KEYS 버그픽스 + 복사 시 규칙 리셋 + 별칭 전체 삭제)
- r135: live a19c2311 / test 84f8c6e6 (드롭다운 '계산서에만 있는 거래처' 섹션 + 원클릭 업체 등록·배정)
- r136: live b5623185 / test 878237b6 (드롭다운 각진 모서리)
- r137: live bdc6c832 / test abf3e127 (미배정 보류(건너뛰기) + 보류 목록 재확인 흐름)
- r138: live 262bf96c / test cb2c00a2 (드롭다운 UX: 빈 검색 시 두 섹션 항상 표시)
- r139: live fef97103 / test 964273a3 (드롭다운 자가진단: 기등록 안내·타사업장 경고)
- r140: live 406c84c2 / test b2047fbc (원장 입금 건별 재배정(연필))
- r141: live 0234e626 / test 6a253ecf (교차 입금 사업장 이동 배정)
- r142: live 36b675c6 / test de8e2c46 (사명 변경+교차 입금: 동일 사업자번호 타사업장 직접 배정)
- r143: live affa17f0 / test d8f039de (카드·결제 정산 자동 제외: 카드/결+숫자, 업로드 시 + 소급 버튼)
- r144: live 15f2e7fb / test 80d90119 (자동 제외 판정 확장: 카드사명 접두+숫자4↑)
- r145: live 68c5b4e6 / test 491ae2a2 (대표자명 자동 배정 + [자동 배정 재실행] 버튼)
- r146: live c4174099 / test 704159f6 (거래처 중복 원장 버그 수정 + 중복 거래처 후보 진단·병합 도구)
- r147: live b68f46f7 / test 5c47890a (채권 연령 계산 버그 수정: 마이너스 계산서/음수 기초이월을 변제로 처리)
- r148: live e3c1e163 / test c041844b (미수현황 표 전체폭 확장 + 업체 목록 페이지네이션 교체)
- r149: live 905803bf / test 0490fd2d (업체 목록 렌더링 정지 버그 수정: allClients 손상 항목 방어)
- r150: live 19fe1cb7 / test 56566e28 (2026-08-25 — 미수현황 페이지네이션 1페이지 20개, 요약 칩은 전체 기준 유지)
- r151: live a9c50d36 / test 70ae1f35 (2026-08-26 — 매입매출 계산 속도 개선. 수치·판정 로직 불변(1,653행 대조 일치). 원장 캐시(_fxDataStamp=_fxCacheBump+배열길이; _fxSave/_fxSaveBig/_fxEnsureData/외부동기화 4곳에서 ++), _fxDupCandidates O(n²)→O(n), _fxLedgersOne 기초이월·N|병합 이름인덱스화(Object.create(null)), _fxDue 메모이제이션, 검색창 180ms 디바운스, fxArXls slice(). 첫 진입 365→28ms, 검색 344→2ms, 5글자 타이핑 1,829→0ms)
- r152: live 2895d3db / test db46801a (2026-08-26 작업본, PC test 파일 = r152, 미배포 — 매입매출 첫 진입 로딩 단축. r151 이 계산을 줄였다면 r152 는 자료 받아오는 시간을 줄임. (A) _fxEnsureData 가 블롭 6개를 for+await 로 순차 요청하던 것을 Promise.all 동시 요청으로 변경 — 왕복지연(RTT)이 6번 쌓이던 것이 1번으로. 응답 순서와 무관하게 ks 순서로 다시 담아 결과·순서 완전 동일(검증 완료). 동시호출 안전성: _fbFetch 는 호출마다 독립이고 _fxSaveBig 가 이미 _fxBlobPut 6개를 동시 발사 중. (B) _fxBlobGet 이 받은 자료를 캐시용으로 통째 JSON.parse(JSON.stringify()) 하던 깊은복사 제거(약 50ms) — 이 캐시는 _fxEnsureData(force) 에서만 읽히는데 force 가 해당 키를 먼저 delete 하므로 참조 보관으로 충분. 자료 규모 실측: 블롭 6개 합계 6.3MB(sales_서울 1,478KB 최대), JSON 파싱 13ms/깊은복사 50ms/concat 0ms → CPU 아닌 네트워크가 지배. 대역폭 공유 반영 시뮬: RTT120/100Mbps 1,373→689ms, RTT250/25Mbps 3,775→2,406ms, RTT400/10Mbps 7,893→5,814ms. 남은 시간은 6.3MB 전송 자체(세션당 1회). 더 줄이려면 매입(purch, 2.05MB=32%) 블롭을 집계 탭 진입 시로 미루는 방법이 있으나 AR 툴바 _fxMetaRefresh 의 "매입 N건" 표시·집계탭·엑셀 3곳을 함께 손봐야 해 미적용)
- r153: live 9ae0e2da / test adcecee8 (2026-08-26 — 거래처 검색 결과 정렬. 검색어가 있을 때만 0순위=이름이 검색어로 시작 / 1순위=사업자번호가 검색어로 시작 / 2순위=중간 포함 으로 묶고, 같은 순위 안에서는 기존 기준(미수 잔액 큰 순) 유지. 앞자리 판단은 _fxNormName 재사용(공백·(주)/㈜/주식회사 등 제거)이라 "케이" 검색 시 "주식회사 케이에스" 도 앞묶음. 검색에 걸리는 집합(필터)은 불변, 정렬만 변경. 미배정 입금 드롭다운(등록업체·계산서전용 두 목록)에도 동일 정렬 적용 — 60곳에서 잘리므로 순서가 중요)
- r154: live 95da4c86 / test 7f98d6fa (2026-08-26 작업본, PC test 파일 = r154, 미배포 — 미배정 입금 배정 안전장치 + 되돌리기. (1) fxAssignDep 이 후보 mm[0] 을 말없이 고르거나 후보 0곳이면 입력한 생 텍스트를 그대로 배정하던 것을 수정: 정확일치 없을 때 후보1곳=그곳 / 후보다수는 정규화 앞자리 일치가 딱 1곳이면 그곳, 아니면 후보목록 안내 후 배정 안 함 / 후보0곳은 계산서전용 거래처로 1곳 좁혀지면 fxPickNewVend(등록+배정), 아니면 안내 후 배정 안 함. 드롭다운 클릭 경로는 정확일치라 기존과 동일 동작. (2) 되돌리기: 입금 자료에 asgBat/asgAt/asgBy/asgU(이전 vendor·vbiz·held, 학습된 별칭키 a 와 별칭 이전값 pa)를 얹어 저장 — 새 동기화 키 없이 입금 블롭에 함께 저장됨. 최근 50묶음까지만 유지(_fxAsgPrune, 배정 자체는 유지). 자료 업로드 탭 상단에 "최근 거래처 배정 N건 [보기/되돌리기]" 패널 추가, 묶음 단위 되돌리기(같은 입금자명 동시배정분 포함). 별칭은 이전 값이 있었으면 그 값으로 정확히 복원, 없었으면 삭제. 자동배정 재실행(fxReassignRun)도 묶음 기록되며 별칭을 학습하지 않으므로 되돌려도 별칭 불변. fxPickCrossVend(사업장 이동 배정)는 자체 확인창이 있어 제외)
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
