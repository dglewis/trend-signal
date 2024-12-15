import streamlit as st
import pandas as pd
from data_fetcher import DataFetcher, InvalidSymbolError, APIError, DataFetcherError
from technical_analysis import TechnicalAnalyzer
from database import DatabaseManager
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

st.set_page_config(page_title="TrendSignal", page_icon="📈", layout="wide")

# Technical terms tooltips
TOOLTIPS = {
    'technical_score': """
    Overall technical analysis score (0-100) based on multiple indicators:
    - MACD trend
    - EMA crossovers
    - Volume trends
    - Price momentum
    """,
    'macd': """
    Moving Average Convergence Divergence (MACD):
    A trend-following momentum indicator that shows the relationship between two moving averages of a security's price.
    - Positive MACD indicates upward momentum
    - Negative MACD indicates downward momentum
    """,
    'ema_short': """
    Short-term Exponential Moving Average (EMA):
    A type of moving average that places greater weight on recent data.
    The short-term EMA (12 periods) responds more quickly to price changes.
    """,
    'ema_long': """
    Long-term Exponential Moving Average (EMA):
    A type of moving average that places greater weight on recent data.
    The long-term EMA (26 periods) shows the longer-term trend direction.
    """,
    'crypto_volume': """
    Cryptocurrency Trading Volume:
    24-hour trading volume in USD.
    Higher volumes typically indicate more market activity and liquidity.
    """
}

def create_candlestick_chart(df, title="Price Chart"):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['1. open'] if '1. open' in df.columns else df['4. close'],
                high=df['2. high'] if '2. high' in df.columns else df['4. close'],
                low=df['3. low'] if '3. low' in df.columns else df['4. close'],
                close=df['4. close'])])
    fig.update_layout(title=title, xaxis_title='Date', yaxis_title='Price')
    return fig

def display_error(message: str, level: str = "error"):
    """Display an error message with the appropriate styling"""
    if level == "error":
        st.error(f"❌ {message}")
    elif level == "warning":
        st.warning(f"⚠️ {message}")
    else:
        st.info(f"ℹ️ {message}")

