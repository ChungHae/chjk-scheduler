"""
SemPlus / KIS정보통신 (화성 지점) 카드매출 - 과거 데이터 한 번에 채우기(백필) 스크립트.

평소 매일 자동 동기화(scrape_semplus.py)는 최근 1주일치만 가져오지만,
이 스크립트는 지정한 기간(기본: 2026-01-01 ~ 오늘) 전체를 한 번만 긁어와
Firebase에 채워 넣는다. 로그인/메뉴이동/엑셀 파싱/기록 로직은 전부
scrape_semplus.py 것을 그대로 재사용하고, 여기서는 "기간을 직접
지정해서 조회하는" 부분만 새로 만든다.

거래 고유 id를 key로 upsert하므로 중복 실행해도 안전하다(멱등) -
실패한 구간만 다시 실행해도 되고, 전체를 다시 돌려도 무방하다.

SemPlus 신용거래 조회 화면은 한 번에 조회 가능한 기간이 35일로
제한되어 있음(실제 화면에서 넓은 기간으로 검색을 시도했을 때 뜬
경고창으로 확인됨) - 전체 기간을 35일 이하 조각(chunk)으로 나눠
여러 번 조회한다.

특정 초기 구간(예: 2026년 1월)에 데이터가 없어도 정상 - 해당 구간은
0건으로 기록되고 다음 구간으로 계속 진행된다("안 되면 되는 날부터"
요구사항을 별도 분기 없이 자연스럽게 만족).

2026-08-05 중요 버그 수정: 이전 버전은 드롭다운 항목을 화면 전체에서
text="01월" 같은 글자로만 찾아 클릭했는데, WebSquare 화면에는 같은
글자가 드롭다운 목록 밖(달력 라벨 등)에도 있을 수 있어 엉뚱한 요소를
클릭하고도 "성공"으로 지나가는 조용한 실패가 가능했다. 실제로 백필을
두 번(어제/오늘) 돌렸을 때 7개 구간 전부가 매번 정확히 2건씩(총 14건)
나왔는데, 같은 날 daily 동기화(1주일 조회)는 4행을 파싱했다 - 즉 조회
기간이 실제로는 바뀌지 않고 매번 기본 화면 결과만 다운로드했을 가능성이
크다. 그래서 이번 버전은
  (1) 드롭다운 항목을 해당 드롭다운의 목록(id가 박스 id로 시작하는
      요소들) 안에서 우선 찾고,
  (2) 선택 후 드롭다운에 표시된 글자를 다시 읽어 원하는 값으로 바뀌었는지
      검증하며(안 바뀌었으면 그 구간을 실패로 처리),
  (3) 다운로드한 엑셀의 거래일자가 요청한 구간을 벗어나면 그 구간을
      실패로 처리한다(조용히 엉뚱한 데이터를 기록하지 않도록).

실행:
  python backfill_semplus.py [시작일 YYYY-MM-DD] [종료일 YYYY-MM-DD]
  인자를 생략(또는 빈 문자열)하면 시작일=2026-01-01, 종료일=오늘.

필요한 GitHub Secrets: SEMPLUS_ID, SEMPLUS_PW, FIREBASE_SERVICE_ACCOUNT_JSON
(daily 동기화와 동일한 시크릿을 그대로 사용)
"""
import asyncio
import datetime as _dt
import sys

from playwright.async_api import async_playwright

from scrape_semplus import (
    DEBUG_SCREENSHOT_PATH,
    _first_visible_anywhere,
    _to_record,
    download_excel,
    login,
    open_credit_transaction_list,
    parse_excel,
)
from common_firebase import write_transactions, reset_branch
import os as _os

CHUNK_MAX_DAYS = 35  # 실제 조회 화면에서 확인된 제한(35일 이내로만 조회 가능)
DEFAULT_START = _dt.date(2026, 1, 1)


