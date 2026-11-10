# ☕ 나만의 카페 노트 웹서비스
# 이 파일 하나만 실행하면 내 컴퓨터에 작은 카페 홈페이지가 열려요!
# 첫 화면에는 지역 폴더들이 동그랗게 놓여 있고, 폴더를 누르면 그 지역의 지도와 카페 목록이 나와요.
# 화면 생김새(HTML)는 templates 폴더에, 꾸밈(CSS)은 static/style.css에 따로 나눠 두었어요.

import csv  # csv는 "엑셀처럼 칸이 나뉜 글 파일"을 읽는 도구예요.
import json  # json은 내가 쓴 메모를 파일에 저장하고 다시 꺼내는 도구예요.
import math  # math는 별 모양이나 동그라미 자리를 계산할 때 쓰는 도구예요.
import os  # os는 컴퓨터(서버)에 적어둔 설정값(환경 변수)을 읽는 도구예요.
import secrets  # secrets는 아무도 맞힐 수 없는 무작위 열쇠를 만드는 도구예요.
import time  # time은 "잠깐 기다려!"를 할 수 있는 도구예요.
from datetime import date, timedelta  # date는 "오늘이 며칠인지", timedelta는 "며칠 동안"을 나타내는 도구예요.
from functools import wraps  # wraps는 함수에 "주인만 들어올 수 있어요" 같은 검사를 덧붙일 때 쓰는 도구예요.
from pathlib import Path  # Path는 "파일이 어디에 있는지" 주소를 알려주는 도구예요.

import shutil  # shutil은 파일을 통째로 복사하는 도구예요.

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, session, url_for  # Flask는 웹사이트를 만들어 주는 마법 상자예요.
# render_template는 templates 폴더에 있는 화면 파일(.html)을 꺼내서 내용을 채워 주는 도구예요.
# session은 "이 사람은 로그인했어요"를 브라우저에 기억시켜 두는 주머니, flash는 화면 위에 한 번 띄우는 안내 쪽지예요.
# send_from_directory는 정해진 폴더 안의 파일(내가 올린 사진)만 안전하게 꺼내 보여주는 도구예요.
from werkzeug.security import check_password_hash  # 적은 비밀번호가 저장해 둔 비밀번호(해시)와 맞는지 확인하는 도구예요.

BASE_DIR = Path(__file__).parent  # 지금 이 app.py 파일이 들어있는 폴더를 기억해요.

# ===== "코드"와 "기록"을 나눠요 =====
# 코드(app.py, 화면, 꾸밈, AI 사진, 처음 카페 24곳)는 깃허브로 관리하고,
# 기록(등록한 카페, 메모, 내가 올린 사진, 비밀번호)은 DATA_DIR 폴더에만 저장해요. 이 폴더는 깃허브에 올라가지 않아요.
# 내 컴퓨터에서는 cafe-note/data 폴더를 쓰고, 서버에서는 CAFE_DATA_DIR 설정으로 다른 폴더(예: /home/아이디/cafe-data)를 써요.
DATA_DIR = Path(os.environ.get("CAFE_DATA_DIR", BASE_DIR / "data"))  # 기록을 저장하는 폴더예요.
SEED_FILE = BASE_DIR / "seed" / "cafes.csv"  # 처음 시작할 때 쓰는 카페 24곳 목록이에요. (깃허브에 올라가요)
CAFE_FILE = DATA_DIR / "cafes.csv"  # 지금까지 기록한 카페 목록이에요.
NOTE_FILE = DATA_DIR / "notes.json"  # 내가 쓴 메모를 저장할 파일이에요.
OWNER_FILE = DATA_DIR / "owner.json"  # 주인 비밀번호(해시)와 비밀 열쇠가 저장된 파일이에요. (set_password.py로 만들어요)
UPLOAD_DIR = DATA_DIR / "photos"  # 내가 올린 카페 사진을 저장하는 폴더예요.

