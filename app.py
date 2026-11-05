
import html
import random
from datetime import date

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

# -------------------- 기본 설정 --------------------
st.set_page_config(
    page_title="오늘 뭐 먹지?",
    page_icon="🍴",
    layout="wide",
)

CATEGORIES = ["전체", "한식", "중식", "일식", "양식", "카페", "분식"]


# -------------------- 디자인 --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}
.stApp {
    background: #fffdf9;
    color: #263b42;
}
.block-container {
    max-width: 1500px;
    padding: 1.5rem 2rem 3rem;
}
.brand {
    font-size: 1.65rem;
    font-weight: 800;
    color: #263b42;
}
.brand span {
    color: #ff735b;
}
.greeting {
    text-align: right;
    color: #718083;
    font-size: .9rem;
    padding-top: 10px;
}
.hero {
    background: linear-gradient(120deg, #fff0df, #fff8ee);
    border: 1px solid #ffead8;
    border-radius: 24px;
    padding: 25px;
    min-height: 220px;
}
.hero-tag {
    color: #e76b50;
    font-weight: 800;
    font-size: .85rem;
}
.hero-title {
    color: #263b42;
    font-weight: 800;
    font-size: 2rem;
    line-height: 1.4;
    margin: 10px 0;
}
.hero-desc {
    color: #6d797b;
    line-height: 1.8;
}
.section-title {
    font-size: 1.2rem;
    font-weight: 800;
    color: #263b42;
    margin: 12px 0;
}
.pick-card {
    background: white;
    border: 1px solid #f0e8df;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 12px;
}
.pick-tag {
    color: #e66c50;
    font-weight: 800;
    font-size: .82rem;
}
.pick-name {
    font-size: 1.55rem;
    font-weight: 800;
    margin: 6px 0;
    color: #263b42;
}
.muted {
    color: #758184;
    font-size: .9rem;
    line-height: 1.7;
}
.chip {
    display: inline-block;
    padding: 5px 11px;
    margin: 3px 4px 3px 0;
    background: #fff0e7;
    color: #d9654e;
    border-radius: 20px;
    font-size: .78rem;
    font-weight: 700;
}
.photo-placeholder {
    background: linear-gradient(135deg, #fff0df, #f7eee4);
    border: 1px dashed #e8cbb5;
    border-radius: 16px;
    min-height: 150px;
    padding: 25px 12px;
    text-align: center;
    color: #8b7770;
}
div.stButton > button,
div.stFormSubmitButton > button,
div.stLinkButton > a {
    border-radius: 12px;
    font-weight: 700;
    min-height: 42px;
}
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background: #ff735b;
    border-color: #ff735b;
    color: white;
}
div[data-testid="stTextInput"] input {
    border-radius: 12px;
}
hr {
    border-color: #eee8e0;
}
</style>
""", unsafe_allow_html=True)


# -------------------- 공통 함수 --------------------
def safe_text(value, fallback="정보 없음"):
    if value is None or not str(value).strip():
        return fallback
    return html.escape(str(value))


def get_address(place):
    return (
        place.get("road_address_name")
        or place.get("address_name")
        or "주소 정보 없음"
    )


def get_restaurant_photo(place):
    """
    카카오 로컬 API는 일반적으로 식당 사진을 제공하지 않음.
    사진 API를 연결하기 전에는 임의의 사진 URL을 반환하지 않음.
    """
    return None


def show_restaurant_photo(place, height=190):
    """실제 사진 URL이 있을 때만 사진을 표시."""
    photo_url = get_restaurant_photo(place)

    if photo_url:
        st.image(photo_url, use_container_width=True)
    else:
        name = safe_text(place.get("place_name", "이 식당"))

        st.markdown(
            f"""
            <div class="photo-placeholder" style="min-height:{height}px">
                <div style="font-size:2.5rem;">📷</div>
                <div style="font-weight:700;margin-top:8px;">
                    {name}
                </div>
                <div style="font-size:.85rem;margin-top:5px;">
                    등록된 식당 사진을 찾을 수 없어요.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def search_places(query, api_key):
    response = requests.get(
        "https://dapi.kakao.com/v2/local/search/keyword.json",
        headers={"Authorization": f"KakaoAK {api_key}"},
        params={"query": query, "size": 15, "page": 1},
        timeout=15,
    )

    if response.status_code == 401:
        raise ValueError("카카오 REST API 키를 확인해 주세요.")

    if response.status_code == 403:
        raise ValueError("카카오 API 권한 또는 이용 설정을 확인해 주세요.")

    response.raise_for_status()
    return response.json().get("documents", [])


# -------------------- 상단 헤더 --------------------
today = date.today()
weekday_names = ["월", "화", "수", "목", "금", "토", "일"]

header_left, header_right = st.columns([1.4, 1])

with header_left:
    st.markdown(
        '<div class="brand"><span>🍴</span> 오늘 뭐 먹지?</div>',
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(
        f'<div class="greeting">'
        f'{today.year}년 {today.month}월 {today.day}일'
        f'({weekday_names[today.weekday()]}) '
        f'맛있는 하루 되세요! 😊</div>',
        unsafe_allow_html=True,
    )

st.divider()


# -------------------- 카카오 API 키 --------------------
try:
    kakao_key = st.secrets["KAKAO_REST_API_KEY"]
except Exception:
    kakao_key = ""

if not kakao_key:
    st.error(
        "카카오 REST API 키가 설정되지 않았어요. "
        "Secrets에 KAKAO_REST_API_KEY를 등록해 주세요."
    )
    st.stop()


# -------------------- 히어로 + 검색 영역 --------------------
hero_col, search_col = st.columns([1.05, 1], gap="large")

with hero_col:
    st.markdown("""
    <div class="hero">
        <div class="hero-tag">TODAY'S FOOD JOURNEY ✨</div>
        <div class="hero-title">
            오늘의 한 끼,<br>특별하게!
        </div>
        <div class="hero-desc">
            오늘 뭐 먹지?<br>
            내 주변 맛집을 찾아보고<br>
            새로운 메뉴에 도전해 보세요.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("🍜 한 끼의 즐거움을 발견하는 맛집 탐험")

with search_col:
    with st.container(border=True):
        st.markdown("### 📍 어디에서 찾아볼까요?")

        with st.form("search_form"):
            area = st.text_input(
                "검색 지역",
                placeholder="지역을 입력하세요 (예: 인하대학교, 수원시 영통구)",
                label_visibility="collapsed",
            )

            category = st.radio(
                "음식 종류",
                CATEGORIES,
                horizontal=True,
            )

            submitted = st.form_submit_button(
                "🔎 맛집 검색하기",
                type="primary",
                use_container_width=True,
            )

        st.caption("지역과 음식 종류를 선택하고 검색해 주세요.")


# -------------------- 검색 실행 --------------------
if submitted:
    if not area.strip():
        st.warning("검색할 지역을 먼저 입력해 주세요.")
    else:
        category_word = "" if category == "전체" else category
        query = f"{area.strip()} {category_word} 맛집".strip()

        try:
            with st.spinner("주변 맛집을 찾고 있어요..."):
                found_places = search_places(query, kakao_key)

            # 이전 결과를 새 검색 결과로 교체
            st.session_state["places"] = found_places
            st.session_state["searched_area"] = area.strip()
            st.session_state["searched_category"] = category
            st.session_state.pop("selected_place_id", None)

            if not found_places:
                st.info("검색 결과가 없어요. 지역이나 음식 종류를 바꿔 보세요.")

        except ValueError as error:
            st.error(str(error))
        except requests.RequestException:
            st.error("네트워크 연결을 확인하고 다시 검색해 주세요.")


# -------------------- 검색 결과 표시 --------------------
places = st.session_state.get("places", [])

if places:
    selected_id = st.session_state.get("selected_place_id")

    selected = next(
        (p for p in places if p.get("id") == selected_id),
        None,
    )

    if selected is None:
        seed = (
            f"{today.isoformat()}|"
            f"{st.session_state.get('searched_area', '')}|"
            f"{st.session_state.get('searched_category', '')}"
        )

        selected = random.Random(seed).choice(places)
        st.session_state["selected_place_id"] = selected["id"]

    address = get_address(selected)
    place_url = selected.get("place_url", "")

    # -------------------- 좌 7 : 우 3 --------------------
    left_col, right_col = st.columns([7, 3], gap="large")

    # ==================== 왼쪽 영역 ====================
    with left_col:
        st.markdown(
            '<div class="section-title">⭐ 오늘의 추천 맛집</div>',
            unsafe_allow_html=True,
        )

        # 추천 식당의 실제 사진이 있을 때만 사진 표시
        show_restaurant_photo(selected, height=190)

        st.markdown(
            f"""
            <div class="pick-card">
                <div class="pick-tag">TODAY'S PICK · 오늘의 추천</div>
                <div class="pick-name">
                    🍽️ {safe_text(selected.get("place_name"))}
                </div>
                <span class="chip">맛집 추천</span>
                <span class="chip">
                    {safe_text(st.session_state.get("searched_category", "전체"))}
                </span>
                <div class="muted" style="margin-top:9px;">
                    📍 {safe_text(address)}
                </div>
                <div class="muted" style="margin-top:5px;">
                    {safe_text(selected.get("category_name", ""), "카테고리 정보 없음")}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if place_url:
            st.link_button(
                "🗺️ 카카오맵에서 보기 →",
                place_url,
                type="primary",
                use_container_width=True,
            )

        st.markdown(
            '<div class="section-title">🗺️ 우리 동네 맛집 지도</div>',
            unsafe_allow_html=True,
        )

        try:
            food_map = folium.Map(
                location=[
                    float(selected["y"]),
                    float(selected["x"]),
                ],
                zoom_start=15,
                control_scale=True,
                tiles="OpenStreetMap",
                zoom_control=True,
            )

            for place in places:
                lat = float(place["y"])
                lon = float(place["x"])
                name = safe_text(place.get("place_name", "이름 없음"))
                addr = safe_text(get_address(place))
                url = place.get("place_url", "")
                is_selected = place.get("id") == selected.get("id")

                popup_html = f"<b>{name}</b><br>{addr}<br>"

                if url:
                    safe_url = html.escape(url, quote=True)
                    popup_html += (
                        f"<a href='{safe_url}' target='_blank' "
                        f"rel='noopener noreferrer'>카카오맵에서 보기 →</a>"
                    )

                folium.Marker(
                    location=[lat, lon],
                    tooltip="⭐ 오늘의 추천" if is_selected else name,
                    popup=folium.Popup(popup_html, max_width=260),
                    icon=folium.Icon(
                        color="orange" if is_selected else "red",
                        icon="star" if is_selected else "cutlery",
                        prefix="fa",
                    ),
                ).add_to(food_map)

            st_folium(
                food_map,
                use_container_width=True,
                height=470,
                key="restaurant_map",
            )

            st.caption("⭐ 오늘의 추천 맛집　　📍 일반 맛집")

        except (KeyError, TypeError, ValueError):
            st.warning("지도에 표시할 위치 정보를 불러오지 못했어요.")

    # ==================== 오른쪽 영역 ====================
    with right_col:
        st.markdown(
            '<div class="section-title">📋 맛집 상세 정보</div>',
            unsafe_allow_html=True,
        )

        # 상세 정보 사진
        show_restaurant_photo(selected, height=220)

        with st.container(border=True):
            st.markdown(
                f"### {safe_text(selected.get('place_name'))}"
            )

            st.caption("⭐ 평점 및 리뷰 수 정보 없음")

            st.markdown(
                f'<span class="chip">'
                f'{safe_text(st.session_state.get("searched_category", "전체"))}'
                f'</span>',
                unsafe_allow_html=True,
            )

            st.write("📍", address)
            st.write("☎️", selected.get("phone") or "전화번호 정보 없음")
            st.write("🕒", "영업시간 정보 없음")

            st.markdown("**식당 소개**")
            st.write(
                selected.get("category_name")
                or "카카오 로컬 API에서 제공한 식당 정보입니다."
            )

            if place_url:
                st.link_button(
                    "카카오맵에서 보기 →",
                    place_url,
                    use_container_width=True,
                )

        st.markdown(
            '<div class="section-title">🍴 다른 맛집 둘러보기</div>',
            unsafe_allow_html=True,
        )

        alternatives = [
            p for p in places
            if p.get("id") != selected.get("id")
        ]

        for index, place in enumerate(alternatives[:5]):
            with st.container(border=True):
                show_restaurant_photo(place, height=120)

                st.markdown(
                    f"**{safe_text(place.get('place_name'))}**"
                )
                st.caption(
                    place.get("category_name") or "음식점"
                )
                st.caption("⭐ 평점 정보 없음")

                if st.button(
                    "이 맛집 보기",
                    key=f"select_{place.get('id')}",
                    use_container_width=True,
                ):
                    st.session_state["selected_place_id"] = place["id"]
                    st.rerun()

        if st.button(
            "🎲 다른 맛집 추천받기",
            type="primary",
            use_container_width=True,
        ):
            if alternatives:
                st.session_state["selected_place_id"] = random.choice(
                    alternatives
                )["id"]
                st.rerun()
            else:
                st.info("다른 지역을 검색해 보세요.")

else:
    # 검색 전 화면
    st.markdown("")

    empty_left, empty_center, empty_right = st.columns([1, 2, 1])

    with empty_center:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align:center;padding:22px">
                <div style="font-size:3.5rem">🍲</div>
                <h3>오늘은 어떤 맛집을 찾을까요?</h3>
                <p style="color:#758184">
                    위 검색창에 지역을 입력하면 추천 맛집과 지도가 나타나요.
                </p>
            </div>
            """, unsafe_allow_html=True)

st.divider()
st.caption("오늘 뭐 먹지? · 맛있는 하루를 위한 맛집 탐험 🍴")
