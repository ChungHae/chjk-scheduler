"""
SemPlus / KIS정보통신 (화성 지점) 오프라인 매장 단말기 카드매출 - 거래건별 상세내역 스크래퍼.

SemPlus는 WebSquare라는 구형 전자정부 프레임워크 기반 사이트로,
- 클래식 <frameset>/<frame> + 그 안에 다시 <iframe> 여러 겹으로 중첩된 구조이고
- 화면이 쓰는 실제 AJAX 요청(selectCreditTranList.do)이 XML 기반의
  복잡한 자체 포맷이라, 요청/응답을 직접 흉내 내는 것보다
  "사람이 쓰는 화면을 그대로 자동화 + 이미 있는 엑셀 다운로드 기능을
  이용해 정형 데이터를 받는" 방식이 훨씬 안정적이다.

동작 방식:
  1) Playwright로 로그인 (라벨 텍스트 기준으로 아이디/비밀번호 칸을 찾음).
  2) 상단 메뉴 "거래내역 > 신용거래"로 이동.
  3) 조회기간을 "1주일"(최근 7일) 퀵버튼으로 설정 → 검색.
  4) 그 화면에 있는 "엑셀" 다운로드 버튼을 눌러 결과를 엑셀 파일로 받는다
     (Playwright의 download 이벤트로 파일을 저장).
  5) 받은 엑셀을 openpyxl로 파싱해 표 형태 그대로 레코드로 변환.
  6) Firebase에 기록.

필요한 GitHub Secrets:
  SEMPLUS_ID, SEMPLUS_PW

주의: 비밀번호 값은 어떤 경우에도 print/log하지 않는다.

※ 이 사이트는 화면 구조가 자주 바뀔 수 있는 레거시 프레임워크라,
   실제 배포 전 workflow_dispatch로 한 번 수동 실행해 셀렉터가
   맞는지 반드시 확인이 필요하다 (특히 로그인 폼과 메뉴 클릭 부분).
"""
import asyncio
import os
import sys
import tempfile

import openpyxl
from playwright.async_api import async_playwright

from common_firebase import write_transactions

BASE_URL = "https://semplus.kisvan.co.kr/"

ID_FIELD_CANDIDATES = [
    'input[placeholder*="아이디"]', 'input[name*="id" i]', '#userId', '#usr_id', '#mbr_id',
]
PW_FIELD_CANDIDATES = ['input[type="password"]']
LOGIN_SUBMIT_CANDIDATES = ['button:has-text("로그인")', 'a:has-text("로그인")', 'input[type="submit"]']


async def _first_frame_with(page, selector, timeout=8000):
    """page.frames를 훑어서 selector가 존재하는 첫 프레임을 찾는다.
    (frameset 안에 iframe이 중첩돼 있어 어느 frame이 실제 콘텐츠인지 미리 알 수 없음)"""
    deadline = asyncio.get_event_loop().time() + timeout / 1000
    while asyncio.get_event_loop().time() < deadline:
        for f in page.frames:
            try:
                if await f.locator(selector).count() > 0:
                    return f
            except Exception:
                continue
        await asyncio.sleep(0.3)
    return None


async def _find_first_in_frame(frame, selectors, timeout=3000):
    for sel in selectors:
        try:
            loc = frame.locator(sel).first
            await loc.wait_for(state="visible", timeout=timeout)
            return loc
        except Exception:
            continue
    return None


async def login(page):
    await page.goto(BASE_URL, wait_until="domcontentloaded")

    # 로그인 폼이 어느 프레임에 있는지 불확실하므로, 비밀번호 input이 있는 프레임을 우선 탐색
    pw_frame = await _first_frame_with(page, PW_FIELD_CANDIDATES[0])
    if not pw_frame:
        raise RuntimeError("SemPlus 로그인 폼(비밀번호 입력칸)을 찾지 못했습니다.")

    id_field = await _find_first_in_frame(pw_frame, ID_FIELD_CANDIDATES)
    pw_field = await _find_first_in_frame(pw_frame, PW_FIELD_CANDIDATES)
    if not id_field or not pw_field:
        raise RuntimeError("SemPlus 로그인 입력칸을 찾지 못했습니다 - 화면 구조 확인 필요.")

    await id_field.fill(os.environ["SEMPLUS_ID"])
    await pw_field.fill(os.environ["SEMPLUS_PW"])

    submit = await _find_first_in_frame(pw_frame, LOGIN_SUBMIT_CANDIDATES)
    if submit:
        await submit.click()
    else:
        await pw_field.press("Enter")

    await page.wait_for_load_state("networkidle", timeout=15000)
    if await _first_frame_with(page, 'text=로그아웃', timeout=5000) is None:
        raise RuntimeError("SemPlus 로그인 실패로 보입니다 (로그아웃 링크를 찾을 수 없음).")