def main():
    st.title("TrendSignal - Market Analysis Dashboard")

    # Initialize DataFetcher for crypto list
    fetcher = DataFetcher()

    # Sidebar
    st.sidebar.header("Settings")

    # Market type selection
    market_type = st.sidebar.radio(
        "Select Market Type",
        options=['Stock', 'Cryptocurrency'],
        index=0,
        help="Choose between stock market or cryptocurrency analysis"
    )

    # Symbol input based on market type
    if market_type == 'Cryptocurrency':
        try:
            crypto_list = fetcher.get_crypto_list()
            symbol = st.sidebar.selectbox(
                "Select Cryptocurrency",
                options=crypto_list,
                help="Choose from popular cryptocurrencies"
            )
        except Exception as e:
            logger.error(f"Error fetching crypto list: {str(e)}")
            symbol = st.sidebar.text_input("Enter Cryptocurrency Symbol", value="BTC").upper()
            st.sidebar.info("⚠️ Using manual input due to API error")
    else:
        symbol = st.sidebar.text_input("Enter Stock Symbol", value="AAPL").upper()

    interval = st.sidebar.selectbox(
        "Select Time Interval",
        options=['1min', '5min', '15min', '30min', '60min'],
        index=1
    )

    # Add force refresh option
    force_refresh = st.sidebar.checkbox(
        "Force Data Refresh",
        value=False,
        help="If checked, bypass cache and fetch fresh data from API"
    )

    # Function to perform analysis
    def analyze_symbol():
        try:
            # Input validation
            if not symbol:
                display_error("Please enter a symbol")
                return None

            # Fetch and analyze data
            data = fetcher.get_intraday_data(
                symbol=symbol,
                interval=interval,
                market_type='crypto' if market_type == 'Cryptocurrency' else 'stock',
                force_refresh=force_refresh
            )

            if data is None or data.empty:
                display_error(f"No data available for {symbol}")
                return None

            analyzer = TechnicalAnalyzer(data)
            analysis_results = analyzer.analyze()

            # Save to database
            db = DatabaseManager()
            db.save_analysis(symbol, analysis_results)

            return data, analysis_results
        except InvalidSymbolError as e:
            display_error(str(e))
            return None
        except APIError as e:
            if "rate limit" in str(e).lower():
                display_error("API rate limit reached. Please wait a moment and try again.", "warning")
                # Try to get data from cache with extended age
                try:
                    cached_data = fetcher.db.get_cached_data(symbol, max_age_minutes=30)
                    if cached_data is not None:
                        display_error("Using cached data due to rate limit", "info")
                        return pd.DataFrame.from_dict(cached_data), None
                except Exception as cache_e:
                    logger.error(f"Error getting cached data: {str(cache_e)}")
            else:
                display_error(f"API Error: {str(e)}")
            return None
        except Exception as e:
            display_error(f"An unexpected error occurred: {str(e)}")
            logger.error(f"Error in analyze_symbol: {str(e)}", exc_info=True)
            return None

    # Add debug information
    st.sidebar.divider()
    st.sidebar.markdown("### Debug Info")
    if 'last_symbol' in st.session_state:
        st.sidebar.text(f"Last symbol: {st.session_state.last_symbol}")
    if hasattr(st.session_state, 'last_analysis'):
        st.sidebar.text("Analysis data: Available")
    else:
        st.sidebar.text("Analysis data: None")

    # Analyze button (kept for explicit analysis)
    if st.sidebar.button("Analyze"):
        result = analyze_symbol()
        if result:
            data, analysis_results = result
            st.session_state.last_analysis = (data, analysis_results)
        else:
            st.session_state.last_analysis = None

    # Auto-analyze when symbol changes
    if 'last_symbol' not in st.session_state or st.session_state.last_symbol != symbol:
        st.session_state.last_symbol = symbol
        result = analyze_symbol()
        if result:
            st.session_state.last_analysis = result

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Analysis", "Market Movers"])

    with tab1:
        if hasattr(st.session_state, 'last_analysis') and st.session_state.last_analysis:
            data, analysis_results = st.session_state.last_analysis

            # Display cache status
            if not force_refresh:
                st.info("✨ Using cached data (if available)")
            else:
                st.info("🔄 Using fresh data from API")

            if analysis_results:  # Only show metrics if we have analysis results
                # Display results with tooltips
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Technical Score",
                        f"{analysis_results['score']:.2f}",
                        help=TOOLTIPS['technical_score']
                    )
                with col2:
                    st.metric(
                        "MACD",
                        f"{analysis_results['macd']:.2f}",
                        help=TOOLTIPS['macd']
                    )
                with col3:
                    st.metric(
                        "Short EMA",
                        f"{analysis_results['ema_short']:.2f}",
                        help=TOOLTIPS['ema_short']
                    )
                with col4:
                    st.metric(
                        "Long EMA",
                        f"{analysis_results['ema_long']:.2f}",
                        help=TOOLTIPS['ema_long']
                    )

            # Display chart with appropriate title
            chart_title = f"{symbol} {'Cryptocurrency' if market_type == 'Cryptocurrency' else 'Stock'} Price"
            st.plotly_chart(create_candlestick_chart(data, title=chart_title), use_container_width=True)

            # Display recent data
            with st.expander("Recent Data"):
                st.dataframe(data.tail())

    with tab2:
        try:
            if market_type == 'Cryptocurrency':
                st.info("Note: Market movers data is currently only available for US stocks")
                return

            gainers, losers = fetcher.get_top_gainers_losers()

            # Create two columns for gainers and losers
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🔼 Top Gainers")
                if gainers:
                    gainers_df = pd.DataFrame(gainers)
                    st.dataframe(
                        gainers_df[['ticker', 'price', 'change_percentage']],
                        column_config={
                            'ticker': 'Symbol',
                            'price': 'Price ($)',
                            'change_percentage': 'Change (%)'
                        },
                        hide_index=True
                    )
                else:
                    st.info("No gainers data available")

            with col2:
                st.subheader("🔽 Top Losers")
                if losers:
                    losers_df = pd.DataFrame(losers)
                    st.dataframe(
                        losers_df[['ticker', 'price', 'change_percentage']],
                        column_config={
                            'ticker': 'Symbol',
                            'price': 'Price ($)',
                            'change_percentage': 'Change (%)'
                        },
                        hide_index=True
                    )
                else:
                    st.info("No losers data available")

        except (APIError, DataFetcherError) as e:
            display_error(f"Error fetching market movers: {str(e)}", "warning")

if __name__ == "__main__":
    main()