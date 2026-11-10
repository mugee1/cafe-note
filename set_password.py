# 🔑 주인 비밀번호 정하기 프로그램
# 터미널에서 "python set_password.py"로 실행하면 비밀번호를 물어보고,
# 알아볼 수 없게 바꾼 값(해시)만 data/owner.json에 저장해요. 비밀번호 글자 그대로는 어디에도 저장하지 않아요.
# 비밀번호를 바꾸고 싶을 때도 이 프로그램을 다시 실행하면 돼요. (실행 후 웹사이트를 껐다 켜 주세요)

import getpass  # getpass는 비밀번호를 칠 때 화면에 글자가 안 보이게 해주는 도구예요.
import json  # json은 정보를 파일에 저장하는 도구예요.
import os  # os는 컴퓨터(서버)에 적어둔 설정값(환경 변수)을 읽는 도구예요.
import secrets  # secrets는 아무도 맞힐 수 없는 무작위 열쇠를 만드는 도구예요.
from pathlib import Path  # Path는 파일이 어디 있는지 주소를 다루는 도구예요.

from werkzeug.security import generate_password_hash  # 비밀번호를 알아볼 수 없는 값(해시)으로 바꿔주는 도구예요. (Flask와 함께 설치돼요)

# app.py와 똑같은 기록 폴더를 써요. 서버에서는 "CAFE_DATA_DIR=~/cafe-data python set_password.py"처럼 폴더를 알려주고 실행해요.
DATA_DIR = Path(os.environ.get("CAFE_DATA_DIR", Path(__file__).parent / "data"))  # 기록 폴더예요.
OWNER_FILE = DATA_DIR / "owner.json"  # 주인 정보를 저장할 파일 위치예요.

if __name__ == "__main__":  # 이 파일을 직접 실행했을 때만 아래를 해요.
    password = getpass.getpass("새 비밀번호 (8글자 이상, 입력해도 화면에 안 보여요): ")  # 비밀번호를 물어봐요.
    if len(password) < 8:  # 8글자보다 짧으면
        raise SystemExit("❌ 비밀번호는 8글자 이상이어야 해요. 다시 실행해 주세요.")  # 알려주고 끝내요.
    if getpass.getpass("한 번 더 입력해 주세요: ") != password:  # 한 번 더 물어봐서 다르면
        raise SystemExit("❌ 두 비밀번호가 달라요. 다시 실행해 주세요.")  # 알려주고 끝내요.

    old = json.loads(OWNER_FILE.read_text(encoding="utf-8")) if OWNER_FILE.exists() else {}  # 예전에 저장한 정보가 있으면 읽어요.
    owner = {  # 새로 저장할 주인 정보예요.
        "password_hash": generate_password_hash(password),  # 비밀번호를 해시로 바꿔서 넣어요.
        "secret_key": old.get("secret_key") or secrets.token_hex(32),  # 로그인 기억을 잠그는 비밀 열쇠예요. 이미 있으면 그대로 써요.
    }  # 주인 정보 완성!
    OWNER_FILE.parent.mkdir(parents=True, exist_ok=True)  # data 폴더가 없으면 만들어요.
    OWNER_FILE.write_text(json.dumps(owner, indent=2), encoding="utf-8")  # 파일에 저장해요.
    print(f"✅ 비밀번호를 저장했어요! ({OWNER_FILE}) 웹사이트를 껐다 켠 뒤 '관리자 로그인'으로 들어가 보세요.")  # 끝났다고 알려줘요.
    print("⚠️  owner.json 파일은 다른 사람에게 보내거나 공개된 곳(깃허브 등)에 올리지 마세요.")  # 주의할 점을 알려줘요.
