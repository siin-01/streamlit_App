import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 페이지 설정 ---
st.set_page_config(
    page_title="서울시 공영주차장 안내 가이드",
    page_icon="🚗",
    layout="wide"
)

# --- 타이틀 및 안내 ---
st.title("🚗 서울시 공영주차장 스마트 안내 서비스")
st.markdown("""
이 앱은 서울시 공영주차장 안내 데이터를 기반으로 위치, 요금, 운영 정보를 한눈에 보여줍니다. 
왼쪽 사이드바에서 **CSV 파일을 업로드**하거나 **기본 탑재된 데이터**로 바로 탐색해 보세요!
""")

# --- 1. 데이터 로드 및 파일 업로드 기능 ---
@st.cache_data
def load_default_data(file_path):
    try:
        # UTF-8 혹은 CP949 인코딩 처리
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
        
        # 위도/경도 결측치 제거 및 수치형 변환
        df = df.dropna(subset=['위도', '경도'])
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])
        
        # 자치구 추출 (주소에서 첫 번째 단어가 '서울시' 혹은 '서울특별시'인 경우 두 번째 단어를 자치구로 지정)
        def get_gu(address):
            if pd.isna(address):
                return "기타"
            parts = str(address).split()
            if len(parts) > 1 and ('서울' in parts[0]):
                return parts[1]
            return parts[0]
            
        df['자치구'] = df['주소'].apply(get_gu)
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return None

# 사이드바에서 파일 업로드 기능 제공
st.sidebar.header("📁 데이터 설정")
uploaded_file = st.sidebar.file_uploader("공영주차장 CSV 파일을 업로드하세요.", type=["csv"])

# 파일 업로드 여부에 따른 데이터 로드
if uploaded_file is not None:
    # 업로드된 파일 로드
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='cp949')
    
    # 전처리
    df = df.dropna(subset=['위도', '경도'])
    df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
    df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
    df = df.dropna(subset=['위도', '경도'])
    df['자치구'] = df['주소'].apply(lambda x: str(x).split()[1] if len(str(x).split()) > 1 else "기타")
    st.sidebar.success("성공적으로 업로드된 파일을 로드했습니다!")
else:
    # 기본 파일 로드 (로컬에 있는 '서울시 공영주차장 안내 정보.csv'를 기본값으로 설정)
    default_file_path = "서울시 공영주차장 안내 정보.csv"
    df = load_default_data(default_file_path)
    if df is not None:
        st.sidebar.info("기본 제공되는 서울시 공영주차장 데이터를 사용 중입니다.")
    else:
        st.sidebar.warning("기본 데이터를 찾을 수 없습니다. CSV 파일을 직접 업로드해 주세요.")

