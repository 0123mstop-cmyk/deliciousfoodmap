
import html
import random
from datetime import date

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="오늘 뭐 먹지?",
    page_icon="🍴",
    layout="wide",
)

# ---------- UI 디자인 ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}
.stApp {
    background: #fffdf9;
}
.block-container {
    max-width: 1450px;
    padding: 1.5rem 2rem 2rem;
}
header[data-testid="stHeader"] {
    background: transparent;
}
h1, h2, h3 {
    color: #243b45;
}
.brand {
    font-size: 1.8rem;
    font-weight: 800;
    color: #252b2d;
    margin-bottom: 1.1rem;
}
.brand span {
    color: #ff715b;
}
.hero {
    background: linear-gradient(110deg, #fff0df, #fff5ed);
    border-radius: 24px;
    padding: 25px 28px;
    margin-bottom: 22px;
    border: 1px solid #ffeadc;
}
.eyebrow {
    color: #e76b52;
    font-size: .9rem;
    font-weight: 700;
}
.hero-title {
    font-size: 2.2rem;
    line-height: 1.3;
    font-weight: 800;
    color: #243b45;
    margin: 8px 0;
}
.hero-sub {
    color: #6e7778;
    font-size: 1rem;
}
.panel {
    background: white;
    border: 1px solid #eeeae5;
    border-radius: 20px;
    padding: 18px;
    box-shadow: 0 4px 18px rgba(40, 45, 50, .04);
}
.pick {
    background: linear-gradient(110deg, #fff3e4, #fff8f1);
    border: 1px solid #ffeadb;
    border-radius: 18px;
    padding: 20px;
    margin: 8px 0 18px;
}
.pick-label {
    color: #e96750;
    font-size: .85rem;
    font-weight: 800;
}
.pick-name {
    font-size: 1.45rem;
    font-weight: 800;
    color: #273d48;
    margin: 5px 0;
}
.pick-address {
    color: #66757b;
    font-size: .92rem;
}
.section-label {
    font-weight: 800;
    font-size: 1.15rem;
    color: #243b45;
    margin: 8px 0 12px;
}
div.stButton > button,
div.stFormSubmitButton > button {
    border-radius: 12px;
    min-height: 44px;
    font-weight: 700;
}
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background: #ff7058;
    border-color: #ff7058;
    color: white;
}
div[data-testid="stTextInput"] input {
    border-radius: 12px;
}
div[data-testid="stSelectbox"] > div > div {
    border-radius: 12px;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px;
}
small, .muted {
    color: #7b878a;
}
a {
    color: #087e78;
}
@media (max-width: 700px) {
    .block-container {
        padding: 1rem .7rem;
    }
    .hero-title {
        font-size: 1.7rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------- 상단 ----------
st.markdown(
    '<div class="brand"><span>🍴</span> 오늘 뭐 먹지?</div>',
    unsafe_allow_html=True,
)

st.markdown("""
<div class="hero">
    <div class="eyebrow">오늘의 맛집 탐험 ✨</div>
    <div class="hero-title">오늘 뭐 먹지?</div>
    <div class="hero-sub">
        내 주변 맛집을 지도에서 찾고, 오늘의 추천 맛집도 만나 보세요.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- API 키 ----------
try:
    kakao_key = st.secrets["KAKAO_REST_API_KEY"]
except Exception:
    kakao_key = ""

if not kakao_key:
    st.error(
        "카카오 REST API 키가 설정되지 않았어요. "
        "Streamlit의 Secrets 설정을 확인해 주세요."
    )
    st.stop()

# ---------- 검색 영역 ----------
with st.container(border=True):
    st.markdown("#### 📍 어디에서 맛집을 찾을까요?")

    with st.form("search_form"):
        area = st.text_input(
            "지역",
            placeholder="예: 인하대학교, 수원시 영통구",
            label_visibility="collapsed",
        )

        category = st.radio(
            "음식 종류",
            ["전체", "한식", "중식", "일식", "양식", "카페", "분식"],
            horizontal=True,
        )

        search_clicked = st.form_submit_button(
            "🔎 맛집 검색하기",
            type="primary",
            use_container_width=True,
        )

# ---------- API 검색 ----------
if search_clicked:
    if not area.strip():
        st.warning("먼저 검색할 지역을 입력해 주세요.")
    else:
        extra = "" if category == "전체" else category
        query = f"{area.strip()} {extra} 맛집".strip()

        try:
            response = requests.get(
                "https://dapi.kakao.com/v2/local/search/keyword.json",
                headers={"Authorization": f"KakaoAK {kakao_key}"},
                params={"query": query, "size": 15, "page": 1},
                timeout=15,
            )

            if response.status_code == 200:
                results = response.json().get("documents", [])
                st.session_state["places"] = results
                st.session_state["area"] = area.strip()
                st.session_state["category"] = category
                st.session_state.pop("today_pick_id", None)

                if not results:
                    st.info("검색 결과가 없어요. 다른 지역을 검색해 보세요.")

            elif response.status_code == 401:
                st.error("REST API 키를 확인해 주세요.")
            elif response.status_code == 403:
                st.error(
                    "카카오 API 권한 또는 사용 설정을 확인해 주세요."
                )
            else:
                st.error(f"검색 실패: HTTP {response.status_code}")

        except requests.RequestException:
            st.error("인터넷 연결을 확인하고 다시 시도해 주세요.")

places = st.session_state.get("places", [])

# ---------- 오늘의 추천 ----------
if places:
    # 같은 날짜와 검색 조건에서는 추천이 유지됨
    seed_text = (
        f"{date.today().isoformat()}|"
        f"{st.session_state.get('area', '')}|"
        f"{st.session_state.get('category', '')}"
    )
    seed = sum(ord(c) for c in seed_text)

    if "today_pick_id" not in st.session_state:
        initial_pick = random.Random(seed).choice(places)
        st.session_state["today_pick_id"] = initial_pick["id"]

    chosen = next(
        (p for p in places
         if p["id"] == st.session_state["today_pick_id"]),
        places[0],
    )

    address = (
        chosen.get("road_address_name")
        or chosen.get("address_name")
        or "주소 정보 없음"
    )

    # 지도 왼쪽, 정보 오른쪽
    map_col, info_col = st.columns([1.8, 1], gap="medium")

    with map_col:
        st.markdown(
            '<div class="section-label">⭐ 오늘의 추천 맛집</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="pick">
                <div class="pick-label">TODAY'S PICK · 오늘의 추천</div>
                <div class="pick-name">🍽️ {html.escape(chosen["place_name"])}</div>
                <div class="pick-address">📍 {html.escape(address)}</div>
                <div class="pick-address" style="margin-top:8px">
                    {html.escape(chosen.get("category_name", ""))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">🗺️ 우리 동네 맛집 지도</div>',
            unsafe_allow_html=True,
        )

        food_map = folium.Map(
            location=[float(chosen["y"]), float(chosen["x"])],
            zoom_start=15,
            control_scale=True,
            tiles="OpenStreetMap",
        )

        for place in places:
            lat = float(place["y"])
            lon = float(place["x"])
            name = html.escape(place.get("place_name", "이름 없음"))
            place_address = html.escape(
                place.get("road_address_name")
                or place.get("address_name")
                or "주소 정보 없음"
            )
            url = html.escape(place.get("place_url", ""), quote=True)

            popup_html = (
                f"<div style='width:210px;font-family:sans-serif'>"
                f"<b>{name}</b><br>{place_address}<br>"
            )
            if url:
                popup_html += (
                    f"<a href='{url}' target='_blank' "
                    f"rel='noopener noreferrer'>카카오맵에서 보기 ↗</a>"
                )
            popup_html += "</div>"

            is_pick = place["id"] == chosen["id"]

            folium.Marker(
                location=[lat, lon],
                tooltip=("⭐ 오늘의 추천" if is_pick else name),
                popup=folium.Popup(popup_html, max_width=260),
                icon=folium.Icon(
                    color="orange" if is_pick else "red",
                    icon="star" if is_pick else "cutlery",
                    prefix="fa",
                ),
            ).add_to(food_map)

        st_folium(
            food_map,
            use_container_width=True,
            height=570,
            key="food_map",
        )

    with info_col:
        st.markdown(
            '<div class="section-label">📌 맛집 정보</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown("### 🍴 " + chosen["place_name"])

            if chosen.get("category_name"):
                st.caption(chosen["category_name"])

            st.write("📍", address)

            if chosen.get("phone"):
                st.write("☎️", chosen["phone"])
            else:
                st.write("☎️ 전화번호 정보 없음")

            if chosen.get("place_url"):
                st.link_button(
                    "🗺️ 카카오맵에서 보기 ↗",
                    chosen["place_url"],
                    use_container_width=True,
                )

        st.markdown("#### 🎲 다른 맛집도 둘러보세요")

        alternatives = [
            p for p in places if p["id"] != chosen["id"]
        ]

        if alternatives:
            for p in alternatives[:4]:
                p_address = (
                    p.get("road_address_name")
                    or p.get("address_name")
                    or "주소 정보 없음"
                )

                with st.container(border=True):
                    st.markdown("**🍽️ " + p["place_name"] + "**")
                    st.caption(p_address)

                    if st.button(
                        "이 맛집 추천받기",
                        key=f"pick_{p['id']}",
                        use_container_width=True,
                    ):
                        st.session_state["today_pick_id"] = p["id"]
                        st.rerun()

        if st.button(
            "🎲 랜덤 맛집 추천",
            type="primary",
            use_container_width=True,
        ):
            if alternatives:
                st.session_state["today_pick_id"] = random.choice(
                    alternatives
                )["id"]
                st.rerun()
            else:
                st.info("다른 지역을 검색해 보세요.")

else:
    st.markdown("""
    <div class="panel" style="text-align:center;padding:42px 18px">
        <div style="font-size:3rem">🍲</div>
        <h3>오늘은 어떤 맛집을 찾을까요?</h3>
        <p style="color:#7b878a">
            위에서 지역을 검색하면 추천 맛집과 지도가 나타나요.
        </p>
    </div>
    """, unsafe_allow_html=True)
