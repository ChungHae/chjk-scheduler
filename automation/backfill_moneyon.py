"""
머니온(MoneyOn, 서울 지점) 카드매출 - 과거 데이터 한 번에 채우기(백필) 스크립트.

평소 매일 자동 동기화(scrape_moneyon.py)는 최근 7일치만 가져오지만,
이 스크립트는 지정한 기간(기본: 2026-01-01 ~ 오늘) 전체를 한 번만 긁어와
Firebase에 채워 넣는다. 로그인/조회/엑셀다운로드/파싱 로직은 전부
scrape_moneyon.py 것을 그대로 재사용하고, 여기서는 "긴 기간을 여러 구간으로
나눠 반복 조회하는" 부분만 새로 만든다.

2026-08-05: scrape_moneyon.py가 JSON API 가로채기 방식에서 엑셀 다운로드
방식으로 바뀌면서, 구간마다 "조회 → 저장 버튼으로 엑셀 받기 → 파싱"을
반복하도록 함께 바뀜(예전의 page_no 페이지네이션은 더 이상 필요 없음 -
엑셀 저장은 조회된 전체 건을 한 파일로 받아오는 방식이라서).

거래 고유 id를 key로 upsert하므로 중복 실행해도 안전하다(멱등).

머니온 자체의 조회기간 제한 (2가지, 서로 다름):
  1) 한 번에 조회 가능한 "폭"이 31일 이내 (화면에서 실제로 확인: "조회값을
     31일 이내로 하라"는 안내가 뜸 - SemPlus의 35일 제한과는 다름, 더 짧음).
     그래서 31일 단위로 나눠서 조회한다.
  2) 조회 시작일이 오늘로부터 180일 이내여야 함(사용자가 머니온 화면에서
     직접 확인: "180일 이내의 자료만 조회 가능"). 이보다 오래된 과거는
     머니온 자체에서 아예 조회가 안 되므로, 자동화로도 가져올 수 없다.
(2026-08-05 백필 실행에서, 31일 제한만 반영해 재실행했는데도 가장 오래된
 2개 구간(1~2월)만 계속 타임아웃 나는 것을 확인 - 처음엔 폭 제한(1번)
 문제인 줄 알았으나, 실제로는 180일 제한(2번)에 걸린 것이었음. 그래서
 아래에서 조회 시작일을 180일 제한 안쪽으로 강제 조정한다.)

특정 초기 구간에 데이터가 없어도 정상 - 해당 구간은 0건으로 기록되고
다음 구간으로 계속 진행된다. 다만 180일 제한보다 오래된 구간은 애초에
조회 자체가 안 되므로(0건이 아니라 타임아웃) 아예 건너뛴다.

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

from scrape_moneyon import DETAIL_URL, _to_record, download_excel, login, parse_excel, search_range
from common_firebase import write_transactions, reset_branch
import os as _os

CHUNK_MAX_DAYS = 31  # 머니온 화면에서 실제로 확인된 제한("31일 이내")
MAX_LOOKBACK_DAYS = 180  # 머니온 화면에서 실제로 확인된 제한("180일 이내의 자료만 조회 가능")
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

    # 180일 제한: 조회 시작일을 "오늘 - 179일"(오늘 포함 180일) 안쪽으로 강제 조정.
    # 이보다 오래된 기간은 머니온 자체에서 조회가 안 되므로 시도해도 항상 타임아웃만
    # 나고 끝난다 - 아예 조회 대상에서 제외해 불필요한 실패/시간낭비를 막는다.
    earliest_available = _dt.date.today() - _dt.timedelta(days=MAX_LOOKBACK_DAYS - 1)
    if start < earliest_available:
        print(
            f"[안내] 머니온은 오늘로부터 {MAX_LOOKBACK_DAYS}일 이내 데이터만 조회 가능합니다. "
            f"요청하신 시작일({start})은 그보다 오래되어 조회가 불가능하므로, "
            f"실제 조회는 {earliest_available}부터 진행합니다. "
            f"({start} ~ {earliest_available - _dt.timedelta(days=1)} 구간은 머니온 자체 "
            "제한으로 자동조회 불가 - 필요하면 머니온에 별도 문의 필요)"
        )
        start = earliest_available

    if start > end:
        print(f"[안내] 조회 가능한 시작일({start})이 종료일({end})보다 늦어 조회할 구간이 없습니다.")
        return

    chunks = _date_chunks(start, end, CHUNK_MAX_DAYS)
    print(f"머니온 백필: {start} ~ {end}, {len(chunks)}개 구간(최대 {CHUNK_MAX_DAYS}일씩)으로 나눠 조회합니다.")

    # 2026-08-05: 날짜 필드 매핑 버그 수정(입금일 money_rcv_date → 실제 거래일
    # auth_date) 이후, 기존에 잘못된 날짜로 이미 기록된 데이터가 새 날짜 경로에
    # 중복으로 남지 않도록, CARD_SALES_RESET=1 이면 재조회 전에 기존 데이터를
    # 통째로 지우고 새로 채운다(동기화 데이터라 안전 - 사용자가 직접 입력한
    # 값이 아니라 언제든 소스에서 다시 받아올 수 있음).
    if _os.environ.get("CARD_SALES_RESET") in ("1", "true", "True"):
        print("[안내] CARD_SALES_RESET=1 - 기존 서울(머니온) 카드매출 데이터를 삭제하고 새로 채웁니다.")
        reset_branch("seoul")

    failed = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(accept_downloads=True)
        try:
            await login(page)
            await page.goto(DETAIL_URL, wait_until="domcontentloaded")

            total = 0
            for i, (cs, ce) in enumerate(chunks, 1):
                fr_str = cs.strftime("%y%m%d")
                to_str = ce.strftime("%y%m%d")
                print(f"[{i}/{len(chunks)}] {cs} ~ {ce} 조회 중...")
                try:
                    await search_range(page, fr_str, to_str)
                    xlsx_path = await download_excel(page)
                    raw_records = parse_excel(xlsx_path)
                    records = [_to_record(r) for r in raw_records]
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
