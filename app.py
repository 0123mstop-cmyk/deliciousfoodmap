
import os
import html
from datetime import datetime

import requests
import streamlit as st
import folium
from streamlit_folium import st_folium


# ----------------------------------------
# 1. 기본 페이지 설정
# ----------------------------------------

st.set_page_config(
    page_title="오늘 뭐 먹지?",
    page_icon="🍽️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background-color: #FFF9F3;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
}

.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #29231F;
}

.subtitle {
    color: #81766D;
    font-size: 15px;
}

.hero {
    background: linear-gradient(120deg, #FF824F, #FFAD72);
    padding: 30px;
    border-radius: 22px;
    color: white;
    margin: 22px 0;
}

.hero h2 {
    font-size: 27px;
    margin-bottom: 8px;
}

.hero p {
    margin: 0;
    opacity: .95;
}

.section-title {
    font-size: 21px;
    font-weight: 800;
    color: #302821;
    margin: 15px 0;
}

.restaurant-card {
    background: white;
    padding: 17px;
    border-radius: 17px;
    border: 1px solid #F0E6DC;
    margin-bottom: 12px;
}

.restaurant-name {
    font-size: 18px;
    font-weight: 800;
    color: #302821;
}

.restaurant-address {
    font-size: 13px;
    color: #81766D;
    margin-top: 6px;
}

.ai-label {
    display: inline-block;
    background: #FFF0E5;
    color: #D96C36;
    padding: 5px 9px;
    border-radius: 8px;
    font-size: 11px;
    margin-top: 8px;
}

.photo-placeholder {
    background: #F7EDE4;
    border-radius: 15px;
    height: 190px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #927F70;
    text-align: center;
}

.stButton > button {
    border-radius: 12px;
    border: none;
    background: #FF8657;
    color: white;
    font-weight: 700;
}

.stButton > button:hover {
    background: #E96F43;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------
# 2. 카카오 API 설정
# ----------------------------------------

try:
    KAKAO_KEY = st.secrets["KAKAO_REST_API_KEY"]
except Exception:
    KAKAO_KEY = ""

KAKAO_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


# ----------------------------------------
# 3. AI 음식 이미지 연결
# ----------------------------------------

IMAGE_FOLDER = "images"

FOOD_IMAGES = {
    "chicken": os.path.join(IMAGE_FOLDER, "chicken.jpg"),
    "pizza": os.path.join(IMAGE_FOLDER, "pizza.jpg"),
    "sushi": os.path.join(IMAGE_FOLDER, "sushi.jpg"),
    "noodles": os.path.join(IMAGE_FOLDER, "noodles.jpg"),
    "pork": os.path.join(IMAGE_FOLDER, "pork.jpg"),
    "korean": os.path.join(IMAGE_FOLDER, "korean_food.jpg"),
    "default": os.path.join(IMAGE_FOLDER, "default.jpg")
}


def get_food_category(place):
    """식당 이름과 카테고리를 바탕으로 음식 이미지 종류를 결정한다."""

    name = place.get("place_name", "")
    category = place.get("category_name", "")
    text = (name + " " + category).lower()

    if any(word in text for word in ["치킨", "닭강정", "후라이드"]):
        return "chicken"

    if any(word in text for word in ["피자", "파스타", "이탈리안"]):
        return "pizza"

    if any(word in text for word in ["초밥", "스시", "회", "일식"]):
        return "sushi"

    if any(word in text for word in ["국수", "라면", "우동", "냉면", "면"]):
        return "noodles"

    if any(word in text for word in ["고기", "삼겹살", "갈비", "돈까스", "족발"]):
        return "pork"

    if any(word in text for word in [
        "한식", "백반", "찌개", "김치", "국밥", "비빔밥", "한정식"
    ]):
        return "korean"

    return "default"


def show_food_image(place, height=190):
    """저장된 AI 생성 음식 이미지를 표시한다."""

    category = get_food_category(place)
    image_path = FOOD_IMAGES.get(category, FOOD_IMAGES["default"])

    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.markdown("""
        <div class="photo-placeholder">
            <div style="font-size:45px;">🍽️</div>
            <div style="font-weight:700;">음식 이미지 준비 중</div>
            <div style="font-size:12px;">images 폴더에 사진을 추가해 주세요.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<span class="ai-label">✨ AI 생성 이미지 · 실제 식당 사진 아님</span>',
        unsafe_allow_html=True
    )


# ----------------------------------------
# 4. 카카오 식당 검색 함수
# ----------------------------------------

def search_restaurants(keyword):

    if not KAKAO_KEY:
        st.error(
            "카카오 API 키를 찾을 수 없습니다. "
            ".streamlit/secrets.toml을 확인해 주세요."
        )
        return []

    headers = {
        "Authorization": f"KakaoAK {KAKAO_KEY}"
    }

    params = {
        "query": keyword,
        "size": 15,
        "page": 1
    }

    try:
        response = requests.get(
            KAKAO_URL,
            headers=headers,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        return data.get("documents", [])

    except requests.exceptions.RequestException as error:
        st.error(f"식당 검색 중 오류가 발생했습니다: {error}")
        return []

    except ValueError:
        st.error("검색 결과를 읽을 수 없습니다.")
        return []


# ----------------------------------------
# 5. 상단 화면
# ----------------------------------------

today = datetime.now().strftime("%Y년 %m월 %d일")

st.markdown(
    '<div class="main-title">🍽️ 오늘 뭐 먹지?</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="subtitle">{today} · 오늘의 맛집을 찾아보세요!</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="hero">
    <h2>오늘은 어떤 음식이 끌리나요? 😋</h2>
    <p>먹고 싶은 음식을 검색하면 주변 식당을 찾아드릴게요.</p>
</div>
""", unsafe_allow_html=True)


# ----------------------------------------
# 6. 검색 영역
# ----------------------------------------

st.markdown(
    '<div class="section-title">🔎 맛집 검색하기</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns([5, 1])

with col1:
    keyword = st.text_input(
        "검색어",
        placeholder="예: 강남역 초밥, 수원역 돈까스",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button(
        "검색하기",
        use_container_width=True
    )


# ----------------------------------------
# 7. 검색 결과 저장
# ----------------------------------------

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

if search_button:
    if keyword.strip():
        with st.spinner("맛집을 찾고 있어요... 🍳"):
            st.session_state.restaurants = search_restaurants(
                keyword.strip()
            )
    else:
        st.warning("검색어를 입력해 주세요.")


# ----------------------------------------
# 8. 검색 결과 화면
# ----------------------------------------

restaurants = st.session_state.restaurants

if restaurants:

    st.markdown(
        f'<div class="section-title">📍 검색 결과 '
        f'{len(restaurants)}곳</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns([7, 3], gap="large")

    # 지도
    with left:

        st.markdown(
            '<div class="section-title">🗺️ 식당 위치</div>',
            unsafe_allow_html=True
        )

        first = restaurants[0]

        center_lat = float(first["y"])
        center_lon = float(first["x"])

        restaurant_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=14
        )

        for place in restaurants:

            lat = float(place["y"])
            lon = float(place["x"])

            name = html.escape(place.get("place_name", "이름 없음"))
            address = html.escape(
                place.get("road_address_name")
                or place.get("address_name", "")
            )

            popup_text = f"<b>{name}</b><br>{address}"

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=name,
                icon=folium.Icon(
                    color="orange",
                    icon="cutlery",
                    prefix="fa"
                )
            ).add_to(restaurant_map)

        st_folium(
            restaurant_map,
            width=None,
            height=430,
            key="restaurant_map"
        )

    # 식당 정보
    with right:

        st.markdown(
            '<div class="section-title">🍴 추천 식당</div>',
            unsafe_allow_html=True
        )

        selected_index = st.selectbox(
            "식당 선택",
            options=range(len(restaurants)),
            format_func=lambda i: restaurants[i].get(
                "place_name", "이름 없음"
            )
        )

        place = restaurants[selected_index]

        st.markdown('<div class="restaurant-card">', unsafe_allow_html=True)

        show_food_image(place)

        st.markdown(
            f'<div class="restaurant-name">'
            f'{html.escape(place.get("place_name", "이름 없음"))}'
            f'</div>',
            unsafe_allow_html=True
        )

        address = (
            place.get("road_address_name")
            or place.get("address_name", "주소 정보 없음")
        )

        st.markdown(
            f'<div class="restaurant-address">'
            f'📍 {html.escape(address)}'
            f'</div>',
            unsafe_allow_html=True
        )

        phone = place.get("phone", "")

        if phone:
            st.write(f"☎️ {phone}")

        category = place.get("category_name", "")

        if category:
            st.caption(f"분류: {category}")

        place_url = place.get("place_url")

        if place_url:
            st.link_button(
                "카카오에서 식당 자세히 보기",
                place_url,
                use_container_width=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

    # 다른 식당 목록
    st.markdown("---")
    st.markdown(
        '<div class="section-title">🍴 다른 검색 결과</div>',
        unsafe_allow_html=True
    )

    for i, restaurant in enumerate(restaurants):

        with st.container():
            c1, c2 = st.columns([1, 4])

            with c1:
                show_food_image(restaurant, height=120)

            with c2:
                st.markdown(
                    f"**{html.escape(restaurant.get('place_name', '이름 없음'))}**"
                )

                address = (
                    restaurant.get("road_address_name")
                    or restaurant.get("address_name", "주소 정보 없음")
                )

                st.caption(f"📍 {address}")

                if restaurant.get("place_url"):
                    st.link_button(
                        "상세 정보",
                        restaurant["place_url"],
                        key=f"place_link_{i}"
                    )

            st.divider()

elif search_button and keyword.strip():
    st.info("검색 결과가 없습니다. 다른 검색어를 입력해 보세요.")

else:
    st.markdown("""
    <div class="photo-placeholder" style="height:180px;">
        <div style="font-size:45px;">🥘</div>
        <div style="font-size:17px;font-weight:700;">
            먹고 싶은 음식을 검색해 보세요!
        </div>
        <div style="font-size:13px;">
            예: 수원역 맛집, 강남역 초밥, 홍대 치킨
        </div>
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------
# 9. 하단 안내
# ----------------------------------------

st.markdown("---")

st.caption(
    "🍽️ 오늘 뭐 먹지? | 식당 정보: 카카오 로컬 API | "
    "음식 이미지: AI 생성 이미지 (실제 식당 사진이 아닙니다.)"
)
