
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

# ---------- 디자인 ----------
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
    }
    .hero {
        background: linear-gradient(120deg, #fff1cf, #ffe0cf);
        padding: 24px;
        border-radius: 18px;
        margin-bottom: 20px;
    }
    .hero h1 {
        margin: 0;
        color: #542d20;
    }
    .hero p {
        color: #754b3d;
        margin-bottom: 0;
    }
    </style>
    <div class="hero">
        <h1>🍜 오늘 뭐 먹지?</h1>
        <p>지도에서 발견하는 우리 동네 맛집</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- API 키 ----------
try:
    kakao_key = st.secrets["KAKAO_REST_API_KEY"]
except Exception:
    kakao_key = ""

if not kakao_key:
    st.error(
        "카카오 REST API 키가 설정되지 않았어요. "
        "Streamlit Secrets 설정을 확인해 주세요."
    )
    st.stop()

# ---------- 검색창 ----------
with st.form("search_form"):
    area = st.text_input(
        "📍 검색할 지역",
        placeholder="예: 인하대학교, 수원시 영통구",
    )
    keyword = st.selectbox(
        "🍴 어떤 맛집을 찾을까요?",
        ["전체 맛집", "한식", "중식", "일식", "양식", "카페", "분식"],
    )
    search_button = st.form_submit_button(
        "🔎 지도에서 맛집 찾기",
        use_container_width=True,
    )

# ---------- 검색 ----------
if search_button:
    if not area.strip():
        st.warning("먼저 지역을 입력해 줘!")
    else:
        search_word = "" if keyword == "전체 맛집" else keyword
        query = f"{area.strip()} {search_word} 맛집".strip()

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
                st.session_state["search_area"] = area.strip()
                st.session_state["search_keyword"] = keyword
                st.session_state.pop("chosen_id", None)
                st.session_state.pop("reroll_seed", None)

                if not results:
                    st.info("검색 결과가 없어요. 다른 지역을 입력해 봐!")

            elif response.status_code == 401:
                st.error("REST API 키가 올바른지 확인해 줘.")
            elif response.status_code == 403:
                st.error(
                    "카카오 API 권한 또는 사용 설정을 확인해 줘. "
                    "카카오 개발자 문서의 오류 안내도 확인해 봐."
                )
            else:
                st.error(
                    f"검색 요청에 실패했어. HTTP {response.status_code}"
                )

        except requests.RequestException:
            st.error("인터넷 연결을 확인하고 다시 시도해 줘.")

# ---------- 지도 ----------
places = st.session_state.get("places", [])

if places:
    # 날짜와 검색 조건이 같으면 오늘의 추천이 일정하게 유지됨
    seed_text = (
        f"{date.today().isoformat()}|"
        f"{st.session_state.get('search_area', '')}|"
        f"{st.session_state.get('search_keyword', '')}"
    )
    seed = sum(ord(char) for char in seed_text)

    if "chosen_id" not in st.session_state:
        st.session_state["chosen_id"] = random.Random(seed).choice(
            places
        )["id"]

    chosen = next(
        (
            place for place in places
            if place["id"] == st.session_state["chosen_id"]
        ),
        places[0],
    )

    # 오늘의 추천 카드
    st.markdown("### ⭐ 오늘의 추천 맛집")
    st.subheader(f"🍽️ {chosen['place_name']}")

    address = (
        chosen.get("road_address_name")
        or chosen.get("address_name")
        or "주소 정보 없음"
    )
    st.write(f"📍 {address}")

    if chosen.get("category_name"):
        st.caption(chosen["category_name"])

    if chosen.get("place_url"):
        st.link_button(
            "카카오맵에서 가게 보기 ↗",
            chosen["place_url"],
        )

    if st.button("🎲 다른 맛집 추천", use_container_width=True):
        alternatives = [
            place for place in places
            if place["id"] != chosen["id"]
        ]
        if alternatives:
            st.session_state["chosen_id"] = random.choice(
                alternatives
            )["id"]
            st.rerun()
        else:
            st.info("다른 추천을 위해 검색 지역을 바꿔 봐!")

    st.divider()
    st.markdown("### 🗺️ 맛집 위치 지도")
    st.caption(
        "마커를 누르면 가게 정보가 나와. "
        "별 모양 마커가 오늘의 추천 맛집이야."
    )

    # 지도 중심 좌표
    center = [float(chosen["y"]), float(chosen["x"])]

    restaurant_map = folium.Map(
        location=center,
        zoom_start=15,
        control_scale=True,
    )

    # 검색된 맛집을 모두 지도 위에 표시
    for place in places:
        lat = float(place["y"])
        lon = float(place["x"])

        name = html.escape(place.get("place_name", "이름 없음"))
        place_address = html.escape(
            place.get("road_address_name")
            or place.get("address_name")
            or "주소 정보 없음"
        )
        category = html.escape(place.get("category_name", ""))
        url = html.escape(place.get("place_url", ""), quote=True)

        popup_html = (
            f"<div style='width:210px'>"
            f"<b>{name}</b><br>"
            f"<span>{place_address}</span><br>"
            f"<small>{category}</small><br>"
        )

        if url:
            popup_html += (
                f"<a href='{url}' target='_blank' "
                f"rel='noopener noreferrer'>카카오맵에서 보기</a>"
            )

        popup_html += "</div>"

        is_chosen = place["id"] == chosen["id"]

        folium.Marker(
            location=[lat, lon],
            tooltip=(
                f"⭐ 오늘의 추천: {name}"
                if is_chosen else name
            ),
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(
                color="orange" if is_chosen else "red",
                icon="star" if is_chosen else "cutlery",
                prefix="fa",
            ),
        ).add_to(restaurant_map)

    st_folium(
        restaurant_map,
        use_container_width=True,
        height=650,
        key="food_map",
    )

else:
    st.info(
        "👆 위에서 지역을 입력하고 검색하면 "
        "맛집 위치가 지도에 표시돼!"
    )
