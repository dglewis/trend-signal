import streamlit as st
import pandas as pd
from data_fetcher import DataFetcher, InvalidSymbolError, APIError, DataFetcherError
from technical_analysis import TechnicalAnalyzer
from database import DatabaseManager
import plotly.graph_objects as go
from datetime import datetime, timedelta

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

def display_error(error_message: str, error_type: str = "error"):
    """Display an error message with appropriate styling"""
    if error_type == "warning":
        st.warning(error_message, icon="⚠️")
    else:
        st.error(error_message, icon="🚨")

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
        crypto_list = fetcher.get_crypto_list()
        symbol = st.sidebar.selectbox(
            "Select Cryptocurrency",
            options=crypto_list,
            help="Choose from popular cryptocurrencies"
        )
    else:
        symbol = st.sidebar.text_input("Enter Stock Symbol", value="AAPL").upper()

    interval = st.sidebar.selectbox(
        "Select Time Interval",
        options=['1min', '5min', '15min', '30min', '60min'],
        index=1
    )

    if st.sidebar.button("Analyze"):
        try:
            # Input validation
            if not symbol:
                display_error("Please enter a symbol")
                return

            # Fetch and analyze data
            data = fetcher.get_intraday_data(
                symbol=symbol,
                interval=interval,
                market_type='crypto' if market_type == 'Cryptocurrency' else 'stock'
            )

            analyzer = TechnicalAnalyzer(data)
            analysis_results = analyzer.analyze()

            # Save to database
            db = DatabaseManager()
            db.save_analysis(symbol, analysis_results)

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
            st.subheader("Recent Data")
            st.dataframe(data.tail())

        except InvalidSymbolError as e:
            display_error(f"Invalid symbol: {symbol}. Please enter a valid symbol.")

        except APIError as e:
            if "rate limit" in str(e).lower():
                display_error("API rate limit reached. Please wait a moment and try again.", "warning")
            else:
                display_error(f"API Error: {str(e)}")

        except DataFetcherError as e:
            display_error(f"Error fetching data: {str(e)}")

        except Exception as e:
            display_error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()