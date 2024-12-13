import streamlit as st
import pandas as pd
from data_fetcher import DataFetcher
from technical_analysis import TechnicalAnalyzer
from database import DatabaseManager
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="TrendSignal", page_icon="📈", layout="wide")

def create_candlestick_chart(df):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['1. open'],
                high=df['2. high'],
                low=df['3. low'],
                close=df['4. close'])])
    fig.update_layout(title='Price Chart', xaxis_title='Date', yaxis_title='Price')
    return fig

def main():
    st.title("TrendSignal - Stock Analysis Dashboard")

    # Sidebar
    st.sidebar.header("Settings")
    symbol = st.sidebar.text_input("Enter Stock Symbol", value="AAPL").upper()
    interval = st.sidebar.selectbox(
        "Select Time Interval",
        options=['1min', '5min', '15min', '30min', '60min'],
        index=1
    )

    if st.sidebar.button("Analyze"):
        try:
            # Fetch and analyze data
            fetcher = DataFetcher()
            data = fetcher.get_intraday_data(symbol, interval)

            analyzer = TechnicalAnalyzer(data)
            analysis_results = analyzer.analyze()

            # Save to database
            db = DatabaseManager()
            db.save_analysis(symbol, analysis_results)

            # Display results
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Technical Score", f"{analysis_results['score']:.2f}")
            with col2:
                st.metric("MACD", f"{analysis_results['macd']:.2f}")
            with col3:
                st.metric("Short EMA", f"{analysis_results['ema_short']:.2f}")
            with col4:
                st.metric("Long EMA", f"{analysis_results['ema_long']:.2f}")

            # Display chart
            st.plotly_chart(create_candlestick_chart(data), use_container_width=True)

            # Display recent data
            st.subheader("Recent Data")
            st.dataframe(data.tail())

        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()