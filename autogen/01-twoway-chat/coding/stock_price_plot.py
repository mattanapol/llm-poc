# filename: stock_price_plot.py
import yfinance as yf
import matplotlib.pyplot as plt

# Fetch historical stock price data for META and TESLA
meta_stock = yf.Ticker("META")
tesla_stock = yf.Ticker("TSLA")

meta_data = meta_stock.history(period="1y")
tesla_data = tesla_stock.history(period="1y")

# Plotting stock price change for META
plt.figure(figsize=(12, 6))
plt.plot(meta_data.index, meta_data['Close'], label='META')
plt.xlabel('Date')
plt.ylabel('Stock Price')
plt.title('META Stock Price Change')
plt.legend()
plt.grid(True)
plt.show()

# Plotting stock price change for TESLA
plt.figure(figsize=(12, 6))
plt.plot(tesla_data.index, tesla_data['Close'], label='TESLA', color='r')
plt.xlabel('Date')
plt.ylabel('Stock Price')
plt.title('TESLA Stock Price Change')
plt.legend()
plt.grid(True)
plt.show()