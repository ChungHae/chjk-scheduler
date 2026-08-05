"""
전 직원 계정의 Firebase Auth 로그인 비밀번호를, 현재 계정 DB(RTDB teamdata_test_accounts)에
저장된 pwHash 값과 다시 맞춰주는(재동기화) 일회성 스크립트.

배경
----
이 앱은 비밀번호를 두 군데에 보관한다.
  1) RTDB `teamdata_test_accounts/{성명}.pwHash` - 관리자 "계정 관리" 화면이 직접 다루는 값
  2) Firebase Auth 서버 자체의 로그인 비밀번호 - 실제 로그인 인증(signIn)에 쓰이는 값
     (index.html의 _fbEnsureAuth/_fbProvisionAccount를 보면, 이 값은 실제 평문 비밀번호가
      아니라 그 sha256 해시 문자열 그 자체를 그대로 Firebase Auth의 "비밀번호"로 쓰고 있다.)

정상적으로는 이 둘이 항상 같아야 하는데, 관리자 화면에서 기존 직원의 비밀번호를
재설정하는 기능이 1)번만 갱신하고 2)번은 갱신하지 않는 버그가 있는 것으로 확인됨
(index.html의 _acctPwChanged 관련 로직이 추적만 하고 실제로 반영되지 않음).

이 어긋남은 평소엔 잘 드러나지 않는다 - 브라우저가 이미 로그인 세션을 캐시해두고
있으면 매번 비밀번호를 다시 검증하지 않기 때문이다. 하지만 세션이 없는 PC(또는
시크릿 모드)에서 새로 로그인을 시도하면, 실제 입력한 비밀번호가 맞아도 Firebase Auth
서버 쪽에는 예전 비밀번호가 남아있어 "성명 또는 비밀번호가 올바르지 않습니다"가 뜬다.

이 스크립트가 하는 일
--------------------
실제 평문 비밀번호를 전혀 몰라도, RTDB에 저장된 현재 pwHash 값을 그대로 Firebase Auth의
비밀번호로 다시 설정해주기만 하면 위 둘을 일치시킬 수 있다. 계정이 Firebase Auth에
아직 없는 경우(예전에 한 번도 로그인 안 해본 계정)는 새로 만들어준다.

멱등성: 이미 일치하는 계정도 같은 값으로 다시 쓰는 것뿐이라 여러 번 실행해도 안전하다.
"""
import hashlib
import json
import os
import sys

import firebase_admin
from firebase_admin import auth as fb_auth
from firebase_admin import credentials, db

DATABASE_URL = "https://chjk-scheduler-default-rtdb.asia-southeast1.firebasedatabase.app"
AUTH_BASE = "teamdata_test"
ACCOUNTS_PATH = f"{AUTH_BASE}_accounts"
AUTHORIZED_PATH = f"{AUTH_BASE}_authorized"
AUTHMAP_PATH = f"{AUTH_BASE}_authmap"


def _synth_email(account_id: str) -> str:
    # index.html의 _synthEmail(id)와 완전히 동일한 계산식
    # (crypto.subtle.digest('SHA-256', ...) == hashlib.sha256(...))
    h = hashlib.sha256(str(account_id).encode("utf-8")).hexdigest()
    return f"u{h[:32]}@chjk-scheduler.web.app"


def main():
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not raw:
        print("[오류] FIREBASE_SERVICE_ACCOUNT_JSON 환경변수(시크릿)가 없습니다.", file=sys.stderr)
        sys.exit(1)

    cred = credentials.Certificate(json.loads(raw))
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

    accounts = db.reference(ACCOUNTS_PATH).get() or {}
    print(f"총 {len(accounts)}개 계정 확인됨. 재동기화를 시작합니다.")

    synced, created, skipped, failed = 0, 0, 0, 0
    for account_id, info in accounts.items():
        if not isinstance(info, dict):
            continue
        pw_hash = info.get("pwHash")
        if not pw_hash:
            print(f"  [건너뜀] {account_id}: pwHash 없음")
            skipped += 1
            continue

        email = _synth_email(account_id)
        try:
            user = fb_auth.get_user_by_email(email)
            fb_auth.update_user(user.uid, password=pw_hash)
            print(f"  [재동기화 완료] {account_id}")
            synced += 1
        except fb_auth.UserNotFoundError:
            try:
                new_user = fb_auth.create_user(email=email, password=pw_hash)
                db.reference(f"{AUTHORIZED_PATH}/{new_user.uid}").set(True)
                db.reference(f"{AUTHMAP_PATH}/{account_id}").set(new_user.uid)
                print(f"  [신규 생성] {account_id}: Firebase Auth 계정이 없어 새로 만들었습니다.")
                created += 1
            except Exception as e:
                print(f"  [실패] {account_id}: 신규 생성 중 오류 - {e}")
                failed += 1
        except Exception as e:
            print(f"  [실패] {account_id}: {e}")
            failed += 1

    print(
        f"\n완료: 재동기화 {synced}건, 신규 생성 {created}건, "
        f"건너뜀 {skipped}건, 실패 {failed}건"
    )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
