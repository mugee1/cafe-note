# 🎨 대표 메뉴 사진 만들기 프로그램
# AI 그림 사이트(Pollinations.ai)에 "손님이 휴대폰으로 찍은 것 같은 메뉴 사진 그려줘!" 하고 부탁해서
# 카페마다 대표 메뉴 사진 한 장씩 static/cafes/ 폴더에 저장해요. (한 번만 실행하면 돼요)

import csv  # csv는 칸이 나뉜 글 파일(cafes.csv)을 읽는 도구예요.
import time  # time은 "잠깐 기다려!"를 할 수 있는 도구예요.
import urllib.parse  # 문장을 인터넷 주소에 넣을 수 있는 모양으로 바꿔주는 도구예요.
import urllib.request  # 인터넷에서 파일을 내려받는 도구예요.
from pathlib import Path  # 파일이 어디 있는지 주소를 다루는 도구예요.

BASE_DIR = Path(__file__).parent  # 이 파일이 들어있는 폴더예요.
CAFE_FILE = BASE_DIR / "seed" / "cafes.csv"  # 처음 카페 24곳 목록이에요. (AI 사진은 이 24곳만 만들어요. 새로 등록한 카페는 내가 찍은 사진을 올려요)
IMAGE_DIR = BASE_DIR / "static" / "cafes"  # 사진을 저장할 폴더의 위치예요.

MENU_EN = {  # AI는 영어를 더 잘 알아들어서, 메뉴 이름을 영어로 바꿔줄 사전이에요.
    "크로플": "golden croffle with syrup",  # 크로플 → 크로와상 와플
    "라떼": "latte with latte art",  # 라떼 → 하트 그림이 있는 라떼
    "소금빵": "salt butter rolls",  # 소금빵 → 소금 버터빵
    "핸드드립": "pour-over hand drip coffee",  # 핸드드립 → 손으로 내린 커피
    "말차라떼": "green matcha latte",  # 말차라떼 → 초록색 녹차 라떼
    "아메리카노": "iced americano",  # 아메리카노 → 시원한 아메리카노
}  # 사전 끝!

MOOD_EN = {  # 카페 이름을 보고, 사진 뒤쪽에 흐릿하게 보일 카페 분위기를 영어로 적어둔 사전이에요.
    "모퉁이 커피": "small corner cafe on a street",  # 길모퉁이에 있는 작은 카페
    "오늘의 원두": "modern specialty coffee bar with coffee beans",  # 원두가 가득한 세련된 카페
    "창가 자리": "seat by a big window with ocean view",  # 바다가 보이는 창가 자리
    "빵굽는 오후": "bakery cafe in afternoon sunlight",  # 오후 햇살이 드는 빵집 카페
    "느린 하루": "calm slow-living cafe with soft light",  # 느긋하고 조용한 카페
    "초록 잔": "cafe full of green plants",  # 초록 식물이 가득한 카페
    "골목 다방": "retro korean dabang in an alley",  # 골목에 있는 옛날 다방
    "라떼 연구소": "minimal white lab-style cafe",  # 실험실처럼 하얗고 깔끔한 카페
    "바닐라 숲": "cafe with wooden forest interior",  # 나무 숲 같은 카페
    "책 읽는 카페": "book cafe with tall bookshelves",  # 책장이 가득한 카페
    "작은 정원": "cafe with a tiny flower garden",  # 작은 꽃밭이 있는 카페
    "새벽 로스터리": "coffee roastery at dawn",  # 새벽의 커피 볶는 가게
    "달 카페": "night cafe with moon-shaped lamps",  # 달 모양 전등이 있는 밤 카페
    "한 잔의 쉼표": "quiet cozy cafe with armchairs",  # 푹신한 의자가 있는 조용한 카페
    "파란 지붕": "cafe with a blue roof by the sea",  # 바닷가의 파란 지붕 카페
    "구름 베이커리": "white fluffy cloud-themed bakery",  # 구름처럼 하얀 빵집
    "말차 하우스": "japanese style tea house cafe",  # 일본식 차 가게 같은 카페
    "따뜻한 머그": "warm cafe with handmade mugs on shelves",  # 손으로 만든 컵이 진열된 카페
    "노을 테라스": "rooftop terrace cafe at sunset",  # 노을 지는 옥상 테라스 카페
    "별빛 다방": "cafe with twinkling string lights at night",  # 반짝이 전구가 달린 밤 카페
    "소금 빵집": "seaside bakery with bread display",  # 바닷가의 빵집
    "카페 도서관": "library-like cafe with long wooden tables",  # 도서관 같은 카페
    "흰 고양이 커피": "cafe with a white cat sleeping on a chair",  # 흰 고양이가 자는 카페
    "둥근 테이블": "cafe with round wooden tables",  # 동그란 나무 탁자가 있는 카페
}  # 사전 끝!


