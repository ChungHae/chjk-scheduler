"""
chjk-scheduler Firebase Realtime Database 공용 쓰기 모듈.

GitHub Actions에서 매장 단말기(POS) 카드매출 데이터를 긁어와
업무관리 앱(chjk-scheduler)이 읽는 것과 동일한 Firebase RTDB에
서버 쪽(관리자 권한)으로 기록하기 위한 헬퍼.

앱 자체는 사용자별 커스텀 로그인(합성 이메일 + 해시 비밀번호) 방식을
쓰지만, 서버 자동화 스크립트는 그 방식을 흉내 낼 필요 없이
Firebase 서비스 계정(관리자 키)으로 붙어서 보안 규칙을 그대로
우회(관리자 권한이므로 정상)하는 것이 훨씬 안전하고 간단하다.

필요한 GitHub Secret: FIREBASE_SERVICE_ACCOUNT_JSON
  - Firebase 콘솔 > 프로젝트 설정 > 서비스 계정 > "새 비공개 키 생성"으로
    받은 JSON 파일의 '내용 전체'를 그대로 문자열로 저장.
"""
import json
import os

import firebase_admin
from firebase_admin import credentials, db

DATABASE_URL = "https://chjk-scheduler-default-rtdb.asia-southeast1.firebasedatabase.app"

# index.html의 _FB_PATH 상수와 동일한 프리픽스.
# (운영 배포 URL에는 '/test/'가 없으므로 _IS_STAGE=false → 'teamdata_test')
FB_PATH_PREFIX = "teamdata_test"
CARD_SALES_ROOT = f"{FB_PATH_PREFIX}_cardsales"

_app = None


def get_db():
    global _app
    if _app is None:
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if not raw:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON 환경변수(시크릿)가 없습니다.")
        cred = credentials.Certificate(json.loads(raw))
        _app = firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
    return db


def write_transactions(branch: str, records: list):
    """
    branch: 'seoul' | 'hwaseong'
    records: [{id, date(YYYYMMDD), time, merchant, issuer, installment,
               cardNoMasked, approvalNo, amount, supplyAmt, taxAmt, source,
               raw}, ...]

    거래 고유 id를 key로 사용해 upsert하므로, 같은 거래를 여러 번
    다시 긁어와도 중복되지 않고 덮어쓰기만 된다(멱등성).
    """
    dbm = get_db()
    grouped = {}
    for r in records:
        date = r["date"]
        grouped.setdefault(date, {})[_safe_key(r["id"])] = r

    for date, rows in grouped.items():
        ref = dbm.reference(f"{CARD_SALES_ROOT}/{branch}/{date}")
        ref.update(rows)

    # 프론트엔드에서 "마지막 동기화 시각"을 표시할 수 있도록 메타 정보도 기록
    dbm.reference(f"{CARD_SALES_ROOT}/_meta/{branch}").set({
        "lastSyncedAt": _now_iso(),
        "lastSyncedDates": sorted(grouped.keys()),
        "lastSyncedCount": sum(len(v) for v in grouped.values()),
    })


def reset_branch(branch: str):
    """해당 지점의 카드매출 데이터를 전부 삭제한다(동기화 데이터라 소스에서
    다시 채울 수 있으므로 안전 - 사용자가 직접 입력한 데이터가 아님).

    2026-08-05 머니온 날짜 필드 버그 수정(입금일 → 실제 거래일) 이후, 기존에
    잘못된 날짜로 이미 기록된 데이터가 새 날짜 경로에 중복으로 남는 것을
    막기 위해 백필 재실행 전 한 번 정리할 용도로 추가함."""
    dbm = get_db()
    dbm.reference(f"{CARD_SALES_ROOT}/{branch}").delete()
    dbm.reference(f"{CARD_SALES_ROOT}/_meta/{branch}").delete()


def _safe_key(raw_id: str) -> str:
    # Firebase 키에는 '.', '#', '$', '/', '[', ']' 사용 불가
    return "".join(c if c not in ".#$/[]" else "_" for c in str(raw_id))


def _now_iso():
    import datetime
    return datetime.datetime.utcnow().isoformat() + "Z"
