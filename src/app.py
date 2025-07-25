import streamlit as st
import pandas as pd
from src.data_fetcher import DataFetcher, InvalidSymbolError, APIError, DataFetcherError
from src.technical_analysis import TechnicalAnalyzer
from src.database import DatabaseManager
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def analyze_symbol(symbol: str, interval: str, market_type: str, force_refresh: bool = False):
    """Analyze the selected symbol and display results"""
    try:
        fetcher = DataFetcher()

        if not symbol:
            st.warning("Please enter a symbol")
            return

        try:
            data = fetcher.get_intraday_data(
                symbol=symbol,
                interval=interval,
                market_type=market_type.lower(),
                force_refresh=force_refresh
            )

            if data is None or data.empty:
                st.error(f"No data available for {symbol}")
                return

            # Perform technical analysis
            analyzer = TechnicalAnalyzer(data)
            analysis_results = analyzer.analyze()

            # Return both data and analysis results
            return data, analysis_results

        except InvalidSymbolError as e:
            st.error(str(e))
        except APIError as e:
            st.error(f"API Error: {str(e)}")
        except DataFetcherError as e:
            st.error(f"Data Error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in analyze_symbol: {str(e)}", exc_info=True)
            st.error(f"An unexpected error occurred: {str(e)}")
    finally:
        if 'fetcher' in locals():
            fetcher.close()

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

    # Add debug information
    st.sidebar.divider()
    st.sidebar.markdown("### Debug Info")
    st.sidebar.text(f"Current symbol: {symbol}")
    st.sidebar.text(f"Market type: {market_type}")
    st.sidebar.text(f"Interval: {interval}")
    st.sidebar.text(f"Force refresh: {force_refresh}")

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Analysis", "Market Movers"])

    with tab1:
        # Run analysis when the page loads or when inputs change
        result = analyze_symbol(symbol, interval, market_type, force_refresh)

        if result:
            data, analysis_results = result

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
                st.dataframe(data.head())

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