DATA_DIR.mkdir(parents=True, exist_ok=True)  # 기록 폴더가 없으면 만들어요.
if not CAFE_FILE.exists():  # 기록한 카페 목록이 아직 없으면 (처음 켰을 때)
    shutil.copy(SEED_FILE, CAFE_FILE)  # 처음 카페 24곳 목록을 복사해서 시작해요.


def load_owner():  # 주인 정보 파일을 읽는 함수예요.
    if not OWNER_FILE.exists():  # 아직 비밀번호를 정하지 않았으면
        return None  # "주인 정보 없음"을 돌려줘요.
    return json.loads(OWNER_FILE.read_text(encoding="utf-8"))  # 파일을 읽어서 돌려줘요.


app = Flask(__name__)  # 우리만의 웹사이트(앱)를 하나 만들어요.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 한 번에 올릴 수 있는 사진 크기를 10MB까지로 정해요. (너무 큰 파일 막기)
app.config["SECRET_KEY"] = (load_owner() or {}).get("secret_key") or secrets.token_hex(32)  # 로그인 기억 주머니(session)를 잠그는 비밀 열쇠예요. 파일에 없으면 임시 열쇠를 만들어요.
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # 다른 사이트가 몰래 우리 사이트에 "등록해!"라고 보내는 걸 막아줘요.
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("CAFE_HTTPS") == "1"  # 배포해서 https 주소를 쓸 때는 로그인 기억을 안전한 연결로만 주고받아요.
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)  # 한 번 로그인하면 30일 동안 기억해요.

IMAGE_DIR = BASE_DIR / "static" / "cafes"  # AI가 그린 대표 메뉴 사진들이 들어있는 폴더예요. (코드와 함께 깃허브에 올라가요)
PHOTO_TYPES = (".jpg", ".jpeg", ".png", ".webp")  # 사진으로 받아줄 파일 종류예요.

NAVER_MAP_KEY = "i6m2gj348z"  # 네이버 지도를 쓰기 위한 열쇠(Client ID)예요. 네이버 클라우드에서 받은 값이에요.
ALL = "전체"  # "모든 지역"을 뜻하는 특별한 이름이에요.

AREA_POSITIONS = {  # 지역마다 지도에 핀을 꽂을 위치(위도, 경도)를 적어둔 사전이에요.
    "합정": (37.5495, 126.9139),  # 서울 합정역 근처
    "강남": (37.4979, 127.0276),  # 서울 강남역 근처
    "성수": (37.5446, 127.0559),  # 서울 성수역 근처
    "둔산": (36.3518, 127.3785),  # 대전 둔산동 근처
    "동성로": (35.8690, 128.5958),  # 대구 동성로 근처
    "해운대": (35.1587, 129.1604),  # 부산 해운대 해수욕장 근처
}  # 사전 끝!

AREA_ENGLISH = {  # 폴더 이름표에 같이 적을 영어 이름이에요. (레퍼런스처럼 "city_helsinki" 느낌을 내요)
    "합정": "hapjeong", "강남": "gangnam", "성수": "seongsu",
    "둔산": "dunsan", "동성로": "dongseongro", "해운대": "haeundae",
}  # 사전 끝!

FOLDER_SLOTS = [  # 첫 화면에서 지역 폴더를 놓을 자리(가로 %, 세로 %)예요. 가운데를 빙 둘러싸요. (7번째 폴더부터는 아래 "새로 생긴 폴더" 영역에 놓여요)
    (31, 14), (77, 16),  # 위쪽 왼쪽, 위쪽 오른쪽
    (13, 48), (87, 52),  # 가운데 왼쪽, 가운데 오른쪽
    (22, 85), (79, 87),  # 아래쪽 왼쪽, 아래쪽 오른쪽
]  # 자리 끝!
FOLDER_COLORS = ["pink", "yellow", "blue"]  # 폴더 색깔을 분홍 → 노랑 → 파랑 순서로 돌려가며 칠해요.

