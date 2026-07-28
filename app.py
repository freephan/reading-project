import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# 환경변수 불러오기
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="독서 기록장",
    page_icon="📚",
    layout="wide",
)

st.title("📚 독서 기록장")
st.caption("PostgreSQL에 저장된 책 목록")


@st.cache_resource
def get_engine():
    """PostgreSQL 연결 엔진을 생성합니다."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            ".env 파일에 DATABASE_URL이 설정되어 있지 않습니다."
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


@st.cache_data(ttl=30)
def load_books():
    """books 테이블의 데이터를 불러옵니다."""
    engine = get_engine()

    query = text("""
        SELECT *
        FROM books
        ORDER BY book_id DESC
    """)

    with engine.connect() as connection:
        return pd.read_sql_query(query, connection)


try:
    books_df = load_books()

except ValueError as error:
    st.error(str(error))
    st.stop()

except SQLAlchemyError as error:
    st.error("데이터베이스 연결 또는 조회 중 오류가 발생했습니다.")
    st.code(str(error))
    st.stop()

except Exception as error:
    st.error("책 목록을 불러오는 중 예상하지 못한 오류가 발생했습니다.")
    st.code(str(error))
    st.stop()


# 상단 요약 영역
total_books = len(books_df)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("등록된 책", f"{total_books}권")

with col2:
    if "authors" in books_df.columns:
        author_count = books_df["authors"].dropna().nunique()
        st.metric("저자 수", f"{author_count}명")
    else:
        st.metric("저자 수", "-")

with col3:
    if "publisher" in books_df.columns:
        publisher_count = books_df["publisher"].dropna().nunique()
        st.metric("출판사 수", f"{publisher_count}곳")
    else:
        st.metric("출판사 수", "-")


st.divider()


if books_df.empty:
    st.info(
        "아직 등록된 책이 없습니다. "
        "ISBN을 입력하고 create_books_csv.py와 import_books.py를 실행하세요."
    )

else:
    # 검색어
    search_word = st.text_input(
        "책 검색",
        placeholder="제목, 저자, ISBN을 입력하세요",
    )

    filtered_df = books_df.copy()

    if search_word:
        search_word = search_word.strip().lower()

        searchable_columns = [
            column
            for column in ["title", "authors", "isbn13", "publisher"]
            if column in filtered_df.columns
        ]

        if searchable_columns:
            condition = pd.Series(False, index=filtered_df.index)

            for column in searchable_columns:
                condition |= (
                    filtered_df[column]
                    .fillna("")
                    .astype(str)
                    .str.lower()
                    .str.contains(search_word, regex=False)
                )

            filtered_df = filtered_df[condition]

    st.write(f"검색 결과: **{len(filtered_df)}권**")

    # 화면에 보여줄 열
    preferred_columns = [
        "book_id",
        "title",
        "authors",
        "publisher",
        "published_date",
        "isbn13",
        "page_count",
        "categories",
        "created_at",
    ]

    display_columns = [
        column
        for column in preferred_columns
        if column in filtered_df.columns
    ]

    # 예상한 열 이름이 하나도 없으면 전체 열을 표시
    if not display_columns:
        display_columns = list(filtered_df.columns)

    st.dataframe(
        filtered_df[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "book_id": st.column_config.NumberColumn(
                "번호",
                format="%d",
            ),
            "title": st.column_config.TextColumn(
                "제목",
                width="large",
            ),
            "authors": st.column_config.TextColumn(
                "저자",
                width="medium",
            ),
            "publisher": st.column_config.TextColumn(
                "출판사",
                width="medium",
            ),
            "published_date": st.column_config.TextColumn(
                "출간일",
            ),
            "isbn13": st.column_config.TextColumn(
                "ISBN",
            ),
            "page_count": st.column_config.NumberColumn(
                "쪽수",
                format="%d쪽",
            ),
            "categories": st.column_config.TextColumn(
                "분류",
            ),
            "created_at": st.column_config.DatetimeColumn(
                "등록일",
                format="YYYY-MM-DD HH:mm",
            ),
        },
    )

    st.divider()
    st.subheader("📖 책 상세정보")

    # 검색 결과가 있을 때만 선택창 표시
    if filtered_df.empty:
        st.info("상세정보를 볼 책이 없습니다.")

    else:
        # book_id를 기준으로 책 선택
        book_options = filtered_df[
            ["book_id", "title", "authors"]
        ].copy()

        def make_book_label(book_id):
            row = book_options[
                book_options["book_id"] == book_id
            ].iloc[0]

            title = row.get("title") or "제목 없음"
            authors = row.get("authors") or "저자 미상"

            return f"{title} — {authors}"

        selected_book_id = st.selectbox(
            "상세정보를 볼 책을 선택하세요",
            options=book_options["book_id"].tolist(),
            format_func=make_book_label,
        )

        selected_book = filtered_df[
            filtered_df["book_id"] == selected_book_id
        ].iloc[0]

        detail_col1, detail_col2 = st.columns(
            [1, 3],
            gap="large",
        )

        # 왼쪽: 책 표지
        with detail_col1:
            cover_url = selected_book.get("cover_url")

            if pd.notna(cover_url) and str(cover_url).strip():
                st.image(
                    str(cover_url),
                    caption=selected_book.get("title", ""),
                    use_container_width=True,
                )
            else:
                st.info("등록된 표지 이미지가 없습니다.")

        # 오른쪽: 책 기본정보
        with detail_col2:
            title = selected_book.get("title") or "제목 없음"
            subtitle = selected_book.get("subtitle")
            authors = selected_book.get("authors") or "저자 미상"
            translator = selected_book.get("translator")
            publisher = selected_book.get("publisher") or "-"
            published_date = selected_book.get("published_date") or "-"
            isbn13 = selected_book.get("isbn13") or "-"
            isbn10 = selected_book.get("isbn10") or "-"
            page_count = selected_book.get("page_count")
            categories = selected_book.get("categories") or "-"
            language_code = selected_book.get("language_code") or "-"

            st.markdown(f"## {title}")

            if pd.notna(subtitle) and str(subtitle).strip():
                st.markdown(f"**{subtitle}**")

            st.markdown(f"**저자:** {authors}")

            if pd.notna(translator) and str(translator).strip():
                st.markdown(f"**번역:** {translator}")

            st.markdown(f"**출판사:** {publisher}")
            st.markdown(f"**출간일:** {published_date}")
            st.markdown(f"**ISBN-13:** {isbn13}")
            st.markdown(f"**ISBN-10:** {isbn10}")

            if pd.notna(page_count):
                try:
                    st.markdown(f"**쪽수:** {int(page_count)}쪽")
                except (ValueError, TypeError):
                    st.markdown(f"**쪽수:** {page_count}")

            st.markdown(f"**분류:** {categories}")
            st.markdown(f"**언어:** {language_code}")

        # 책 소개
        description = selected_book.get("description")

        with st.expander("책 소개 보기", expanded=True):
            if pd.notna(description) and str(description).strip():
                st.write(str(description))
            else:
                st.info("등록된 책 소개가 없습니다.")

        # 외부 정보 링크
        preview_url = selected_book.get("preview_url")
        info_url = selected_book.get("info_url")

        link_col1, link_col2 = st.columns(2)

        with link_col1:
            if pd.notna(preview_url) and str(preview_url).strip():
                st.link_button(
                    "Google Books 미리보기",
                    str(preview_url),
                    use_container_width=True,
                )

        with link_col2:
            if pd.notna(info_url) and str(info_url).strip():
                st.link_button(
                    "도서 정보 페이지",
                    str(info_url),
                    use_container_width=True,
                )

    if st.button("목록 새로고침"):
        st.cache_data.clear()
        st.rerun()