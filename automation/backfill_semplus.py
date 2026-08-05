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


async def _select_dropdown(page, box_id: str, option_text: str):
    """WebSquare의 w2selectbox(커스텀 드롭다운) 위젯 - id를 가진 버튼을 눌러
    목록을 열고, 정확히 option_text와 일치하는(화면에 보이는) 항목을 클릭한다.
    (로그인/메뉴 클릭에서 겪었던 것과 같은 종류의 커스텀 위젯이라, 같은
    파일의 _first_visible_anywhere를 그대로 재사용해 "실제로 보이는 첫
    항목"만 고른다.)"""
    btn = await _first_visible_anywhere(page, f'#{box_id}')
    if not btn:
        raise RuntimeError(f"'{box_id}' 드롭다운을 화면에서 찾지 못했습니다.")
    await btn.click()
    await page.wait_for_timeout(200)
    opt = await _first_visible_anywhere(page, f'text="{option_text}"', timeout=3000)
    if not opt:
        raise RuntimeError(f"'{box_id}' 드롭다운에서 '{option_text}' 항목을 찾지 못했습니다.")
    await opt.click()
    await page.wait_for_timeout(200)


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

    search_btn = await _first_visible_anywhere(page, "text=검색")
    if not search_btn:
        raise RuntimeError("'검색' 버튼이 화면에 보이지 않습니다.")
    await search_btn.click()
    await page.wait_for_timeout(2000)


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
                    if records:
                        write_transactions("hwaseong", records)
                    total += len(records)
                    print(f"  → {len(records)}건 기록 (누적 {total}건)")
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