BURST = " ".join(  # 가운데 사진 뒤에 붙일 "반짝 별" 모양의 꼭짓점들을 계산해요.
    f"{50 + (50 if i % 2 == 0 else 32) * math.cos(math.pi * i / 10):.1f},"  # 바깥 점과 안쪽 점을 번갈아 찍어서
    f"{50 + (50 if i % 2 == 0 else 32) * math.sin(math.pi * i / 10):.1f}"  # 뾰족뾰족한 별을 만들어요.
    for i in range(20)  # 꼭짓점 20개 (뾰족한 끝 10개)
)  # 별 완성!


def find_photo(cafe_id):  # 카페 번호로 사진 파일을 찾아주는 함수예요.
    for ext in PHOTO_TYPES:  # jpg, jpeg, png, webp를 차례로 확인해서
        if (UPLOAD_DIR / f"{cafe_id}{ext}").exists():  # 내가 올린 사진이 있으면 그걸 먼저 써요.
            return ("upload", f"{cafe_id}{ext}")  # "내가 올린 사진 폴더의 25.jpg"라는 뜻이에요.
        if (IMAGE_DIR / f"{cafe_id}{ext}").exists():  # 없으면 AI가 그린 사진을 찾아봐요.
            return ("static", f"cafes/{cafe_id}{ext}")  # "static 폴더의 cafes/3.jpg"라는 뜻이에요.
    return None  # 사진이 하나도 없으면 "없음"을 돌려줘요.


@app.template_global()  # 아래 함수를 화면 파일(템플릿)에서도 쓸 수 있게 해요.
def photo_url(image):  # find_photo가 알려준 사진 정보를 실제 인터넷 주소로 바꿔주는 함수예요.
    where, name = image  # 어느 폴더(upload/static)의 어떤 파일인지 꺼내요.
    if where == "upload":  # 내가 올린 사진이면
        return url_for("uploaded_photo", filename=name)  # /photos/25.jpg 같은 주소를 만들어요.
    return url_for("static", filename=name)  # AI 사진이면 /static/cafes/3.jpg 같은 주소를 만들어요.


def area_label(area):  # 폴더 이름표를 만드는 함수예요. 예: "합정" → "합정_hapjeong"
    eng = AREA_ENGLISH.get(area)  # 영어 이름을 찾아봐요.
    return f"{area}_{eng}" if eng else area  # 영어 이름이 있으면 붙이고, 새로 생긴 지역이면 한글 이름만 써요.


def load_cafes():  # 카페 목록을 파일에서 읽어오는 함수(심부름꾼)를 만들어요.
    cafes = []  # 카페들을 담을 빈 바구니를 준비해요.
    with open(CAFE_FILE, encoding="utf-8-sig", newline="") as f:  # 카페 파일을 열어요. (utf-8-sig는 한글이 안 깨지게 해줘요)
        for row in csv.DictReader(f):  # 파일을 한 줄씩 읽어서, 칸 이름(이름, 지역...)으로 꺼낼 수 있게 해요.
            price = row["가격"].strip()  # 가격 칸을 꺼내고 양쪽 빈칸을 지워요.
            rating = row["평점"].strip()  # 평점 칸을 꺼내고 양쪽 빈칸을 지워요.
            cafes.append({  # 카페 하나의 정보를 정리해서 바구니에 넣어요.
                "id": int(row["id"]),  # 카페 번호예요. 글자를 숫자로 바꿔요.
                "name": row["이름"],  # 카페 이름이에요.
                "area": row["지역"],  # 카페가 있는 동네예요.
                "menu": row["대표메뉴"],  # 그 카페에서 제일 유명한 메뉴예요.
                "price": int(price) if price else None,  # 가격이 적혀 있으면 숫자로, 비어 있으면 "없음(None)"으로 해요.
                "outlet": row["콘센트"].strip() or "모름",  # 콘센트가 있는지 적어요. 비어 있으면 "모름"이라고 해요.
                "open": row["여는시간"],  # 문 여는 시간이에요.
                "close": row["닫는시간"],  # 문 닫는 시간이에요.
                "rating": float(rating) if rating else None,  # 평점이 있으면 소수 숫자로, 없으면 "없음(None)"으로 해요.
                "image": find_photo(row["id"]),  # 카페 사진 파일이 있으면 그 이름을, 없으면 "없음"을 적어요.
            })  # 카페 하나 정리 끝!
    return cafes  # 다 채운 바구니를 돌려줘요.


