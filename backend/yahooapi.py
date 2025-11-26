import requests

url = f"https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1m&range=1d"
data = requests.get(url).json()