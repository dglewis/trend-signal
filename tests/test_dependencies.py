import pytest

def test_required_dependencies():
    """Test that all required dependencies are installed and can be imported."""
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'alpha_vantage',
        'ta',
        'sqlalchemy',
        'dotenv'
    ]

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError as e:
            pytest.fail(f"Required package '{package}' is not installed: {str(e)}")

def test_app_imports():
    """Test that all imports in the main app file work."""
    try:
        import streamlit as st
        import pandas as pd
        import plotly.graph_objects as go
        from src.data_fetcher import DataFetcher
        from src.technical_analysis import TechnicalAnalyzer
        from src.database import DatabaseManager
    except ImportError as e:
        pytest.fail(f"Failed to import required module: {str(e)}")

def test_specific_imports():
    """Test specific imports that might have different import names than package names."""
    try:
        from dotenv import load_dotenv
    except ImportError as e:
        pytest.fail(f"Failed to import dotenv: {str(e)}")