def load_notes():  # 내가 쓴 메모들을 파일에서 꺼내오는 함수예요.
    if not NOTE_FILE.exists():  # 만약 메모 파일이 아직 없다면(처음 켰을 때),
        return {}  # 빈 메모장을 돌려줘요.
    return json.loads(NOTE_FILE.read_text(encoding="utf-8"))  # 메모 파일을 읽어서 돌려줘요.


def save_notes(notes):  # 메모들을 파일에 저장하는 함수예요.
    NOTE_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")  # 한글 그대로 예쁘게 줄 맞춰 저장해요.


def add_cafe(form):  # 새 카페 한 줄을 cafes.csv 맨 아래에 적어 넣는 함수예요.
    new_id = max((c["id"] for c in load_cafes()), default=0) + 1  # 지금 가장 큰 번호보다 1 큰 번호를 새 카페에게 줘요.
    if not CAFE_FILE.read_bytes().endswith(b"\n"):  # 파일 마지막 줄이 줄바꿈으로 끝나지 않으면
        with open(CAFE_FILE, "a", encoding="utf-8") as f:  # 파일을 "이어 쓰기(a)"로 열어서
            f.write("\n")  # 줄바꿈을 하나 넣어요. (안 그러면 새 카페가 마지막 카페 줄에 붙어버려요)
    with open(CAFE_FILE, "a", encoding="utf-8", newline="") as f:  # 다시 "이어 쓰기"로 열어요.
        csv.writer(f).writerow([  # 칸 순서에 맞춰 한 줄을 적어요. (id,이름,지역,대표메뉴,가격,콘센트,여는시간,닫는시간,평점)
            new_id, form["name"], form["area"], form["menu"], form["price"],
            form["outlet"], form["open"], form["close"], form["rating"],
        ])  # 한 줄 적기 끝!
    return new_id  # 새 카페 번호를 돌려줘요.


def area_order(cafes):  # 지역 이름들을 정해진 순서로 줄 세우는 함수예요. (홈 화면과 지역 화면의 폴더 색을 똑같이 맞추려고요)
    return sorted({c["area"] for c in cafes}, key=lambda a: (a not in AREA_ENGLISH, a))  # 원래 있던 6곳을 먼저, 새로 생긴 지역은 뒤에 가나다순으로 놓아요.


def is_owner():  # 지금 보고 있는 사람이 주인(로그인한 사람)인지 알려주는 함수예요.
    return session.get("owner") is True  # 로그인 기억 주머니에 "주인이에요" 표시가 있으면 True예요.


def owner_required(view):  # "이 화면은 주인만 들어올 수 있어요" 검사를 붙여주는 함수예요. (@owner_required 라고 붙여서 써요)
    @wraps(view)  # 원래 화면 함수의 이름표를 그대로 지켜줘요.
    def checked(*args, **kwargs):  # 화면에 들어오기 전에 먼저 이 검사를 해요.
        if not is_owner():  # 주인이 아니면
            flash("카페 등록과 메모 쓰기는 주인만 할 수 있어요. 비밀번호를 넣어 주세요.")  # 안내 쪽지를 남기고
            return redirect(url_for("login", next=request.path))  # 로그인 화면으로 보내요. (로그인하면 원래 가려던 곳으로 돌아와요)
        return view(*args, **kwargs)  # 주인이면 원래 화면을 보여줘요.
    return checked  # 검사가 붙은 새 함수를 돌려줘요.


def safe_next(target):  # 로그인 뒤 돌아갈 주소가 "우리 사이트 안"인지 확인하는 함수예요.
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:  # "/"로 시작하는 우리 사이트 주소만
        return target  # 그 주소로 돌아가요.
    return url_for("home")  # 이상한 주소(다른 사이트)면 홈으로 보내요. (나쁜 사이트로 끌려가는 걸 막아요)


