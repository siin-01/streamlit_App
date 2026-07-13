import streamlit as st
import requests
import random

# --------------------------
# 설정
# --------------------------

API_KEY = "e9cb9eeb7e6345707e71485fb442e09c"

st.set_page_config(
    page_title="🍙 오늘 뭐 먹지?",
    page_icon="🍜",
    layout="centered"
)

# --------------------------
# CSS
# --------------------------

st.markdown("""
<style>

.stApp{
    background: linear-gradient(#FFF8F8,#FFEFF5);
}

.title{
    text-align:center;
    font-size:45px;
    color:#ff5f87;
    font-weight:bold;
}

.subtitle{
    text-align:center;
    font-size:20px;
    color:#666;
}

.card{
    background:white;
    border-radius:20px;
    padding:20px;
    box-shadow:0px 4px 12px rgba(0,0,0,0.15);
}

.foodname{
    text-align:center;
    font-size:35px;
    color:#ff6699;
    font-weight:bold;
}

.info{
    font-size:20px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------
# 음식 데이터
# --------------------------

foods = {
    "cold":[
        {
            "name":"🍜 라면",
            "image":"https://images.unsplash.com/photo-1617093727343-374698b1b08d",
            "cal":510,
            "carb":"78g",
            "protein":"12g",
            "fat":"18g"
        },
        {
            "name":"🍲 김치찌개",
            "image":"https://images.unsplash.com/photo-1604908176997-125f25cc6f3d",
            "cal":430,
            "carb":"24g",
            "protein":"28g",
            "fat":"22g"
        },
        {
            "name":"🍢 어묵",
            "image":"https://images.unsplash.com/photo-1547592180-85f173990554",
            "cal":320,
            "carb":"18g",
            "protein":"20g",
            "fat":"14g"
        }
    ],

    "hot":[
        {
            "name":"🍧 빙수",
            "image":"https://images.unsplash.com/photo-1563805042-7684c019e1cb",
            "cal":450,
            "carb":"80g",
            "protein":"8g",
            "fat":"10g"
        },
        {
            "name":"🥗 냉면",
            "image":"https://images.unsplash.com/photo-1559847844-d721426d6edc",
            "cal":480,
            "carb":"90g",
            "protein":"14g",
            "fat":"5g"
        },
        {
            "name":"🍉 수박",
            "image":"https://images.unsplash.com/photo-1563114773-84221bd62daa",
            "cal":90,
            "carb":"23g",
            "protein":"2g",
            "fat":"0g"
        }
    ],

    "rain":[
        {
            "name":"🥞 파전",
            "image":"https://images.unsplash.com/photo-1625944524162-35d66a1f6ad8",
            "cal":620,
            "carb":"60g",
            "protein":"18g",
            "fat":"30g"
        },
        {
            "name":"🍜 칼국수",
            "image":"https://images.unsplash.com/photo-1612929633738-8fe44f7ec841",
            "cal":520,
            "carb":"82g",
            "protein":"16g",
            "fat":"12g"
        }
    ],

    "normal":[
        {
            "name":"🍔 햄버거",
            "image":"https://images.unsplash.com/photo-1568901346375-23c9450c58cd",
            "cal":650,
            "carb":"54g",
            "protein":"30g",
            "fat":"32g"
        },
        {
            "name":"🍣 초밥",
            "image":"https://images.unsplash.com/photo-1579871494447-9811cf80d66c",
            "cal":420,
            "carb":"58g",
            "protein":"26g",
            "fat":"9g"
        }
    ]
}

# --------------------------
# 제목
# --------------------------

st.markdown("<div class='title'>🍙 오늘 뭐 먹지?</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>날씨에 맞는 메뉴를 추천해드려요!</div>", unsafe_allow_html=True)

city = st.text_input("📍 도시 이름", "Seoul")

# --------------------------
# 버튼
# --------------------------

if st.button("🍴 메뉴 추천받기"):

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(url)

    if response.status_code == 200:

        data = response.json()

        temp = data["main"]["temp"]
        weather = data["weather"][0]["main"]

        st.success(f"현재 기온 : {temp:.1f}℃")

        if weather in ["Rain","Drizzle","Thunderstorm"]:
            category="rain"

        elif temp <= 10:
            category="cold"

        elif temp >= 25:
            category="hot"

        else:
            category="normal"

        menu=random.choice(foods[category])

        st.markdown("<br>", unsafe_allow_html=True)

        st.image(menu["image"], use_container_width=True)

        st.markdown(
            f"<div class='foodname'>{menu['name']}</div>",
            unsafe_allow_html=True
        )

        st.markdown("### 🍽️ 영양정보")

        col1,col2=st.columns(2)

        with col1:
            st.metric("🔥 칼로리",f"{menu['cal']} kcal")

        with col2:
            st.metric("🌡️ 현재 기온",f"{temp:.1f}℃")

        st.write(f"🥖 탄수화물 : {menu['carb']}")
        st.write(f"🥩 단백질 : {menu['protein']}")
        st.write(f"🧈 지방 : {menu['fat']}")

    else:
        st.error("도시를 찾을 수 없습니다.")
