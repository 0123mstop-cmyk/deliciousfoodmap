
import html
import random
from datetime import date

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="오늘 뭐 먹지?",
    page_icon="🍜",
    layout="wide",
)

# 디자인
st.markdown("""
<style>
.block-container {
    max-width: 1200px;
    padding-top: 2rem;
}
.hero {
    background: linear-gradient(120deg, #fff0c9, #ffdfd1);
    padding: 25px;
    border-radius: 20px;
    margin-bottom: 20px;
}
.hero h1 {
    color: #572d20;
    margin: 0;
}
.hero p {
    color: #754b3d;
    margin-bottom: 0;
}
</style>
<div class="hero">
    <h1>🍜 오늘 뭐 먹지?</h1>
    <p>오늘의 맛집을 추천받고 지도에서 바로 찾아보세요!</p>
</div>
""", unsafe_allow_html=True)

# API 키
try:
    kakao_key = st.secrets["KAKAO_REST_API_KEY"]
except Exception:
    kakao_key = ""

if not kakao_key:
    st.error("카카오 REST API 키를 Streamlit Secrets에 설정해 주세요.")
    st.stop()

# 검색창
with st.form("search_form"):
    area = st.text_input(
        "📍 지역 입력",
        placeholder="예: 인하대학교, 수원시 영통구",
    )

    category = st.selectbox(
        "🍴 먹고 싶은 종류",
        ["전체", "한식", "중식", "일식", "양식", "카페", "분식"],
    )

    search_clicked = st.form_submit_button(
        "맛집 찾기",
        use_container_width=True,
    )

# 검색 결과
if search_clicked:
    if not area.strip():
        st.warning("지역을 입력해 주세요.")
    else:
        category_query = "" if category == "전체" else category
        query = f"{area.strip()} {category_query} 맛집".strip()

        try:
            response = requests.get(
                "https://dapi.kakao.com/v2/local/search/keyword.json",
                headers={"Authorization": f"KakaoAK {kakao_key}"},
                params={"query": query, "size": 15, "page": 1},
                timeout=15,
            )

            if response.status_code == 200:
                places = response.json().get("documents", [])
                st.session_state["places"] = places
                st.session_state["area"] = area.strip()
                st.session_state["category"] = category

                # 검색 조건이 바뀌면 추천도 새로 선정
                st.session_state.pop("today_pick_id", None)
                st.session_state.pop("used_pick_ids", None)

                if not places:
                    st.info("검색 결과가 없어요. 다른 지역을 입력해 보세요.")

            elif response.status_code == 401:
                st.error("REST API 키를 확인해 주세요.")
            elif response.status_code == 403:
                st.error(
                    "카카오 API 권한이나 사용 설정을 확인해 주세요."
                )
            else:
                st.error(f"검색 오류: HTTP {response.status_code}")

        except requests.RequestException:
            st.error("인터넷 연결을 확인한 뒤 다시 시도해 주세요.")

places = st.session_state.get("places", [])

if places:
    # 오늘의 추천 식당: 날짜와 검색 지역을 기준으로 고정
    seed_text = (
        f"{date.today().isoformat()}|"
        f"{st.session_state.get('area', '')}|"
        f"{st.session_state.get('category', '')}"
    )
    seed = sum(ord(char) for char in seed_text)

    if "today_pick_id" not in st.session_state:
        first_pick = random.Random(seed).choice(places)
        st.session_state["today_pick_id"] = first_pick["id"]
        st.session_state["used_pick_ids"] = [first_pick["id"]]

    # 선택된 식당 찾기
    chosen = next(
        (
            p for p in places
            if p["id"] == st.session_state["today_pick_id"]
        ),
        places[0],
    )

    # 오늘의 맛집 카드
    st.markdown("## ⭐ 오늘의 추천 맛집")
    st.markdown(f"### 🍽️ {chosen['place_name']}")

    chosen_address = (
        chosen.get("road_address_name")
        or chosen.get("address_name")
        or "주소 정보 없음"
    )
    st.write(f"📍 {chosen_address}")

    if chosen.get("category_name"):
        st.caption(chosen["category_name"])

    if chosen.get("place_url"):
        st.link_button("카카오맵에서 자세히 보기", chosen["place_url"])

    # 다른 맛집 추천
    if st.button("🎲 다른 맛집 추천받기", use_container_width=True):
        alternatives = [
            p for p in places
            if p["id"] != st.session_state["today_pick_id"]
        ]

        if alternatives:
            new_pick = random.choice(alternatives)
            st.session_state["today_pick_id"] = new_pick["id"]
            st.session_state["used_pick_ids"].append(new_pick["id"])
            st.rerun()
        else:
            st.info("검색된 식당이 한 곳뿐이에요. 다른 지역을 검색해 보세요.")

    st.divider()
    st.markdown("## 🗺️ 맛집 지도")
    st.caption("별 마커는 오늘의 추천 맛집이에요. 마커를 눌러 정보를 확인하세요.")

    # 추천 식당을 지도 중심으로 설정
    center = [float(chosen["y"]), float(chosen["x"])]

    food_map = folium.Map(
        location=center,
        zoom_start=15,
        control_scale=True,
    )

    # 지도 위에 식당 마커 표시
    for place in places:
        lat = float(place["y"])
        lon = float(place["x"])

        name = html.escape(place.get("place_name", "이름 없음"))
        address = html.escape(
            place.get("road_address_name")
            or place.get("address_name")
            or "주소 정보 없음"
        )
        category_name = html.escape(place.get("category_name", ""))
        place_url = html.escape(place.get("place_url", ""), quote=True)

        popup_content = (
            f"<div style='width:220px'>"
            f"<b>{name}</b><br>"
            f"{address}<br>"
            f"<small>{category_name}</small><br>"
        )

        if place_url:
            popup_content += (
                f"<a href='{place_url}' target='_blank' "
                f"rel='noopener noreferrer'>카카오맵에서 보기</a>"
            )

        popup_content += "</div>"

        is_today_pick = place["id"] == chosen["id"]

        folium.Marker(
            location=[lat, lon],
            tooltip=(
                f"⭐ 오늘의 추천: {name}"
                if is_today_pick else name
            ),
            popup=folium.Popup(popup_content, max_width=280),
            icon=folium.Icon(
                color="orange" if is_today_pick else "red",
                icon="star" if is_today_pick else "cutlery",
                prefix="fa",
            ),
        ).add_to(food_map)

    st_folium(
        food_map,
        use_container_width=True,
        height=650,
        key="food_map",
    )

else:
    st.info(
        "👆 먼저 지역을 입력하고 '맛집 찾기'를 눌러 주세요. "
        "검색이 완료되면 오늘의 추천 식당과 지도가 나타나요!"
    )