@app.context_processor  # 여기서 돌려주는 값들은 "모든 화면"에서 쓸 수 있어요. (base.html의 바닥 글씨, 로그인 표시에 쓰여요)
def common_values():  # 모든 화면에 공통으로 넘길 재료를 만드는 함수예요.
    return {"year": date.today().year, "cafe_count": len(load_cafes()), "is_owner": is_owner()}  # 올해, 카페 수, 주인인지


@app.route("/login", methods=["GET", "POST"])  # "/login"으로 들어오면 아래 함수가 일해요.
def login():  # 주인 로그인 화면이에요.
    next_url = safe_next(request.values.get("next"))  # 로그인 뒤에 돌아갈 주소를 꺼내요.
    owner = load_owner()  # 저장해 둔 주인 정보를 읽어요.
    error = ""  # 틀렸을 때 보여줄 말이에요. 처음엔 비어 있어요.

    if request.method == "POST":  # "로그인" 버튼을 눌렀다면,
        if owner is None:  # 아직 비밀번호를 정하지 않았으면
            error = "아직 비밀번호가 없어요. 터미널에서 python set_password.py 를 먼저 실행해 주세요."  # 방법을 알려줘요.
        elif check_password_hash(owner["password_hash"], request.form.get("password", "")):  # 비밀번호가 맞으면
            session.clear()  # 예전 기억은 깨끗이 지우고
            session["owner"] = True  # "주인이에요" 표시를 넣어요.
            session.permanent = True  # 브라우저를 껐다 켜도 30일 동안 기억해요.
            flash("로그인했어요. 이제 카페를 등록하고 메모를 쓸 수 있어요.")  # 안내 쪽지를 남기고
            return redirect(next_url)  # 원래 가려던 곳으로 보내요.
        else:  # 비밀번호가 틀리면
            time.sleep(1)  # 1초 기다리게 해요. (나쁜 사람이 비밀번호를 빠르게 계속 찍어보는 걸 느리게 만들어요)
            error = "비밀번호가 맞지 않아요."  # 틀렸다고 알려줘요.

    return render_template("login.html", error=error, next=next_url, ready=owner is not None)  # 로그인 화면을 보여줘요.


@app.route("/logout", methods=["POST"])  # "로그아웃" 버튼을 누르면 아래 함수가 일해요.
def logout():  # 로그아웃하는 함수예요.
    session.clear()  # 로그인 기억을 모두 지워요.
    flash("로그아웃했어요.")  # 안내 쪽지를 남기고
    return redirect(url_for("home"))  # 홈으로 보내요.


@app.route("/")  # 누군가 홈페이지 첫 화면("/")에 들어오면 아래 함수가 일해요.
def home():  # 첫 화면(지역 폴더판)을 만들어 주는 함수예요.
    cafes = load_cafes()  # 카페 목록을 파일에서 가져와요.
    areas = area_order(cafes)  # 지역 이름들을 정해진 순서로 모아요.

    folders = []  # 화면에 놓을 폴더들을 담을 바구니예요.
    for i, a in enumerate(areas):  # 지역을 하나씩 꺼내면서 번호(i)도 같이 세요.
        x, y = FOLDER_SLOTS[i] if i < len(FOLDER_SLOTS) else (None, None)  # 둘러싼 자리가 남아 있으면 그 자리를, 아니면 "자리 없음"을 적어요.
        folders.append({  # 폴더 하나의 정보를 정리해요.
            "name": a,  # 지역 이름 (주소에 쓰여요)
            "label": area_label(a),  # 이름표 예: "합정_hapjeong"
            "count": sum(1 for c in cafes if c["area"] == a),  # 그 지역 카페 수
            "color": FOLDER_COLORS[i % len(FOLDER_COLORS)],  # 폴더 색깔
            "x": x, "y": y,  # 화면 위 자리
        })  # 폴더 하나 끝!
    ring = folders[:len(FOLDER_SLOTS)]  # 앞의 6개는 가운데를 빙 둘러싸는 폴더예요.
    more = folders[len(FOLDER_SLOTS):]  # 7번째부터는 아래 "새로 생긴 폴더" 영역에 놓을 폴더예요.

    with_photo = [c for c in cafes if c["image"]]  # 사진이 있는 카페만 골라요.
    featured = sorted(with_photo, key=lambda c: c["rating"] or 0, reverse=True)[:3]  # 평점 높은 3곳을 가운데 콜라주에 써요.

    return render_template(  # templates/home.html을 꺼내서 내용을 채워 보여줘요.
        "home.html", ring=ring, more=more, featured=featured, burst=BURST, all_name=ALL,
    )  # 페이지 완성!


