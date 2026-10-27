
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

st.title("🍜 오늘 뭐 먹지?")
st.write("우리 동네 맛집을 찾고 오늘의 추천 메뉴를 확인해 보세요!")

# 카카오 REST API 키 읽기
try:
    KAKAO_KEY = st.secrets["KAKAO_REST_API_KEY"]
except Exception:
    KAKAO_KEY = ""

if not KAKAO_KEY:
    st.error(
        "카카오 REST API 키가 설정되지 않았어요. "
        "아래 설정 방법을 확인해 주세요."
    )
    st.stop()

# 검색할 지역 입력
with st.form("search_form"):
    area = st.text_input(
        "📍 어느 지역에서 찾을까요?",
        placeholder="예: 수원시 영통구, 인하대학교",
    )
    submitted = st.form_submit_button("주변 맛집 찾기")

# 검색 결과 보관
if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

if submitted:
    if not area.strip():
        st.warning("검색할 지역을 입력해 주세요.")
    else:
        try:
            response = requests.get(
                "https://dapi.kakao.com/v2/local/search/keyword.json",
                headers={
                    "Authorization": f"KakaoAK {KAKAO_KEY}"
                },
                params={
                    "query": f"{area.strip()} 맛집",
                    "size": 15,
                    "page": 1,
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state.restaurants = data.get(
                    "documents", []
                )
                st.session_state.area = area.strip()
                st.session_state.pop("chosen_restaurant", None)

                if not st.session_state.restaurants:
                    st.info("검색 결과가 없어요. 다른 지역명을 입력해 보세요.")
            elif response.status_code == 401:
                st.error("REST API 키를 확인해 주세요.")
            elif response.status_code == 403:
                st.error("카카오 로컬 API 사용 설정을 확인해 주세요.")
            else:
                st.error(
                    f"검색에 실패했어요. 상태 코드: "
                    f"{response.status_code}"
                )

        except requests.RequestException:
            st.error("인터넷 연결을 확인하고 다시 시도해 주세요.")

restaurants = st.session_state.restaurants

if restaurants:
    st.subheader(f"📍 {st.session_state.area} 맛집")

    # 날짜가 바뀌면 오늘의 추천도 바뀜
    today_seed = int(date.today().strftime("%Y%m%d"))
    daily_restaurant = random.Random(today_seed).choice(restaurants)

    if "chosen_restaurant" not in st.session_state:
        st.session_state.chosen_restaurant = daily_restaurant

    st.markdown("### 🌟 오늘의 추천 맛집")
    chosen = st.session_state.chosen_restaurant

    st.subheader(chosen["place_name"])
    st.write(
        "주소:",
        chosen.get("road_address_name")
        or chosen.get("address_name", "주소 정보 없음"),
    )
    st.write("분류:", chosen.get("category_name", "정보 없음"))
    st.write("전화:", chosen.get("phone") or "전화번호 정보 없음")

    if chosen.get("place_url"):
        st.link_button("카카오맵에서 보기", chosen["place_url"])

    if st.button("🎲 다른 맛집 추천받기"):
        st.session_state.chosen_restaurant = random.choice(restaurants)
        st.rerun()

    st.divider()
    st.subheader("🗺️ 맛집 지도")

    first = restaurants[0]
    map_center = [float(first["y"]), float(first["x"])]

    restaurant_map = folium.Map(
        location=map_center,
        zoom_start=14,
    )

    for place in restaurants:
        lat = float(place["y"])
        lon = float(place["x"])

        address = (
            place.get("road_address_name")
            or place.get("address_name", "주소 정보 없음")
        )

        popup_html = (
            f"<b>{place['place_name']}</b><br>"
            f"{address}"
        )

        folium.Marker(
            location=[lat, lon],
            tooltip=place["place_name"],
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(restaurant_map)

    st_folium(
        restaurant_map,
        width=None,
        height=500,
        key="restaurant_map",
    )

    st.subheader("🍽️ 검색된 맛집 목록")

    for index, place in enumerate(restaurants, start=1):
        with st.expander(f"{index}. {place['place_name']}"):
            st.write(
                place.get("road_address_name")
                or place.get("address_name", "주소 정보 없음")
            )
            st.write(place.get("category_name", "분류 정보 없음"))

            if place.get("phone"):
                st.write(f"전화: {place['phone']}")

            if place.get("place_url"):
                st.link_button(
                    "카카오맵에서 보기",
                    place["place_url"],
                    key=f"place_{place['id']}",
                )
