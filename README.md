# TrendSignal

A real-time stock analysis tool that monitors technical indicators and provides scoring based on market signals.

## Features (MVP)

- Real-time stock data fetching using Alpha Vantage API
- Cryptocurrency data support with robust error handling
- Technical analysis including MACD and EMA indicators
- Scoring system based on technical indicators
- Data persistence using SQLite with intelligent caching
- Interactive Streamlit dashboard with improved user experience
- Comprehensive error handling and logging
- Automated testing with 100% test coverage
- API rate limit management and fallback mechanisms
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

# Optional: Install coverage tools for detailed test reports
pip install pytest-cov
```

4. Create a `.env` file in the root directory with your Alpha Vantage API key:
```
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

## Usage

1. Start the Streamlit dashboard (for quick development):
```bash
PYTHONPATH=. streamlit run src/app.py
```

2. Enter a stock symbol (e.g., AAPL) or cryptocurrency symbol (e.g., BTC) and select the time interval in the sidebar
3. Choose between Stock and Cryptocurrency market types
4. Optionally enable "Force Refresh" to bypass cache and fetch fresh data
5. View the technical analysis results, charts, and scoring
6. The application automatically handles API rate limits and uses cached data when available

## Key Capabilities

- **Intelligent Caching**: Automatically caches data to minimize API calls and improve performance
- **Error Recovery**: Gracefully handles API rate limits, network issues, and invalid symbols  
- **Dual Market Support**: Supports both traditional stocks and cryptocurrencies
- **Real-time Analysis**: Provides immediate technical analysis with visual charts
- **Automated Testing**: Comprehensive test suite ensures reliability and stability

## Testing

### Running Tests

The project includes a comprehensive test suite with 100% pass rate covering all major functionality:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests with verbose output
PYTHONPATH=. python -m pytest tests/ -v

# Run specific test modules
PYTHONPATH=. python -m pytest tests/test_data_fetcher.py -v
PYTHONPATH=. python -m pytest tests/test_app.py -v
PYTHONPATH=. python -m pytest tests/test_error_handling.py -v

# Run tests with coverage report
PYTHONPATH=. python -m pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite covers:

- **Data Fetching**: API integration, caching mechanisms, error handling
- **Technical Analysis**: MACD, EMA, RSI calculations and scoring algorithms  
- **Database Operations**: Data persistence, cache management, timestamp handling
- **Error Handling**: Rate limits, network failures, invalid symbols, malformed responses
- **UI Components**: Streamlit app functions, chart generation, user interactions
- **Dependencies**: Import validation and module compatibility

### Test Categories

- **Unit Tests**: Individual function and method testing
- **Integration Tests**: API interactions and database operations
- **Error Handling Tests**: Comprehensive failure scenario coverage
- **Cache Tests**: Intelligent caching behavior validation
- **Crypto Tests**: Cryptocurrency-specific functionality

### Continuous Validation

Before committing changes, ensure all tests pass:

```bash
# Quick validation
PYTHONPATH=. python -c "
import src.app, src.data_fetcher, src.database, src.technical_analysis
print('✅ All modules import successfully')
"

# Full test suite
PYTHONPATH=. python -m pytest tests/ -v
```

## Project Structure

```
trend-signal/
├── config/
│   └── config.py         # Configuration settings
├── data/                 # SQLite database storage
├── docs/
│   ├── implementation_plan.md  # Feature tracking and roadmap
│   └── system.md              # Trading strategy notes
├── src/
│   ├── app.py           # Streamlit dashboard
│   ├── data_fetcher.py  # Alpha Vantage API integration
│   ├── database.py      # Database models and management
│   └── technical_analysis.py  # Technical indicators and scoring
├── tests/               # Comprehensive test suite
│   ├── test_app.py             # UI component and workflow tests
│   ├── test_data_fetcher.py    # API integration and caching tests
│   ├── test_error_handling.py  # Error condition and recovery tests
│   ├── test_technical_analysis.py  # Algorithm and calculation tests
│   ├── test_crypto_fetcher.py  # Cryptocurrency-specific tests
│   └── test_dependencies.py   # Import and compatibility tests
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