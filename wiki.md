# Project Summary
Wujila is a stock analysis application built using Streamlit, designed to provide real-time stock price queries and technical analysis for both Taiwanese and American stocks. It offers users the ability to visualize stock trends, analyze financial indicators, and receive investment suggestions based on market data.

# Project Module Description
The application consists of several functional modules:
- **Stock Price Query**: Users can input stock tickers to retrieve real-time data for Taiwanese and American stocks.
- **Technical Analysis**: The app computes and displays various indicators such as moving averages (MA5, MA10, MA20) and KD indicators.
- **Visualization**: Provides graphical representations of stock data, including candlestick charts and volume metrics.

# Directory Tree
```
README.md         - Documentation for usage and features
app.py            - Main application code for stock analysis
public/images/    - Contains images used in the application
requirements.txt  - Lists required Python packages
```

# File Description Inventory
1. **app.py** - The core application file that contains the logic for stock analysis, data retrieval, and user interface elements.
2. **requirements.txt** - A file specifying the dependencies needed to run the application.
3. **README.md** - Provides an overview of the project, installation instructions, and usage guidelines.

# Technology Stack
- **Streamlit**: For building the web application interface.
- **yfinance**: For retrieving stock market data.
- **Pandas**: For data manipulation and analysis.
- **NumPy**: For numerical operations.
- **Plotly**: For creating interactive visualizations.

# Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   streamlit run app.py
   ```