async def open_credit_transaction_list(page):
    # 상단 메뉴 "거래내역" 클릭 → 드롭다운의 "신용거래" 클릭
    menu_frame = await _first_frame_with(page, 'text=거래내역')
    if not menu_frame:
        raise RuntimeError("'거래내역' 메뉴를 찾지 못했습니다.")
    await menu_frame.locator('text=거래내역').first.click()
    await page.wait_for_timeout(500)

    sub_frame = await _first_frame_with(page, 'text=신용거래')
    if not sub_frame:
        raise RuntimeError("'신용거래' 하위 메뉴를 찾지 못했습니다.")
    await sub_frame.locator('text=신용거래').first.click()
    await page.wait_for_timeout(1000)


async def search_last_week(page):
    week_btn_frame = await _first_frame_with(page, 'text=1주일')
    if not week_btn_frame:
        raise RuntimeError("'1주일' 조회기간 버튼을 찾지 못했습니다.")
    await week_btn_frame.locator('text=1주일').first.click()

    search_frame = await _first_frame_with(page, 'text=검색')
    await search_frame.locator('text=검색').first.click()
    await page.wait_for_timeout(2000)


async def download_excel(page) -> str:
    excel_frame = await _first_frame_with(page, 'text=엑셀')
    if not excel_frame:
        raise RuntimeError("'엑셀' 다운로드 버튼을 찾지 못했습니다.")
    async with page.expect_download(timeout=20000) as dl_info:
        await excel_frame.locator('text=엑셀').first.click()
    download = await dl_info.value
    path = os.path.join(tempfile.gettempdir(), "semplus_credit_tran.xlsx")
    await download.save_as(path)
    return path


def parse_excel(path: str):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = [str(h).strip() if h else "" for h in rows[0]]
    records = []
    for row in rows[1:]:
        if not any(row):
            continue
        rec = dict(zip(header, row))
        records.append(rec)
    return records


def _to_record(rec: dict) -> dict:
    """SemPlus 엑셀 1행(헤더: 전표/NO/고객ID/단말기ID/가맹점명/발급사/카드번호/
    거래금액/승인번호/거래일자/거래시간/... ) → 공통 스키마로 정규화.
    ※ 실제 엑셀 헤더명은 workflow_dispatch 첫 실행 후 로그로 확인하고
      아래 매핑을 정확한 헤더 문자열에 맞게 다듬을 것.
    """
    date = str(rec.get("거래일자") or "").replace("-", "")
    txn_id = rec.get("전표") or f"{date}_{rec.get('승인번호')}_{rec.get('거래시간')}"
    return {
        "id": txn_id,
        "date": date[:8],
        "time": str(rec.get("거래시간") or ""),
        "merchant": rec.get("가맹점명") or "",
        "txnType": rec.get("체크") or "신용",
        "cardNoMasked": rec.get("카드번호") or "",
        "approvalNo": rec.get("승인번호") or "",
        "amount": rec.get("거래금액") or 0,
        "supplyAmt": rec.get("공급금액") or 0,
        "taxAmt": rec.get("부가세") or 0,
        "source": "semplus",
        "raw": {k: v for k, v in rec.items()},
    }


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(accept_downloads=True)
        try:
            await login(page)
            await open_credit_transaction_list(page)
            await search_last_week(page)
            xlsx_path = await download_excel(page)
            raw_records = parse_excel(xlsx_path)
            print(f"SemPlus: 엑셀에서 {len(raw_records)}행 파싱됨 (헤더 확인 필요 시 첫 행 출력 참고)")
            if raw_records:
                print("헤더 샘플:", list(raw_records[0].keys()))
            records = [_to_record(r) for r in raw_records]
            if records:
                write_transactions("hwaseong", records)
                print("Firebase 기록 완료 (branch=hwaseong)")
        finally:
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[SemPlus 스크래퍼 오류] {e}", file=sys.stderr)
        sys.exit(1)
