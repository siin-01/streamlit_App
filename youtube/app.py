import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt
import re
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="유튜브 댓글 분석기", layout="wide")
st.title("📊 유튜브 댓글 분석기")

# 1. Streamlit Secrets에서 API Key 가져오기
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("Streamlit Secrets에 'YOUTUBE_API_KEY'가 설정되지 않았습니다.")
    st.stop()

# 유튜브 API 객체 생성
youtube = build("youtube", "v3", developerKey=api_key)

# 2. 유튜브 URL에서 Video ID 추출하는 함수
def extract_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

# 3. 유튜브 댓글 수집 함수
def get_youtube_comments(video_id, max_comments):
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_comments, 100), # 한 번에 최대 100개
            textFormat="plainText"
        )
        
        while request and len(comments) < max_comments:
            response = request.execute()
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment['authorDisplayName'],
                    'text': comment['textDisplay'],
                    'published_at': comment['publishedAt'],
                    'like_count': comment['likeCount']
                })
                if len(comments) >= max_comments:
                    break
                    
            # 다음 페이지가 있으면 계속 수집
            if 'nextPageToken' in response and len(comments) < max_comments:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    pageToken=response['nextPageToken'],
                    maxResults=min(max_comments - len(comments), 100),
                    textFormat="plainText"
                )
            else:
                break
    except Exception as e:
        st.error(f"댓글을 가져오는 중 오류가 발생했습니다: {e}")
        return None
        
    return pd.DataFrame(comments)

# --- 사이드바 UI ---
st.sidebar.header("🔍 설정")
video_url = st.sidebar.text_input("유튜브 영상 링크를 입력하세요:")
max_comments = st.sidebar.slider("수집할 댓글 개수 설정", min_value=10, max_value=500, value=100, step=10)
font_path = st.sidebar.text_input("나눔고딕 폰트 경로 (기본값: 같은 폴더)", value="NanumGothic.ttf")

# 메인 로직
if video_url:
    video_id = extract_video_id(video_url)
    
    if video_id:
        # 영상 시각화
        st.subheader("📺 선택한 영상")
        st.video(video_url)
        
        with st.spinner("댓글을 수집하고 분석하는 중입니다..."):
            df = get_youtube_comments(video_id, max_comments)
            
        if df is not None and not df.empty:
            st.success(f"총 {len(df)}개의 댓글 수집 완료!")
            
            # 전처리: 시간대 데이터 변환
            df['published_at'] = pd.to_datetime(df['published_at'])
            # 깃허브 환경(UTC) 고려 및 보기 편하게 날짜/시간 단위로 추출
            df['date_hour'] = df['published_at'].dt.strftime('%m-%d %H시')
            
            # --- 시각화 영역 분할 ---
            col1, col2 = st.columns(2)
            
            with col1:
                # 1. 시간대별 댓글 작성 추이
                st.subheader("📈 시간대별 댓글 작성 추이")
                time_counts = df.groupby('date_hour').size().reset_index(name='count')
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(time_counts['date_hour'], time_counts['count'], marker='o', color='#FF0000', linewidth=2)
                ax.set_xticklabels(time_counts['date_hour'], rotation=45, ha='right')
                ax.set_ylabel("댓글 수")
                ax.grid(True, linestyle='--', alpha=0.6)
                st.pyplot(fig)

            with col2:
                # 2. 댓글 반응도 (좋아요 수 기준 Top 5)
                st.subheader("❤️ 반응도 높은 댓글 (Top 5)")
                top_liked = df.nlargest(5, 'like_count')[['author', 'text', 'like_count']]
                for idx, row in top_liked.iterrows():
                    st.markdown(f"**{row['author']}** (👍 {row['like_count']}개)")
                    st.caption(row['text'])
                    st.write("---")
            
            # 3. 한글 워드클라우드
            st.subheader("☁️ 댓글 키워드 워드클라우드")
            
            # 한글 텍스트 정제 및 명사 추출
            okt = Okt()
            raw_text = " ".join(df['text'].astype(str).tolist())
            # 한글과 공백만 남기기
            clean_text = re.sub(f"[^가-힣\\s]", "", raw_text)
            
            # 명사 추출 (2글자 이상만)
            nouns = [word for word in okt.nouns(clean_text) if len(word) > 1]
            
            if nouns:
                word_counts = Counter(nouns)
                
                try:
                    # 워드클라우드 생성 (설정한 폰트 경로 적용)
                    wc = WordCloud(
                        font_path=font_path,
                        background_color="white",
                        width=800,
                        height=400,
                        max_words=100
                    ).generate_from_frequencies(word_counts)
                    
                    fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
                    ax_wc.imshow(wc, interpolation='interpoles')
                    ax_wc.axis('off')
                    st.pyplot(fig_wc)
                except Exception as e:
                    st.error(f"워드클라우드 생성 중 오류가 발생했습니다. 폰트 경로를 확인해주세요: {e}")
            else:
                st.warning("분석할 만한 한글 명사가 댓글에 존재하지 않습니다.")
                
            # 수집된 데이터 표로 확인하기
            with st.expander("데이터 전체보기"):
                st.dataframe(df[['author', 'text', 'like_count', 'published_at']])
        else:
            st.warning("수집된 댓글이 없습니다. 영상에 댓글이 차단되어 있는지 확인하세요.")
    else:
        st.error("올바른 유튜브 URL 형식이 아닙니다.")