@app.route("/about")  # "/about"으로 들어오면 아래 함수가 일해요.
def about():  # 소개 화면을 만들어 주는 함수예요.
    cafes = load_cafes()  # 카페 목록을 가져와요.
    return render_template(  # templates/about.html을 꺼내서 내용을 채워 보여줘요.
        "about.html",
        area_count=len({c["area"] for c in cafes}),  # 지역(폴더)이 몇 개인지
        memo_count=len(load_notes()),  # 메모를 몇 개 남겼는지
    )  # 페이지 완성!


@app.route("/register", methods=["GET", "POST"])  # "/register"로 들어오면 아래 함수가 일해요. (GET=화면 보기, POST=등록하기 버튼)
@owner_required  # 주인만 들어올 수 있어요. 아니면 로그인 화면으로 보내요.
def register():  # 새 카페를 등록하는 화면이에요.
    cafes = load_cafes()  # 지금 있는 카페들을 가져와요.
    areas = area_order(cafes)  # 지역 이름들 (고르기 목록에 보여줘요)
    menus = sorted({c["menu"] for c in cafes})  # 메뉴 이름들 (고르기 목록에 보여줘요)
    form = {"name": "", "area": "", "menu": "", "price": "", "rating": "",
            "open": "10:00", "close": "22:00", "outlet": ""}  # 빈칸들의 처음 값이에요. (시간은 흔한 값으로 미리 채워둬요)
    errors = []  # 잘못 적은 것들을 모을 바구니예요.

    if request.method == "POST":  # "등록하기" 버튼을 눌렀다면,
        form = {k: request.form.get(k, "").strip() for k in form}  # 적은 내용을 칸마다 꺼내고 양쪽 빈칸을 지워요.
        if not form["name"]:  # 이름이 비어 있으면
            errors.append("카페 이름을 적어 주세요.")  # 알려줄 말을 바구니에 넣어요.
        if not form["area"]:  # 지역이 비어 있으면
            errors.append("지역을 고르거나 새로 적어 주세요.")  # 알려줄 말을 바구니에 넣어요.
        elif "/" in form["area"] or form["area"] == ALL:  # 주소를 망가뜨리는 "/"나, 특별한 이름 "전체"는 쓸 수 없어요.
            errors.append(f"지역 이름에는 '/'를 넣을 수 없고, '{ALL}'라는 이름도 쓸 수 없어요.")  # 알려줄 말을 넣어요.
        if not form["menu"]:  # 메뉴가 비어 있으면
            errors.append("대표 메뉴를 적어 주세요.")  # 알려줄 말을 넣어요.
        if form["price"] and not form["price"].isdigit():  # 가격에 숫자가 아닌 글자가 있으면
            errors.append("가격은 숫자만 적어 주세요. (예: 5500)")  # 알려줄 말을 넣어요.
        if form["rating"]:  # 평점을 적었다면
            try:  # 숫자로 바꿔볼게요.
                ok = 0 <= float(form["rating"]) <= 5  # 0부터 5 사이인지 확인해요.
            except ValueError:  # 숫자로 바꿀 수 없으면
                ok = False  # 잘못 적은 거예요.
            if not ok:  # 잘못 적었으면
                errors.append("평점은 0부터 5 사이 숫자로 적어 주세요. (예: 4.5)")  # 알려줄 말을 넣어요.
        if form["outlet"] not in ("", "있음", "없음"):  # 콘센트는 세 가지 중 하나만 돼요.
            form["outlet"] = ""  # 이상한 값이 오면 "모름"으로 바꿔요.
        if any(c["name"] == form["name"] and c["area"] == form["area"] for c in cafes):  # 같은 지역에 같은 이름이 이미 있으면
            errors.append("같은 지역에 같은 이름의 카페가 이미 있어요.")  # 알려줄 말을 넣어요.

        photo = request.files.get("photo")  # 올린 사진 파일을 꺼내요. (안 올렸으면 비어 있어요)
        ext = Path(photo.filename).suffix.lower() if photo and photo.filename else ""  # 파일 이름 끝(.jpg 같은)을 소문자로 꺼내요.
        if ext and ext not in PHOTO_TYPES:  # 사진이 아닌 파일이면
            errors.append("사진은 jpg, png, webp 파일만 올릴 수 있어요.")  # 알려줄 말을 넣어요.

        if not errors:  # 잘못 적은 게 하나도 없으면,
            new_id = add_cafe(form)  # cafes.csv에 새 카페를 적고 번호를 받아요.
            if ext:  # 사진도 올렸다면
                UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # 내 사진 폴더가 없으면 만들고,
                photo.save(UPLOAD_DIR / f"{new_id}{ext}")  # "카페번호.jpg" 같은 이름으로 기록 폴더에 저장해요.
            return redirect(url_for("detail", cafe_id=new_id, new=1))  # 새 카페의 상세 화면으로 이동해요. (new=1은 "방금 등록했어요" 표시)

    return render_template("register.html", form=form, errors=errors, areas=areas, menus=menus)  # 등록 화면을 보여줘요. (틀렸으면 적은 내용이 그대로 남아 있어요)


