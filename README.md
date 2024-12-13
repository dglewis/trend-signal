# TrendSignal

A real-time stock analysis tool that monitors technical indicators and provides scoring based on market signals.

## Features (MVP)

- Real-time stock data fetching using Alpha Vantage API
- Technical analysis including MACD and EMA indicators
- Scoring system based on technical indicators
- Data persistence using SQLite
- Interactive Streamlit dashboard
- Basic alerting system

## Setup

1. Clone the repository:
```bash
git clone https://github.com/dglewis/trend-signal.git
cd trend-signal
```

2. Create a virtual environment and activate it:
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Alpha Vantage API key:
```
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

## Usage

1. Start the Streamlit dashboard:
```bash
streamlit run src/app.py
```

2. Enter a stock symbol and select the time interval in the sidebar
3. Click "Analyze" to fetch and analyze the data
4. View the technical analysis results and charts

## Project Structure

```
trend-signal/
├── config/
│   └── config.py         # Configuration settings
├── data/                 # SQLite database storage
├── src/
│   ├── app.py           # Streamlit dashboard
│   ├── data_fetcher.py  # Alpha Vantage API integration
│   ├── database.py      # Database models and management
│   └── technical_analysis.py  # Technical indicators and scoring
├── tests/               # Test files
├── .env                 # Environment variables (create this)
├── requirements.txt     # Project dependencies
└── README.md           # This file
```

## Security Note

- Never commit your `.env` file or expose your API keys
- This tool is for educational and research purposes only
- Always verify the analysis with other sources before making investment decisions

## License

MIT License