def make_prompt(cafe):  # 카페 하나를 보고 AI에게 보낼 "그림 주문서"를 만드는 함수예요.
    mood = MOOD_EN.get(cafe["이름"], "cozy cafe")  # 카페 이름에 맞는 분위기를 찾아요. 없으면 "아늑한 카페"로 해요.
    menu = MENU_EN.get(cafe["대표메뉴"], "coffee")  # 대표 메뉴를 영어로 바꿔요. 없으면 "커피"로 해요.
    return (  # 주문서 문장을 완성해요. (괄호 안의 글들이 한 문장으로 이어져요)
        f"casual smartphone photo taken by a customer, close-up of {menu} on a cafe table, "  # 손님이 폰으로 메뉴를 가까이 찍은 사진
        f"slightly tilted angle, {mood} blurred in the background, "  # 살짝 기울어진 각도, 뒤에는 카페 분위기가 흐릿하게
        "natural window light, everyday instagram food snapshot, realistic"  # 창문 빛, 인스타에 올리는 일상 사진 느낌
    )  # 주문서 완성!


def download(cafe):  # 카페 하나의 사진을 AI에게 받아오는 함수예요.
    path = IMAGE_DIR / f"{cafe['id']}.jpg"  # 사진 파일 이름은 "카페번호.jpg"로 해요. (예: 3.jpg)
    if path.exists():  # 이미 사진이 있으면,
        print(f"⏭️  {cafe['이름']}: 이미 사진이 있어서 건너뛰어요")  # 건너뛴다고 알려주고,
        return False  # 여기서 끝내요. ("새로 안 받았어요"라는 뜻으로 False를 돌려줘요) (다시 만들고 싶으면 그 사진 파일을 지우면 돼요)
    prompt = urllib.parse.quote(make_prompt(cafe))  # 주문서 문장을 인터넷 주소에 넣을 수 있게 바꿔요.
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=640&height=480&seed={cafe['id']}&nologo=true"  # AI 그림 사이트 주소를 만들어요.
    for attempt in range(5):  # 실패할 수도 있으니 최대 5번까지 시도해요.
        try:  # 한번 해볼게요!
            with urllib.request.urlopen(url, timeout=120) as res:  # 사이트에 그림을 부탁하고 최대 2분 기다려요.
                path.write_bytes(res.read())  # 받은 그림을 파일로 저장해요.
            print(f"✅ {cafe['이름']}: 사진 저장 완료!")  # 성공했다고 알려줘요.
            return True  # 성공했으니 끝! ("새로 받았어요"라는 뜻으로 True를 돌려줘요)
        except Exception as e:  # 만약 문제가 생기면,
            print(f"⚠️  {cafe['이름']}: 실패({e}), 30초 뒤 다시 해볼게요")  # 무슨 문제인지 알려주고,
            time.sleep(30)  # 무료 사이트는 너무 자주 부탁하면 거절해요(402 오류). 30초 푹 쉬었다가 다시 해요.
    print(f"❌ {cafe['이름']}: 5번 다 실패했어요. 나중에 다시 실행해 주세요")  # 5번 다 실패했다고 알려줘요.
    return True  # 사이트에 부탁은 했으니, 다음 카페 전에 쉬도록 True를 돌려줘요.


if __name__ == "__main__":  # 이 파일을 직접 실행했을 때만 아래를 해요.
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)  # 사진 폴더가 없으면 새로 만들어요.
    with open(CAFE_FILE, encoding="utf-8-sig", newline="") as f:  # 카페 정보 파일을 열어요.
        cafes = list(csv.DictReader(f))  # 모든 카페를 읽어서 목록으로 만들어요.
    for cafe in cafes:  # 카페를 하나씩 꺼내서,
        if download(cafe):  # 사진을 받아오고, 사이트에 실제로 부탁했다면,
            time.sleep(15)  # 다음 카페를 부탁하기 전에 15초 기다려요. (무료 사이트에 예의를 지켜요!)
    print("🎉 끝! 이제 python app.py 로 웹사이트를 켜 보세요.")  # 다 끝났다고 알려줘요.