@app.route("/photos/<path:filename>")  # "/photos/25.jpg"처럼 내가 올린 사진 주소로 들어오면 아래 함수가 일해요.
def uploaded_photo(filename):  # 기록 폴더에 있는 내 사진을 보여주는 함수예요.
    return send_from_directory(UPLOAD_DIR, filename)  # photos 폴더 "안에 있는" 파일만 보여줘요. (../ 같은 꼼수로 다른 파일을 못 꺼내요)


@app.route("/area/<area>")  # "/area/합정"처럼 폴더를 눌러 들어오면 아래 함수가 일해요.
def area_page(area):  # 지역 화면(지도 + 카페 목록)을 만들어 주는 함수예요.
    all_cafes = load_cafes()  # 카페 목록을 파일에서 가져와요.
    areas = area_order(all_cafes)  # 홈 화면과 같은 순서로 지역 이름들을 모아요. (폴더 색을 맞추려고요)
    if area != ALL and area not in areas:  # 없는 지역 이름으로 들어오면
        abort(404)  # "못 찾음" 화면을 보여줘요.

    q = request.args.get("q", "").strip()  # 검색창에 쓴 글자를 가져와요. 없으면 빈 글자예요.
    outlet = request.args.get("outlet", "")  # 콘센트 조건을 가져와요.
    sort = request.args.get("sort", "id")  # 어떤 순서로 줄 세울지 가져와요. 기본은 번호순이에요.

    pins = {  # 지도에 꽂을 핀 정보를 만들어요.
        a: {"pos": AREA_POSITIONS[a], "count": sum(1 for c in all_cafes if c["area"] == a)}  # 지역마다 위치와 카페 수를 적어요.
        for a in areas if a in AREA_POSITIONS  # 위치를 알고 있는 지역만 핀을 꽂아요. (새로 생긴 지역은 위치를 몰라서 핀이 없어요)
    }  # 핀 정보 완성!

    cafes = all_cafes if area == ALL else [c for c in all_cafes if c["area"] == area]  # 이 폴더(지역)의 카페만 남겨요.
    total = len(cafes)  # 검색하기 전, 이 지역 카페가 모두 몇 곳인지 기억해요.
    if q:  # 검색어가 있다면,
        cafes = [c for c in cafes if q in c["name"] or q in c["menu"]]  # 이름이나 메뉴에 검색어가 들어간 카페만 남겨요.
    if outlet:  # 콘센트 조건을 골랐다면,
        cafes = [c for c in cafes if c["outlet"] == outlet]  # 콘센트가 있는 카페만 남겨요.
    if sort == "rating":  # 평점 높은순을 골랐다면,
        cafes.sort(key=lambda c: c["rating"] or 0, reverse=True)  # 평점이 큰 것부터 줄 세워요. (평점 없으면 0점 취급)
    elif sort == "price":  # 가격 낮은순을 골랐다면,
        cafes.sort(key=lambda c: c["price"] or 999999)  # 싼 것부터 줄 세워요. (가격 모르면 맨 뒤로 보내요)

    color = FOLDER_COLORS[areas.index(area) % len(FOLDER_COLORS)] if area in areas else "lav"  # 첫 화면과 같은 폴더 색을 써요.
    return render_template(  # templates/area.html을 꺼내서 내용을 채워 보여줘요.
        "area.html", area=area, cafes=cafes, total=total, notes=load_notes(),
        pins=pins, map_key=NAVER_MAP_KEY, color=color,
        folder_label=area_label(area) if area != ALL else f"{ALL}_all",  # 제목 줄에 보일 이름표
        q=q, outlet=outlet, sort=sort,  # 내가 고른 검색 조건도 넘겨서, 화면에 그대로 남아 있게 해요.
    )  # 페이지 완성!


