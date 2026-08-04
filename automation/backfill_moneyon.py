"""
머니온(MoneyOn, 서울 지점) 카드매출 - 과거 데이터 한 번에 채우기(백필) 스크립트.

평소 매일 자동 동기화(scrape_moneyon.py)는 최근 7일치만 가져오지만,
이 스크립트는 지정한 기간(기본: 2026-01-01 ~ 오늘) 전체를 한 번만 긁어와
Firebase에 채워 넣는다. 로그인/조회/파싱 로직은 전부 scrape_moneyon.py
것을 그대로 재사용하고, 여기서는 "긴 기간을 여러 구간으로 나눠 반복
조회하는" 부분만 새로 만든다.

거래 고유 id를 key로 upsert하므로 중복 실행해도 안전하다(멱등).

머니온 자체의 조회기간 제한은 확인되지 않았지만(SemPlus는 35일 제한이
실제로 확인됨), 안전하게 SemPlus와 동일한 35일 단위로 나눠서 조회한다.

특정 초기 구간에 데이터가 없어도 정상 - 해당 구간은 0건으로 기록되고
다음 구간으로 계속 진행된다.

실행:
  python backfill_moneyon.py [시작일 YYYY-MM-DD] [종료일 YYYY-MM-DD]
  인자를 생략(또는 빈 문자열)하면 시작일=2026-01-01, 종료일=오늘.

필요한 GitHub Secrets: MONEYON_ID, MONEYON_PW, FIREBASE_SERVICE_ACCOUNT_JSON
(daily 동기화와 동일한 시크릿을 그대로 사용)
"""
import asyncio
import datetime as _dt
import sys

from playwright.async_api import async_playwright

from scrape_moneyon import DETAIL_URL, _to_record, fetch_detail_page, login
from common_firebase import write_transactions

CHUNK_MAX_DAYS = 35  # SemPlus에서 확인된 제한과 동일하게 보수적으로 통일
DEFAULT_START = _dt.date(2026, 1, 1)
DEBUG_SCREENSHOT_PATH = "moneyon_backfill_debug.png"


def _date_chunks(start: _dt.date, end: _dt.date, max_days: int):
    chunks = []
    cur = start
    one_day = _dt.timedelta(days=1)
    while cur <= end:
        chunk_end = min(cur + _dt.timedelta(days=max_days - 1), end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + one_day
    return chunks


def _parse_date_arg(argv, idx, default):
    if len(argv) > idx and argv[idx]:
        return _dt.date.fromisoformat(argv[idx])
    return default


async def main():
    start = _parse_date_arg(sys.argv, 1, DEFAULT_START)
    end = _parse_date_arg(sys.argv, 2, _dt.date.today())
    chunks = _date_chunks(start, end, CHUNK_MAX_DAYS)
    print(f"머니온 백필: {start} ~ {end}, {len(chunks)}개 구간(최대 {CHUNK_MAX_DAYS}일씩)으로 나눠 조회합니다.")

    failed = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        try:
            await login(page)
            await page.goto(DETAIL_URL, wait_until="domcontentloaded")

            total = 0
            for i, (cs, ce) in enumerate(chunks, 1):
                fr_str = cs.strftime("%y%m%d")
                to_str = ce.strftime("%y%m%d")
                print(f"[{i}/{len(chunks)}] {cs} ~ {ce} 조회 중...")
                try:
                    all_rows = []
                    page_no = 1
                    while True:
                        data = await fetch_detail_page(page, fr_str, to_str, page_no)
                        rows = data.get("data") or []
                        all_rows.extend(rows)
                        total_rows = data.get("TOTROWS", len(rows))
                        if len(all_rows) >= total_rows or not rows:
                            break
                        page_no += 1
                        if page_no > 50:  # 안전장치: 무한루프 방지(원본 스크립트와 동일)
                            print(f"  [경고] 페이지가 50페이지를 넘어 중단합니다(TOTROWS={total_rows})")
                            break
                    records = [_to_record(r) for r in all_rows if r]
                    if records:
                        write_transactions("seoul", records)
                    total += len(records)
                    print(f"  → {len(records)}건 기록 (누적 {total}건)")
                except Exception as e:
                    print(f"  [경고] {cs}~{ce} 구간 실패: {e} - 건너뛰고 계속 진행합니다.")
                    failed.append((cs, ce, str(e)))

            print(f"머니온 백필 완료: 총 {total}건")
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
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[머니온 백필 오류] {e}", file=sys.stderr)
        sys.exit(1)
