# r196 — 두 작업 흐름 병합 복구 (2026-09-18)

## 무슨 일이 있었나
이 저장소에 **rNN 번호를 각자 매기는 작업 흐름이 두 개** 돌고 있었고, 서로의 커밋을
번갈아 덮어쓰고 있었다. 양쪽 다 "직전 배포본"을 자기 로컬 파일로만 확인하고
**저장소의 현재 index.html 해시를 확인하지 않은 채** 업로드했기 때문이다.

- 흐름 A (회계·매입매출): r189 기업은행 어음 인식 → r190 하나 적요 → r191 적요 배지 → r192 보류·제외 정렬
- 흐름 B (견적·일정·회의록): r192 IME Enter → r193 일정 주간·개발 키워드 → r194 같은 규격 가격 통일 → r195 붙여넣기 가격 연동

커밋 순서(모두 index.html):
  885b2be r188 (공통조상, live c943e3b5 / test 7cf2608a)
  421635c B r192 → cbe2e84 B r193
  a132ddc A r189 → 41ba28c A r190 → 41191cd A r191 → cded1de A r192   ← B r192·r193 을 덮음
  ba7f372 B r194 → 094fdea B r195                                      ← A r189~r192 를 덮음
  7cd9546 어음차단 r193 → 281091c 어음차단 r194                          ← B r194·r195 를 덮음

## 어떻게 복구했나
`git merge-file` 3-way 병합 (공통조상 r188 기준):
  base  = 885b2be:index.html (c943e3b5) / 7ca67f7:test/index.html (7cf2608a)
  side1 = 094fdea:index.html (99dd3bb9) / 027d595:test/index.html (b143f76b)   ← 흐름 B r195
  side2 = 281091c:index.html (288741ed) / 6821077:test/index.html (afab2445)   ← 흐름 A r192 + 어음차단

live 는 충돌 0. test 는 `<!-- test build rNN -->` 한 줄만 충돌 → r196 으로 정리.

결과: **live 32348ba8 / test fa3dc5b5**

## 검증
- node --check 전 스크립트 블록 통과
- 방향별 diff 로 교차 오염 없음 확인
    B(r195) → 병합본 : `_fx*` 식별자만 변경  (= 흐름 A 작업만 들어감)
    A(어음차단) → 병합본 : `_mt*`/`_mm*`/`_qCart*` 만 변경 (= 흐름 B 작업만 들어감)
- 회계 스위트: r194 15/15 · r193 11/11 · r192 9/9 · r191 10/10 · r190 8/8 · r189 9/9
- 회귀: r176 23/23 · r175 26/26 · r174 16/16 · r173 13/13 · r172 17/17 · unq 12/12 · qpaste 13/13
- 교차 스모크 mgsmoke.js 16/16 (양쪽 흐름 함수 전부 정의 + 붙여넣기가 _qCartSyncSameSpec 호출 + 어음 차단 가드 생존)
- 서빙 바이트 확인 (github.io, cache:'no-store'): live 32348ba8 / test fa3dc5b5, 7개 기능 마커 전부 true

## ★ 재발 방지 (반드시 지킬 것)
1. **업로드 직전에 저장소의 현재 blob 해시를 확인한다.** 로컬 해시만 보면 안 된다.
   `git clone --depth 1` 후 `git hash-object index.html test/index.html` 가 내 직전 배포본과
   같은지 본다. 다르면 다른 흐름이 먼저 올린 것이므로 **그 파일을 새 base 로 삼아 다시 빌드**한다.
2. **rNN 번호는 저장소 기준으로 매긴다.** `git log --oneline -- index.html` 로 마지막 번호를 보고
   그 다음 번호를 쓴다. 자기 로컬 체인의 번호를 쓰면 충돌한다.
3. 커밋 메시지에 어느 영역인지 적는다 (예: `r197(회계): …`).