@app.route("/cafe/<int:cafe_id>", methods=["GET", "POST"])  # "/cafe/3"처럼 카페 번호로 들어오면 아래 함수가 일해요.
def detail(cafe_id):  # 카페 하나의 자세한 정보와 메모를 보여주는 함수예요.
    cafe = next((c for c in load_cafes() if c["id"] == cafe_id), None)  # 번호가 똑같은 카페를 찾아요. 없으면 None이에요.
    if cafe is None:  # 그런 번호의 카페가 없다면,
        abort(404)  # "못 찾음" 화면을 보여줘요. (404는 "못 찾음"이라는 뜻의 번호예요)

    notes = load_notes()  # 지금까지 쓴 메모들을 꺼내요.
    key = str(cafe_id)  # 메모장에서 카페를 찾을 때 쓸 이름표예요. (숫자를 글자로 바꿔요)

    if request.method == "POST":  # "저장하기" 버튼을 눌렀다면,
        if not is_owner():  # 주인이 아니면 메모를 고칠 수 없어요.
            abort(403)  # "들어올 수 없어요" 화면을 보여줘요. (403은 "허락 안 됨"이라는 뜻의 번호예요)
        memo = request.form.get("memo", "").strip()  # 내가 쓴 메모 글을 가져와요.
        if memo:  # 메모에 글자가 있으면,
            notes[key] = memo  # 메모장에 이 카페의 메모로 적어요.
        else:  # 메모를 다 지웠으면,
            notes.pop(key, None)  # 메모장에서 이 카페 메모를 지워요.
        save_notes(notes)  # 바뀐 메모장을 파일에 저장해요.
        return redirect(url_for("detail", cafe_id=cafe_id))  # 같은 페이지를 새로 열어서 저장된 걸 보여줘요.

    return render_template(  # templates/cafe.html을 꺼내서 내용을 채워 보여줘요.
        "cafe.html", cafe=cafe, memo=notes.get(key, ""),
        just_added=request.args.get("new") == "1",  # 방금 등록한 카페면 "등록했어요!" 알림을 보여줘요.
    )  # 페이지 완성!


if __name__ == "__main__":  # "python app.py"로 내 컴퓨터에서 직접 실행했을 때만 아래를 해요.
    # 배포한 서버(PythonAnywhere 등)는 이 줄을 실행하지 않고 app만 가져다 써요. 그래서 debug는 내 컴퓨터에서만 켜져요.
    # 내 컴퓨터에서도 debug를 끄고 싶으면 CAFE_DEBUG=0 으로 설정하고 실행하면 돼요.
    app.run(debug=os.environ.get("CAFE_DEBUG", "1") == "1")  # 웹사이트를 켜요! (debug는 코드를 고치면 자동으로 다시 켜주는 기능이에요)
