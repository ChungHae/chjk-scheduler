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

# 로그인 폼 후보 선택자들 - 위에서부터 순서대로 시도
# (2026-08-04 workflow_dispatch 실행에서 "로그인 폼(비밀번호 입력칸)을 찾지 못했습니다"
#  오류 발생 → 로그아웃 상태의 실제 로그인 화면 DOM을 직접 확인함.
#  로그인 폼은 WebSquare 프레임워크가 그려 넣는 별도 frame
#  (websquare.html#w2xPath=/main/kr/co/kisvan/login/login.xml) 안에 있고,
#  아이디/비밀번호 입력칸은 커스텀 위젯(class="w2input w2input_mandatory")이며
#  로그인 버튼은 <button>이 아니라 클릭 가능한 <div id="grp_login">이다.)
ID_FIELD_CANDIDATES = [
    '#ibx_userId', 'input[placeholder*="아이디"]', 'input[name*="id" i]', '#userId', '#usr_id', '#mbr_id',
]
PW_FIELD_CANDIDATES = ['#ibx_Password', 'input[type="password"]']
LOGIN_SUBMIT_CANDIDATES = ['#grp_login', 'button:has-text("로그인")', 'a:has-text("로그인")', 'input[type="submit"]']

# WebSquare는 화면을 자바스크립트로 그려 넣는 구형 프레임워크라, 헤드리스/CI
# 환경(특히 매번 새로 뜨는 GitHub Actions 러너)에서는 렌더링이 끝날 때까지
# 예상보다 오래 걸릴 수 있다 - 넉넉하게 잡는다.
LOGIN_FRAME_TIMEOUT_MS = 25000


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
    try:
        # WebSquare는 백그라운드 폴링(남은시간 카운트다운 등) 때문에 완전히
        # idle 상태가 되지 않을 수 있으므로, 실패해도 무시하고 진행한다.
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    # 로그인 폼이 어느 프레임에 있는지 불확실하므로, 비밀번호 input이 있는 프레임을 우선 탐색
    pw_frame = await _first_frame_with(page, PW_FIELD_CANDIDATES[0], timeout=LOGIN_FRAME_TIMEOUT_MS)
    if not pw_frame:
        raise RuntimeError("SemPlus 로그인 폼(비밀번호 입력칸)을 찾지 못했습니다.")

    id_field = await _find_first_in_frame(pw_frame, ID_FIELD_CANDIDATES)
    pw_field = await _find_first_in_frame(pw_frame, PW_FIELD_CANDIDATES)
    if not id_field or not pw_field:
        raise RuntimeError("SemPlus 입력칸을 찾지 못했습니다 - 화면 구조 확인 필요.")

    # WebSquare의 w2input 위젯은 화면에 보이는 값과 별개로, 내부적으로는
    # 키 입력 이벤트(keydown/keyup)를 하나하나 받아서 자기만의 데이터
    # 모델에 반영하는 경우가 많다. Playwright의 fill()은 값을 한 번에
    # 넣고 input 이벤트 한 번만 보내기 때문에, 화면엔 값이 보여도 위젯의
    # 내부 모델은 비어 있거나 예전 값 그대로라 로그인 버튼을 눌러도
    # 실제로는 빈 아이디/비밀번호로 시도된 것처럼 실패할 수 있다.
    # → 진짜 타이핑처럼 한 글자씩 키 이벤트를 보내는 press_sequentially를 사용.
    await id_field.click()
    await id_field.fill("")
    await id_field.press_sequentially(os.environ["SEMPLUS_ID"], delay=40)

    await pw_field.click()
    await pw_field.fill("")
    await pw_field.press_sequentially(os.environ["SEMPLUS_PW"], delay=40)

    # 일부 WebSquare 위젯은 blur 시점에야 값 검증/모델 확정을 하므로,
    # 로그인 버튼을 누르기 전에 Tab으로 포커스를 옮겨 blur를 발생시킨다.
    await pw_field.press("Tab")
    await page.wait_for_timeout(300)

    submit = await _find_first_in_frame(pw_frame, LOGIN_SUBMIT_CANDIDATES)
    if submit:
        await submit.click()
    else:
        await pw_field.press("Enter")

    await page.wait_for_timeout(2000)
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    # 신규/미등록 환경(예: GitHub Actions처럼 매번 IP가 바뀌는 러너)에서 로그인하면
    # SemPlus가 SMS 2차 인증(#ibx_2Factor)을 요구할 수 있다. 이 경우 사람이 문자로
    # 받은 인증번호를 입력해야 해서 완전 자동화가 불가능하므로, 원인을 명확히 구분해
    # 알린다 (단순 선택자 문제와 헷갈리지 않도록).
    twofactor_frame = await _first_frame_with(page, '#ibx_2Factor', timeout=3000)
    if twofactor_frame:
        try:
            twofactor_visible = await twofactor_frame.locator('#ibx_2Factor').first.is_visible()
        except Exception:
            twofactor_visible = True
        if twofactor_visible:
            raise RuntimeError(
                "SemPlus에서 SMS 2차 인증(#ibx_2Factor)을 요구하고 있습니다. "
                "GitHub Actions처럼 매번 IP가 바뀌는 환경은 신규 기기로 인식되어 "
                "2차 인증이 뜰 수 있는데, 이 경우 자동 로그인은 불가능합니다 - "
                "SemPlus 고객센터에 해당 계정의 신규기기 2차 인증을 끄거나 예외 처리할 "
                "수 있는지 문의가 필요합니다."
            )

    if await _first_frame_with(page, 'text=로그아웃', timeout=8000) is None:
        # 원인 파악을 돕기 위해, 화면에 남아있는 오류 메시지가 있다면 함께 남긴다.
        # (비밀번호 값 자체가 아니라 "비밀번호가 일치하지 않습니다" 같은 안내
        #  문구만 찾는 것이므로 자격증명이 로그에 노출되지 않는다.)
        err_text = None
        try:
            for f in page.frames:
                try:
                    body_text = await f.locator("body").inner_text(timeout=1000)
                except Exception:
                    continue
                for line in body_text.splitlines():
                    line = line.strip()
                    if line and len(line) < 80 and any(
                        kw in line for kw in ("비밀번호", "아이디", "일치", "오류", "잠금", "실패", "인증")
                    ):
                        err_text = line
                        break
                if err_text:
                    break
        except Exception:
            pass
        msg = "SemPlus 로그인 실패로 보입니다 (로그아웃 링크를 찾을 수 없음)."
        if err_text:
            msg += f" 화면 표시 메시지로 추정: {err_text!r}"
        raise RuntimeError(msg)


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