def _date_chunks(start: _dt.date, end: _dt.date, max_days: int):
    """[start, end] 구간을 max_days 이하 크기로 나눠 (chunk_start, chunk_end) 리스트로 반환."""
    chunks = []
    cur = start
    one_day = _dt.timedelta(days=1)
    while cur <= end:
        chunk_end = min(cur + _dt.timedelta(days=max_days - 1), end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + one_day
    return chunks


async def _read_box_label(page, box_id: str) -> str:
    """드롭다운 박스에 현재 표시된 글자를 읽는다(검증용). 못 읽으면 빈 문자열."""
    box = await _first_visible_anywhere(page, f'#{box_id}', timeout=3000)
    if not box:
        return ""
    try:
        return (await box.inner_text()).strip()
    except Exception:
        return ""


async def _select_dropdown(page, box_id: str, option_text: str):
    """WebSquare의 w2selectbox(커스텀 드롭다운) 위젯 - id를 가진 버튼을 눌러
    목록을 열고, 그 드롭다운의 목록 안에서 option_text와 일치하는 항목을
    클릭한 뒤, 실제로 선택이 반영됐는지 표시 글자를 다시 읽어 검증한다.

    (2026-08-05 수정) 예전엔 화면 전체에서 text=로만 항목을 찾아, 목록
    밖의 같은 글자를 클릭하고도 성공한 것처럼 지나가는 조용한 실패가
    가능했다 - 이제 id가 박스 id로 시작하는 요소(WebSquare가 목록을
    "{box_id}_itemTable_..." 같은 id로 그림) 안에서 우선 찾고, 선택 후
    반드시 검증한다."""
    for attempt in (1, 2):
        # 이미 원하는 값이면 그대로 통과 (재실행/재시도 시 불필요한 클릭 방지)
        current = await _read_box_label(page, box_id)
        if option_text in current:
            return

        btn = await _first_visible_anywhere(page, f'#{box_id}')
        if not btn:
            raise RuntimeError(f"'{box_id}' 드롭다운을 화면에서 찾지 못했습니다.")
        await btn.click()
        await page.wait_for_timeout(300)

        # 1순위: 해당 드롭다운의 목록(id가 박스 id로 시작) 안에서 찾기,
        # 2순위: (혹시 목록 id 규칙이 다르면) 화면 전체에서 찾기.
        opt = await _first_visible_anywhere(
            page, f'[id^="{box_id}_"] >> text="{option_text}"', timeout=2000
        )
        if not opt:
            opt = await _first_visible_anywhere(
                page, f'text="{option_text}"', timeout=2000
            )
        if not opt:
            raise RuntimeError(
                f"'{box_id}' 드롭다운에서 '{option_text}' 항목을 찾지 못했습니다."
            )
        await opt.click()
        await page.wait_for_timeout(300)

        # 선택이 실제로 반영됐는지 검증
        after = await _read_box_label(page, box_id)
        if option_text in after:
            return
        # 반영 안 됐으면 한 번 더 시도(2회째도 실패하면 아래에서 오류)

    raise RuntimeError(
        f"'{box_id}' 드롭다운을 '{option_text}'(으)로 바꾸지 못했습니다 "
        f"(현재 표시: '{after}'). 조회 기간이 적용되지 않아 이 구간을 실패 처리합니다."
    )


async def search_range(page, start: _dt.date, end: _dt.date):
    """조회기간을 start~end(같은 해 안)로 직접 지정해 검색한다.
    (화면의 '1주일' 등 빠른 버튼 대신, 조회조건의 연/월/일 드롭다운
    5개(년/시작월/시작일/종료월/종료일)를 직접 설정 - 실제 화면에서
    확인된 위젯 id: sbx_TrYyyy, sbx_TrFromMon, sbx_TrFromDay,
    sbx_TrToMon, sbx_TrToDay)"""
    if start.year != end.year:
        raise ValueError(
            "SemPlus 조회기간 연도 셀렉트가 1개뿐이라 같은 해 안에서만 나눠야 합니다 "
            f"(요청: {start} ~ {end})."
        )
    await _select_dropdown(page, "sbx_TrYyyy", f"{start.year}년")
    await _select_dropdown(page, "sbx_TrFromMon", f"{start.month:02d}월")
    await _select_dropdown(page, "sbx_TrFromDay", f"{start.day:02d}일")
    await _select_dropdown(page, "sbx_TrToMon", f"{end.month:02d}월")
    await _select_dropdown(page, "sbx_TrToDay", f"{end.day:02d}일")

    # 설정된 값을 로그로 남겨 나중에 검증할 수 있게 한다.
    labels = []
    for box_id in ("sbx_TrYyyy", "sbx_TrFromMon", "sbx_TrFromDay", "sbx_TrToMon", "sbx_TrToDay"):
        labels.append(await _read_box_label(page, box_id))
    print(f"  조회기간 설정 확인: {' / '.join(labels)}")

    search_btn = await _first_visible_anywhere(page, "text=검색")
    if not search_btn:
        raise RuntimeError("'검색' 버튼이 화면에 보이지 않습니다.")
    await search_btn.click()
    await page.wait_for_timeout(2000)


def _check_record_dates(records, cs: _dt.date, ce: _dt.date):
    """다운로드한 레코드들의 거래일자가 요청 구간 안인지 검증.
    구간 밖 날짜가 있으면 (조회 기간이 적용되지 않았다는 뜻이므로)
    오류를 던져 해당 구간을 실패로 처리한다. 날짜를 아예 못 읽은
    레코드는 판단 불가라 그대로 둔다. 반환값: (최소날짜, 최대날짜) 문자열."""
    seen = []
    bad = []
    for r in records:
        d = str(r.get("date") or "")
        if len(d) == 8 and d.isdigit():
            try:
                dt = _dt.date(int(d[:4]), int(d[4:6]), int(d[6:8]))
            except ValueError:
                continue
            seen.append(d)
            if not (cs <= dt <= ce):
                bad.append(d)
    if bad:
        raise RuntimeError(
            f"다운로드한 데이터의 거래일자가 요청 구간({cs}~{ce}) 밖입니다 "
            f"(예: {sorted(set(bad))[:5]}). 조회 기간이 화면에 적용되지 않은 "
            "것으로 보여 이 구간을 실패 처리합니다."
        )
    if seen:
        return min(seen), max(seen)
    return "", ""


def _parse_date_arg(argv, idx, default):
    if len(argv) > idx and argv[idx]:
        return _dt.date.fromisoformat(argv[idx])
    return default


async def main():
    start = _parse_date_arg(sys.argv, 1, DEFAULT_START)
    end = _parse_date_arg(sys.argv, 2, _dt.date.today())
    chunks = _date_chunks(start, end, CHUNK_MAX_DAYS)
    print(f"SemPlus 백필: {start} ~ {end}, {len(chunks)}개 구간(최대 {CHUNK_MAX_DAYS}일씩)으로 나눠 조회합니다.")

    # 카드매출 화면 개편(발급사/할부 항목 추가)에 맞춰 기존 데이터를 깨끗하게
    # 다시 채우고 싶을 때 CARD_SALES_RESET=1로 재실행하면 기존 데이터를 지우고
    # 새로 받는다(동기화 데이터라 안전).
    if _os.environ.get("CARD_SALES_RESET") in ("1", "true", "True"):
        print("[안내] CARD_SALES_RESET=1 - 기존 화성(SemPlus) 카드매출 데이터를 삭제하고 새로 채웁니다.")
        reset_branch("hwaseong")

    failed = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(accept_downloads=True)
        try:
            await login(page)
            await open_credit_transaction_list(page)

            total = 0
            for i, (cs, ce) in enumerate(chunks, 1):
                print(f"[{i}/{len(chunks)}] {cs} ~ {ce} 조회 중...")
                try:
                    await search_range(page, cs, ce)
                    xlsx_path = await download_excel(page)
                    raw_records = parse_excel(xlsx_path)
                    records = [_to_record(r) for r in raw_records]
                    dmin, dmax = _check_record_dates(records, cs, ce)
                    if records:
                        write_transactions("hwaseong", records)
                    total += len(records)
                    span = f", 거래일자 {dmin}~{dmax}" if dmin else ""
                    print(f"  → {len(records)}건 기록 (누적 {total}건{span})")
                except Exception as e:
                    print(f"  [경고] {cs}~{ce} 구간 실패: {e} - 건너뛰고 계속 진행합니다.")
                    failed.append((cs, ce, str(e)))

            print(f"SemPlus 백필 완료: 총 {total}건")
            if failed:
                print(f"[경고] 실패한 구간 {len(failed)}개 - 나중에 해당 구간만 다시 실행 필요:")
                for cs, ce, err in failed:
                    print(f"  - {cs} ~ {ce}: {err}")
        except Exception:
            try:
                await page.screenshot(path=DEBUG_SCREENSHOT_PATH, full_page=True)
                print(f"[디버그] 실패 시점 스크린샷 저장: {DEBUG_SCREENSHOT_PATH}")
            except Exception:
                pass
            raise
        finally:
            await browser.close()

    if failed:
        sys.exit(1)  # 일부 구간 실패 시 CI에서 실패로 표시(재확인 유도)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[SemPlus 백필 오류] {e}", file=sys.stderr)
        sys.exit(1)
