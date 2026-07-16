import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="서울시 공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울시 공영주차장 안내")

# -----------------------------
# CSV 불러오기
# -----------------------------
uploaded_file = st.sidebar.file_uploader(
    "CSV 업로드",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding="cp949")
else:
    df = pd.read_csv("서울시 공영주차장 안내 정보.csv", encoding="cp949")

# -----------------------------
# 컬럼 공백 제거
# -----------------------------
df.columns = df.columns.str.strip()

# -----------------------------
# 숫자 변환
# -----------------------------
if "위도" in df.columns:
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")

if "경도" in df.columns:
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

# -----------------------------
# 기본요금 숫자 변환
# -----------------------------
fee_col = None

for c in df.columns:
    if "기본" in c and "요금" in c:
        fee_col = c
        break

if fee_col:
    df[fee_col] = (
        df[fee_col]
        .astype(str)
        .str.replace(",", "")
        .str.extract(r"(\d+)")
    )

    df[fee_col] = pd.to_numeric(df[fee_col], errors="coerce")

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("검색 옵션")

# 자치구 추출
districts = []

for addr in df["주소"]:
    if pd.notna(addr):
        districts.append(str(addr).split()[1])

districts = sorted(list(set(districts)))

selected_gu = st.sidebar.selectbox(
    "자치구 선택",
    ["전체"] + districts
)

search_name = st.sidebar.text_input(
    "주차장 이름 검색"
)

free_only = st.sidebar.checkbox(
    "무료만 보기"
)

night_free_only = st.sidebar.checkbox(
    "야간무료만 보기"
)

if fee_col:
    min_fee = int(df[fee_col].min())
    max_fee = int(df[fee_col].max())

    fee_range = st.sidebar.slider(
        "기본요금",
        min_fee,
        max_fee,
        (min_fee, max_fee)
    )

# -----------------------------
# 필터
# -----------------------------
filtered = df.copy()

if selected_gu != "전체":
    filtered = filtered[
        filtered["주소"].str.contains(selected_gu, na=False)
    ]

if search_name != "":
    name_col = None

    for c in filtered.columns:
        if "주차장" in c:
            name_col = c
            break

    if name_col:
        filtered = filtered[
            filtered[name_col].str.contains(
                search_name,
                na=False
            )
        ]

if free_only:

    free_col = None

    for c in filtered.columns:
        if "유무료" in c:
            free_col = c
            break

    if free_col:
        filtered = filtered[
            filtered[free_col].astype(str).str.contains("무료")
        ]

if night_free_only:

    night_col = None

    for c in filtered.columns:
        if "야간무료" in c:
            night_col = c
            break

    if night_col:
        filtered = filtered[
            filtered[night_col].astype(str).str.contains("가능|무료|Y|예")
        ]

if fee_col:
    filtered = filtered[
        (filtered[fee_col] >= fee_range[0]) &
        (filtered[fee_col] <= fee_range[1])
    ]

# -----------------------------
# 지도 생성
# -----------------------------
center = [37.5665, 126.9780]

valid = filtered.dropna(subset=["위도", "경도"])

if len(valid) > 0:
    center = [
        valid["위도"].mean(),
        valid["경도"].mean()
    ]

m = folium.Map(
    location=center,
    zoom_start=12
)

# -----------------------------
# 마커 추가
# -----------------------------
name_col = None

for c in filtered.columns:
    if "주차장" in c:
        name_col = c
        break

for _, row in valid.iterrows():

    popup = f"""
<b>{row.get(name_col,'')}</b><br>

주소 : {row.get('주소','')}<br>

기본요금 : {row.get(fee_col,'')}원<br>

무료 :
{row.get('유무료구분명','')}<br>

야간무료 :
{row.get('야간무료개방여부명','')}<br>

주말 :
{row.get('토요일 운영 시작시각','')}
~
{row.get('토요일 운영 종료시각','')}<br>

공휴일 :
{row.get('공휴일 운영 시작시각','')}
~
{row.get('공휴일 운영 종료시각','')}<br>

총 주차면 :
{row.get('총 주차면수','')}
"""

    tooltip = row.get(name_col, "")

    folium.Marker(
        location=[
            row["위도"],
            row["경도"]
        ],
        tooltip=tooltip,
        popup=popup,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

# -----------------------------
# 지도 출력
# -----------------------------
st_folium(
    m,
    width=1200,
    height=700
)

st.write(f"검색 결과 : {len(filtered)}개")
