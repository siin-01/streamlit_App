import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="서울시 공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울시 공영주차장 안내")

###########################################
# 데이터 불러오기
###########################################

uploaded_file = st.sidebar.file_uploader(
    "CSV 업로드",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding="cp949")
else:
    df = pd.read_csv(
        "data/서울시 공영주차장 안내 정보.csv",
        encoding="cp949"
    )

###########################################
# 전처리
###########################################

df = df.copy()

df["기본 주차 요금"] = pd.to_numeric(
    df["기본 주차 요금"],
    errors="coerce"
).fillna(0)

df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

df = df.dropna(subset=["위도", "경도"])

###########################################
# 자치구 추출
###########################################

df["자치구"] = (
    df["주소"]
    .str.extract(r"(강남구|강동구|강북구|강서구|관악구|광진구|구로구|금천구|노원구|도봉구|동대문구|동작구|마포구|서대문구|서초구|성동구|성북구|송파구|양천구|영등포구|용산구|은평구|종로구|중구|중랑구)")
)

###########################################
# 사이드바
###########################################

st.sidebar.header("검색 조건")

selected_gu = st.sidebar.selectbox(
    "자치구 선택",
    ["전체"] + sorted(df["자치구"].dropna().unique())
)

keyword = st.sidebar.text_input(
    "주소 또는 주차장명 검색"
)

free_only = st.sidebar.checkbox("무료 주차장만")

weekend_only = st.sidebar.checkbox("주말 운영")

###########################################
# 필터
###########################################

filtered = df.copy()

if selected_gu != "전체":
    filtered = filtered[
        filtered["자치구"] == selected_gu
    ]

if keyword:
    filtered = filtered[
        filtered["주소"].str.contains(keyword, na=False)
        |
        filtered["주차장명"].str.contains(keyword, na=False)
    ]

if free_only:
    filtered = filtered[
        filtered["유무료구분명"] == "무료"
    ]

if weekend_only:
    filtered = filtered[
        filtered["주말 운영 시작시각(HHMM)"].notna()
    ]

###########################################
# 추천
###########################################

st.subheader("🏆 가장 저렴한 주차장")

if len(filtered):

    free = filtered[
        filtered["유무료구분명"] == "무료"
    ]

    if len(free):

        best = free.iloc[0]

        st.success(
            f"""
무료 주차장 추천

주차장명 : {best['주차장명']}

주소 : {best['주소']}
"""
        )

    else:

        best = filtered.sort_values(
            "기본 주차 요금"
        ).iloc[0]

        st.success(
            f"""
주차장명 : {best['주차장명']}

기본요금 : {int(best['기본 주차 요금'])}원

주소 : {best['주소']}
"""
        )

###########################################
# 지도
###########################################

st.subheader("🗺 지도")

center = [
    filtered["위도"].mean(),
    filtered["경도"].mean()
]

m = folium.Map(
    location=center,
    zoom_start=12
)

for _, row in filtered.iterrows():

    popup = f"""
<b>{row['주차장명']}</b><br>

주소 : {row['주소']}<br>

기본요금 : {row['기본 주차 요금']}원<br>

무료여부 : {row['유무료구분명']}<br>

주말운영 :
{row['주말 운영 시작시각(HHMM)']}
~
{row['주말 운영 종료시각(HHMM)']}
"""

    if row["유무료구분명"] == "무료":
        color = "green"
    else:
        color = "blue"

    folium.Marker(
        location=[
            row["위도"],
            row["경도"]
        ],
        popup=folium.Popup(
            popup,
            max_width=350
        ),
        tooltip=row["주차장명"],
        icon=folium.Icon(color=color)
    ).add_to(m)

st_folium(
    m,
    width=1200,
    height=650
)

###########################################
# 통계
###########################################

col1, col2, col3 = st.columns(3)

col1.metric(
    "주차장 수",
    len(filtered)
)

col2.metric(
    "평균 기본요금",
    f"{filtered['기본 주차 요금'].mean():.0f}원"
)

col3.metric(
    "무료 주차장",
    len(filtered[
        filtered["유무료구분명"]=="무료"
    ])
)

###########################################
# 데이터
###########################################

st.subheader("📋 주차장 목록")

show_cols = [
    "주차장명",
    "주소",
    "기본 주차 요금",
    "유무료구분명",
    "총 주차면",
    "전화번호"
]

st.dataframe(
    filtered[show_cols],
    use_container_width=True
)

###########################################
# 다운로드
###########################################

csv = filtered.to_csv(
    index=False,
    encoding="cp949"
).encode("cp949")

st.download_button(
    "CSV 다운로드",
    csv,
    "parking_result.csv",
    "text/csv"
)
