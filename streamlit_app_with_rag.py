import streamlit as st
import sqlite3
import pandas as pd
import json
import sys
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

from dotenv import load_dotenv
# Load environment
load_dotenv()

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="Research Article Intelligence",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for floating chat button and chat interface
st.markdown("""
<style>
    /* Floating chat button */
    .floating-chat-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .floating-chat-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    }

    .floating-chat-button svg {
        width: 30px;
        height: 30px;
    }

    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    /* Message bubbles */
    .user-message {
        background: #667eea;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        text-align: right;
    }

    .assistant-message {
        background: #f0f2f6;
        color: #262730;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        max-width: 80%;
    }

    .source-card {
        background: #fafafa;
        border-left: 3px solid #667eea;
        padding: 10px;
        margin: 8px 0;
        border-radius: 4px;
        font-size: 0.9em;
    }

    /* Sidebar styling */
    .rag-sidebar {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_db_connection():
    db_path = Path(__file__).parent / "data" / "articles.db"
    return sqlite3.connect(str(db_path), check_same_thread=False)

# Initialize RAG service
@st.cache_resource
def get_rag_service():
    """Initialize RAG service (cached)"""
    try:
        from backend.app.rag import RAGQueryService
        service = RAGQueryService()
        return service
    except Exception as e:
        st.error(f"RAG service not available: {e}")
        st.info("Run: `python scripts/build_rag_index.py` to build the index")
        return None

# Get statistics
@st.cache_data(ttl=60)
def get_stats():
    conn = get_db_connection()

    # Total articles
    total_articles = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM articles",
        conn
    ).iloc[0]['count']

    # Analyzed articles (from article_analysis table)
    analyzed_count = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM article_analysis WHERE analysis_status = 'completed'",
        conn
    ).iloc[0]['count']

    # Rejected articles
    rejected_count = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM article_analysis WHERE analysis_status = 'rejected'",
        conn
    ).iloc[0]['count']

    # Pending analysis
    pending_count = pd.read_sql_query(
        """SELECT COUNT(*) as count FROM articles a
           LEFT JOIN article_analysis aa ON a.id = aa.article_id
           WHERE aa.id IS NULL OR aa.analysis_status = 'pending'""",
        conn
    ).iloc[0]['count']

    # Recent articles by date
    articles_by_date = pd.read_sql_query(
        """SELECT DATE(publication_date) as date, COUNT(*) as count
           FROM articles
           WHERE publication_date IS NOT NULL
           GROUP BY DATE(publication_date)
           ORDER BY date DESC LIMIT 30""",
        conn
    )

    # Sources breakdown
    sources = pd.read_sql_query(
        "SELECT source, COUNT(*) as count FROM articles GROUP BY source",
        conn
    )

    # Category distribution
    categories = pd.read_sql_query(
        """SELECT category, COUNT(*) as count
           FROM article_analysis
           WHERE category IS NOT NULL
           GROUP BY category""",
        conn
    )

    # Sentiment distribution
    sentiments = pd.read_sql_query(
        """SELECT sentiment, COUNT(*) as count
           FROM article_analysis
           WHERE sentiment IS NOT NULL
           GROUP BY sentiment""",
        conn
    )

    # Analysis status distribution
    analysis_status = pd.read_sql_query(
        """SELECT analysis_status, COUNT(*) as count
           FROM article_analysis
           WHERE analysis_status IS NOT NULL
           GROUP BY analysis_status""",
        conn
    )

    # Rejection reasons
    rejection_reasons = pd.read_sql_query(
        """SELECT rejection_reason, COUNT(*) as count
           FROM article_analysis
           WHERE analysis_status = 'rejected' AND rejection_reason IS NOT NULL
           GROUP BY rejection_reason""",
        conn
    )

    return {
        'total': total_articles,
        'analyzed': analyzed_count,
        'rejected': rejected_count,
        'pending': pending_count,
        'by_date': articles_by_date,
        'sources': sources,
        'categories': categories,
        'sentiments': sentiments,
        'analysis_status': analysis_status,
        'rejection_reasons': rejection_reasons
    }

# Get articles with optional filters
@st.cache_data(ttl=60)
def get_articles(search_query=None, source_filter=None, date_from=None, date_to=None,
                 category_filter=None, sentiment_filter=None, subject_filter=None,
                 analysis_status_filter=None, limit=50):
    conn = get_db_connection()

    # Base query with all analysis fields including rejection_reason
    query = """
        SELECT
            a.id,
            a.article_id,
            a.source,
            a.title,
            a.abstract,
            a.journal,
            a.authors,
            a.publication_date,
            a.country,
            a.doi,
            aa.analysis_status,
            aa.analyzed_at,
            aa.subject,
            aa.category,
            aa.summary,
            aa.entities,
            aa.sentiment,
            aa.industry_affiliation,
            aa.evaluation_score,
            aa.stage,
            aa.attempt,
            aa.rejection_reason
        FROM articles a
        LEFT JOIN article_analysis aa ON a.id = aa.article_id
        WHERE 1=1
    """
    params = []

    # Search filter (FTS5)
    if search_query:
        query += """ AND a.id IN (
            SELECT article_id FROM articles_fts
            WHERE articles_fts MATCH ?
        )"""
        params.append(search_query)

    # Source filter
    if source_filter and source_filter != "All":
        query += " AND a.source = ?"
        params.append(source_filter.lower())

    # Date filters
    if date_from:
        query += " AND a.publication_date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND a.publication_date <= ?"
        params.append(date_to)

    # Category filter
    if category_filter and category_filter != "All":
        query += " AND aa.category = ?"
        params.append(category_filter)

    # Sentiment filter
    if sentiment_filter and sentiment_filter != "All":
        query += " AND aa.sentiment = ?"
        params.append(sentiment_filter)

    # Subject filter
    if subject_filter and subject_filter != "All":
        query += " AND aa.subject = ?"
        params.append(subject_filter)

    # Analysis status filter
    if analysis_status_filter and analysis_status_filter != "All":
        if analysis_status_filter == "Not Analyzed":
            query += " AND aa.id IS NULL"
        else:
            query += " AND aa.analysis_status = ?"
            params.append(analysis_status_filter.lower())

    query += " ORDER BY a.publication_date DESC, a.ingested_at DESC LIMIT ?"
    params.append(limit)

    df = pd.read_sql_query(query, conn, params=params)
    return df

# RAG Chat Interface as Main Page
def show_rag_chat_page():
    """Show RAG chat interface as a full page"""
    st.header("💬 RAG Q&A System")
    st.markdown("Ask questions about your research corpus using AI-powered semantic search")

    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'rag_service' not in st.session_state:
        st.session_state.rag_service = get_rag_service()

    rag_service = st.session_state.rag_service

    # Check if RAG is available
    if rag_service is None:
        st.error("⚠️ RAG index not built")
        st.info("""
        **To enable RAG, run:**
        ```bash
        python scripts/build_rag_index.py
        ```

        This will index your analyzed articles for semantic search.
        """)
        return

    # Collection info banner
    try:
        info = rag_service.get_collection_info()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Indexed Articles", info['total_documents'])
        with col2:
            st.metric("Collection", info['collection_name'])
        with col3:
            st.metric("Status", "🟢 Ready" if info['status'] == 'ready' else "🟡 Empty")
    except Exception as e:
        st.warning(f"Index status unknown: {e}")

    st.divider()

    # Sidebar filters
    st.sidebar.markdown("### 🔍 Search Filters")

    filter_category = st.sidebar.selectbox(
        "Category",
        ["All", "Clinical Studies", "Epidemiology", "Public Health Studies",
         "Behavior Studies", "Preclinical Studies", "Other"],
        key="rag_category_filter"
    )

    filter_sentiment = st.sidebar.selectbox(
        "Sentiment",
        ["All", "Positive", "Negative", "Neutral", "Mixed"],
        key="rag_sentiment_filter"
    )

    n_results = st.sidebar.slider("Number of sources", 3, 10, 5, key="rag_n_results")

    # Build filters dict
    filters = {}
    if filter_category != "All":
        filters['category'] = filter_category
    if filter_sentiment != "All":
        filters['sentiment'] = filter_sentiment

    st.sidebar.divider()

    # Clear history button in sidebar
    if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    # Example questions in sidebar
    st.sidebar.markdown("### 💡 Example Questions")
    examples = [
        "What are the cardiovascular effects of e-cigarettes?",
        "Show studies on youth vaping behavior",
        "Compare heated tobacco vs nicotine pouches",
        "What's the consensus on smoking cessation efficacy?",
        "Studies with industry affiliation"
    ]
    for ex in examples:
        if st.sidebar.button(ex, key=f"example_{ex[:20]}", use_container_width=True):
            st.session_state.current_question = ex
            st.rerun()

    # Main chat area
    # Chat history display (scrollable)
    if st.session_state.chat_history:
        st.markdown("### 📝 Conversation History")

        for idx, chat in enumerate(st.session_state.chat_history):
            # Question
            st.markdown(f"""
            <div style='background: #667eea; color: white; padding: 15px;
                        border-radius: 15px; margin: 10px 0; text-align: right;'>
                <strong>You:</strong> {chat['question']}
            </div>
            """, unsafe_allow_html=True)

            # Answer
            st.markdown(f"""
            <div style='background: #f0f2f6; padding: 15px;
                        border-radius: 15px; margin: 10px 0;'>
                <strong>Assistant:</strong><br>{chat['answer']}
            </div>
            """, unsafe_allow_html=True)

            # Sources
            if chat['sources']:
                with st.expander(f"📚 View {len(chat['sources'])} Sources"):
                    for i, source in enumerate(chat['sources'], 1):
                        st.markdown(f"""
                        **[{i}] {source.get('article_id', 'Unknown')}**
                        *{source.get('title', 'No title')}*
                        {source.get('journal', 'Unknown journal')} ({source.get('date', 'Unknown date')})
                        Category: {source.get('category', 'N/A')} | Sentiment: {source.get('sentiment', 'N/A')}
                        """)
                        if source.get('doi'):
                            st.markdown(f"[View Article](https://doi.org/{source['doi']})")
                        st.divider()

            st.divider()

    else:
        st.info("👋 Welcome! Ask a question to get started.")

    # Input area at bottom
    st.markdown("### ✍️ Ask a Question")

    user_question = st.text_area(
        "Type your question here:",
        value=st.session_state.get('current_question', ''),
        height=100,
        key="rag_question_input",
        placeholder="e.g., What are the cardiovascular risks of vaping?"
    )

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        ask_button = st.button("🚀 Ask", type="primary", use_container_width=True)
    with col2:
        clear_input = st.button("Clear Input", use_container_width=True)

    if clear_input:
        st.session_state.current_question = ''
        st.rerun()

    # Process query
    if ask_button and user_question.strip():
        with st.spinner("🔍 Searching and generating answer..."):
            try:
                # Query RAG service
                result = rag_service.query(
                    question=user_question,
                    n_results=n_results,
                    filters=filters if filters else None
                )

                # Add to chat history
                st.session_state.chat_history.append({
                    'question': user_question,
                    'answer': result['answer'],
                    'sources': result['sources'],
                    'timestamp': result['timestamp']
                })

                # Clear input
                st.session_state.current_question = ''
                st.success("✓ Answer generated!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Check that GROQ_API_KEY is set in your .env file")

# Main app
def main():
    st.title("📚 Research Article Intelligence Engine")
    st.markdown("AI-powered platform for analyzing scientific research articles")

    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Dashboard", "Article Browser", "RAG Chat"], key="main_nav")

    if page == "Dashboard":
        show_dashboard()
    elif page == "Article Browser":
        show_article_browser()
    elif page == "RAG Chat":
        show_rag_chat_page()

# Dashboard page
def show_dashboard():
    st.header("Dashboard")

    # Load stats
    with st.spinner("Loading statistics..."):
        stats = get_stats()

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Articles", stats['total'])

    with col2:
        st.metric("Analyzed", stats['analyzed'], delta=None, delta_color="normal")

    with col3:
        st.metric("Rejected", stats['rejected'], delta=None, delta_color="inverse")

    with col4:
        st.metric("Pending Analysis", stats['pending'])

    with col5:
        if stats['total'] > 0:
            completion_rate = (stats['analyzed'] / stats['total']) * 100
            st.metric("Success Rate", f"{completion_rate:.1f}%")
        else:
            st.metric("Success Rate", "0%")

    # Charts
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Articles by Source")
        if not stats['sources'].empty:
            fig = px.pie(stats['sources'], values='count', names='source',
                        title='Source Distribution')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No articles yet")

    with col2:
        st.subheader("Category Distribution")
        if not stats['categories'].empty:
            fig = px.bar(stats['categories'], x='category', y='count',
                        title='Categories')
            fig.update_layout(xaxis_title="Category", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No analysis data yet")

    with col3:
        st.subheader("Sentiment Distribution")
        if not stats['sentiments'].empty:
            fig = px.pie(stats['sentiments'], values='count', names='sentiment',
                        title='Sentiments')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No analysis data yet")

    # Analysis Status and Rejection Reasons
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Analysis Status")
        if not stats['analysis_status'].empty:
            fig = px.bar(stats['analysis_status'], x='analysis_status', y='count',
                        title='Analysis Status Breakdown',
                        color='analysis_status',
                        color_discrete_map={
                            'completed': '#28a745',
                            'rejected': '#dc3545',
                            'pending': '#ffc107'
                        })
            fig.update_layout(xaxis_title="Status", yaxis_title="Count", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No analysis data yet")

    with col2:
        st.subheader("Rejection Reasons")
        if not stats['rejection_reasons'].empty and len(stats['rejection_reasons']) > 0:
            fig = px.pie(stats['rejection_reasons'], values='count', names='rejection_reason',
                        title='Why Articles Were Rejected')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No rejected articles")

    # Publications timeline
    st.divider()
    st.subheader("Recent Publications (Last 30 Days)")
    if not stats['by_date'].empty:
        fig = px.bar(stats['by_date'], x='date', y='count',
                    title='Articles by Publication Date')
        fig.update_layout(xaxis_title="Date", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No date data available")

    # Recent activity
    st.divider()
    st.subheader("Recent Articles")
    recent_df = get_articles(limit=10)

    if not recent_df.empty:
        # Display simplified table
        display_df = recent_df[['article_id', 'title', 'source', 'publication_date', 'analysis_status']].copy()
        display_df.columns = ['Article ID', 'Title', 'Source', 'Publication Date', 'Status']
        display_df['Status'] = display_df['Status'].fillna('pending')
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No articles found. Run ingestion first.")

# Article browser page
def show_article_browser():
    st.header("Article Browser")

    # Filters in expander (main content area)
    with st.expander("🔍 Search Filters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            search_query = st.text_input("Search (title/abstract)", "")
            sources = ["All", "PubMed", "Crossref"]
            source_filter = st.selectbox("Source", sources)

        with col2:
            conn = get_db_connection()

            # Get unique categories
            categories_df = pd.read_sql_query(
                "SELECT DISTINCT category FROM article_analysis WHERE category IS NOT NULL ORDER BY category",
                conn
            )
            categories = ["All"] + categories_df['category'].tolist()
            category_filter = st.selectbox("Category", categories)

            # Get unique sentiments
            sentiments_df = pd.read_sql_query(
                "SELECT DISTINCT sentiment FROM article_analysis WHERE sentiment IS NOT NULL ORDER BY sentiment",
                conn
            )
            sentiments = ["All"] + sentiments_df['sentiment'].tolist()
            sentiment_filter = st.selectbox("Sentiment", sentiments)

        with col3:
            # Get unique subjects
            subjects_df = pd.read_sql_query(
                "SELECT DISTINCT subject FROM article_analysis WHERE subject IS NOT NULL ORDER BY subject",
                conn
            )
            subjects = ["All"] + subjects_df['subject'].tolist()
            subject_filter = st.selectbox("Subject", subjects)

            date_from = st.date_input("From Date", value=None)
            date_to = st.date_input("To Date", value=None)

        limit = st.slider("Results Limit", 10, 200, 50, 10)

        # Analysis status filter
        analysis_status_options = ["All", "completed", "rejected", "pending", "Not Analyzed"]
        analysis_status_filter = st.selectbox("Analysis Status", analysis_status_options)

    # Load articles
    with st.spinner("Loading articles..."):
        df = get_articles(
            search_query=search_query if search_query else None,
            source_filter=source_filter,
            date_from=str(date_from) if date_from else None,
            date_to=str(date_to) if date_to else None,
            category_filter=category_filter,
            sentiment_filter=sentiment_filter,
            subject_filter=subject_filter,
            analysis_status_filter=analysis_status_filter,
            limit=limit
        )

    # Display results
    st.subheader(f"Results ({len(df)} articles)")

    if df.empty:
        st.info("No articles found. Try adjusting filters or run ingestion first.")
        return

    # Display articles
    for idx, row in df.iterrows():
        with st.expander(f"**{row['title']}**"):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"**Article ID:** {row['article_id']}")
                st.write(f"**Source:** {row['source']}")
                st.write(f"**Journal:** {row['journal'] or 'N/A'}")

            with col2:
                st.write(f"**Publication Date:** {row['publication_date'] or 'N/A'}")
                st.write(f"**Country:** {row['country'] or 'N/A'}")

            with col3:
                status = row['analysis_status'] or 'pending'
                status_color = {
                    'completed': '✅',
                    'rejected': '❌',
                    'pending': '🟡',
                    'failed': '🔴'
                }.get(status, '⚪')
                st.write(f"**Status:** {status_color} {status}")
                if pd.notna(row['analyzed_at']):
                    st.write(f"**Analyzed:** {str(row['analyzed_at'])[:10]}")
                if pd.notna(row.get('attempt')) and row.get('attempt', 1) > 1:
                    st.write(f"**Attempts:** {int(row['attempt'])}")

            # Show rejection reason if rejected
            if status == 'rejected' and pd.notna(row.get('rejection_reason')):
                st.warning(f"**⚠️ Rejection Reason:** {row['rejection_reason']}")

            # Abstract
            st.divider()
            st.write("**Abstract:**")
            st.write(row['abstract'] or "No abstract available")

            # Analysis details (if available)
            if pd.notna(row.get('summary')):
                st.divider()
                st.write("**AI Analysis:**")

                col1, col2 = st.columns(2)

                with col1:
                    if pd.notna(row['summary']):
                        st.write("**Summary:**")
                        st.write(row['summary'])

                    if pd.notna(row['entities']):
                        st.write("**Key Entities:**")
                        try:
                            entities = json.loads(row['entities']) if isinstance(row['entities'], str) else row['entities']
                            if entities:
                                st.write(", ".join(entities[:10]))
                        except:
                            st.write(str(row['entities'])[:200])

                with col2:
                    if pd.notna(row['category']):
                        st.write(f"**Category:** {row['category']}")

                    if pd.notna(row['subject']):
                        st.write(f"**Subject:** {row['subject']}")

                    if pd.notna(row['sentiment']):
                        st.write(f"**Sentiment:** {row['sentiment']}")

                    if pd.notna(row['industry_affiliation']):
                        st.write(f"**Industry Affiliation:** {row['industry_affiliation']}")

                    if pd.notna(row.get('evaluation_score')):
                        st.write(f"**Quality Score:** {row['evaluation_score']}%")

                    if pd.notna(row.get('stage')):
                        st.write(f"**Stage:** {row['stage']}")

            # DOI link
            if pd.notna(row['doi']):
                st.write(f"**DOI:** [{row['doi']}](https://doi.org/{row['doi']})")

    # Export option
    st.divider()
    if st.button("Export to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"articles_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