# --- 데이터가 정상적으로 존재할 때 앱 실행 ---
if df is not None and not df.empty:
    
    # --- 2. 최적/최저가 추천 정보 (자치구 선택) ---
    st.subheader("🔍 자치구별 맞춤 주차장 추천")
    
    # 자치구 선택 상자
    gu_list = sorted(list(df['자치구'].unique()))
    selected_gu = st.selectbox("탐색할 자치구를 선택하세요:", gu_list, index=gu_list.index("성동구") if "성동구" in gu_list else 0)
    
    # 해당 구 데이터 필터링
    gu_df = df[df['자치구'] == selected_gu]
    
    # 📌 [추천 기능 - 미니 대시보드]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("해당 구 주차장 수", f"{len(gu_df)} 개")
    with col2:
        avg_price = gu_df['기본 주차 요금'].mean()
        st.metric("평균 기본 요금 (5분/10분 등)", f"{avg_price:.0f} 원" if not pd.isna(avg_price) else "정보 없음")
    with col3:
        weekend_free_count = len(gu_df[gu_df['공휴일 유,무료 구분명'] == '무료'])
        st.metric("공휴일 무료 개방", f"{weekend_free_count} 곳")
    with col4:
        total_slots = gu_df['총 주차면'].sum()
        st.metric("총 주차 공간(면)", f"{total_slots:,} 면")
        
    st.markdown("---")
    
    # --- 최저가 주차장 계산 및 출력 ---
    # 주차 요금 비교를 위해 '기본 주차 요금'이 0원(무료)이거나 가장 저렴한 곳을 선별
    # 단, 기본 주차 시간이 다를 수 있으므로 5분당 가격으로 환산하는 가상 필드 생성 (기본 주차 요금 / 기본 주차 시간)
    gu_df = gu_df.copy()
    gu_df['기본 주차 시간(분 단위)'] = pd.to_numeric(gu_df['기본 주차 시간(분 단위)'], errors='coerce').fillna(5)
    gu_df['기본 주차 요금'] = pd.to_numeric(gu_df['기본 주차 요금'], errors='coerce').fillna(0)
    
    # 5분당 요금 환산
    gu_df['5분당_요금'] = (gu_df['기본 주차 요금'] / gu_df['기본 주차 시간(분 단위)']) * 5
    
    # 최저가 주차장 정렬 (0원 무료 주차장 제외하고 유료 중 가장 싼 곳 혹은 완전 무료 주차장 포함 정렬)
    cheap_df = gu_df.sort_values(by=['5분당_요금', '월 정기권 금액'], ascending=[True, True])
    
    st.markdown(f"### 🏆 **{selected_gu}**에서 가장 요금이 저렴한 주차장 Top 3")
    
    top_cols = st.columns(3)
    for idx, (_, row) in enumerate(cheap_df.head(3).iterrows()):
        with top_cols[idx]:
            st.info(f"**{idx+1}위. {row['주차장명']}**")
            st.markdown(f"""
            * **기본 요금**: {int(row['기본 주차 요금'])}원 / {int(row['기본 주차 시간(분 단위'])}분 (5분 환산: {int(row['5분당_요금'])}원)
            * **월 정기권**: {f"{int(row['월 정기권 금액']):,}" if not pd.isna(row['월 정기권 금액']) and row['월 정기권 금액'] > 0 else '정보없음/무료'}원
            * **주소**: {row['주소']}
            * **운영 시간(평일)**: {str(row['평일 운영 시작시각(HHMM)']).zfill(4)[:2]}:{str(row['평일 운영 시작시각(HHMM)']).zfill(4)[2:]} ~ {str(row['평일 운영 종료시각(HHMM)']).zfill(4)[:2]}:{str(row['평일 운영 종료시각(HHMM)']).zfill(4)[2:]}
            """)

    st.markdown("---")

    # --- 3. 인터랙티브 지도 시각화 필터 ---
    st.subheader("🗺️ 실시간 공영주차장 위치 지도")
    
    # 지도 상세 필터 사이드바 구성
    st.sidebar.header("🎯 지도 필터링")
    
    # 필터: 무료 주차장만 보기 여부
    free_only = st.sidebar.checkbox("무료 주차장만 보기 (기본요금 0원)")
    
    # 필터: 주말/공휴일 무료 주차장만 보기
    holiday_free_only = st.sidebar.checkbox("공휴일 무료 개방 주차장만 보기")
    
    # 데이터 필터 적용
    map_df = gu_df.copy()
    if free_only:
        map_df = map_df[map_df['기본 주차 요금'] == 0]
    if holiday_free_only:
        map_df = map_df[map_df['공휴일 유,무료 구분명'] == '무료']
        
    # 검색 기능
    search_query = st.text_input("🔍 주차장 이름으로 바로 찾기 (선택사항)", "")
    if search_query:
        map_df = map_df[map_df['주차장명'].str.contains(search_query, case=False, na=False)]

    if map_df.empty:
        st.warning("필터 조건에 부합하는 주차장이 없습니다. 필터를 조정해 주세요.")
    else:
        # 자치구 중심점 계산
        center_lat = map_df['위도'].mean()
        center_lng = map_df['경도'].mean()
        
        # 지도 객체 생성
        m = folium.Map(location=[center_lat, center_lng], zoom_start=14)
        
        # 마커 추가
        for _, row in map_df.iterrows():
            # 기본/추가 요금 정보 스트링 포맷팅
            fee_info = f"기본: {int(row['기본 주차 요금'])}원/{int(row['기본 주차 시간(분 단위'])}분"
            add_fee = f"추가: {int(row['추가 단위 요금'])}원/{int(row['추가 단위 시간(분 단위'])}분" if row['추가 단위 요금'] > 0 else "추가 요금 없음"
            
            # 주말/공휴일 개방 요약
            weekend_info = f"토요일: {row['토요일 유,무료 구분명']} | 공휴일: {row['공휴일 유,무료 구분명']}"
            
            # HTML 툴팁 정의 (마우스 올렸을 때 나타나는 팝업)
            tooltip_html = f"""
            <div style="font-family: sans-serif; width: 220px;">
                <h4 style="margin: 0 0 5px 0; color: #1f77b4;">{row['주차장명']}</h4>
                <p style="margin: 2px 0; font-size: 12px;"><b>주소:</b> {row['주소']}</p>
                <p style="margin: 2px 0; font-size: 12px;"><b>요금:</b> {fee_info} ({add_fee})</p>
                <p style="margin: 2px 0; font-size: 11px; color: #555;"><b>주말 운영:</b> {weekend_info}</p>
                <p style="margin: 2px 0; font-size: 11px; color: #2ca02c;"><b>총 주차면수:</b> {int(row['총 주차면'])}면</p>
            </div>
            """
            
            # 마커 색상 설정 (유료: blue, 무료: green)
            marker_color = 'green' if row['기본 주차 요금'] == 0 else 'blue'
            
            # Folium 마커 표시
            folium.Marker(
                location=[row['위도'], row['경도']],
                tooltip=folium.Tooltip(tooltip_html, sticky=True),
                icon=folium.Icon(color=marker_color, icon='info-sign')
            ).add_to(m)
            
        # 스트림릿에 지도 렌더링
        st_folium(m, width="100%", height=550, returned_objects=[])

    # --- 4. 필터링된 주차장 전체 목록 표 ---
    st.subheader("📋 주차장 상세 목록")
    st.dataframe(
        map_df[['주차장명', '주소', '총 주차면', '기본 주차 요금', '기본 주차 시간(분 단위)', '월 정기권 금액', '평일 운영 시작시각(HHMM)', '평일 운영 종료시각(HHMM)', '공휴일 유,무료 구분명']],
        use_container_width=True
    )

else:
    st.error("불러온 데이터가 없거나 형식이 잘못되었습니다. 파일을 확인해 주세요.")
