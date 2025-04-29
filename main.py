
import requests
import time
from datetime import datetime
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.trend import ADXIndicator, EMAIndicator
import telegram
import os

# Wczytaj dane z sekretnych zmiennych
TD_API_KEY = os.getenv("TD_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = {
    "EUR/USD": "EUR/USD",
    "GBP/JPY": "GBP/JPY",
    "EUR/JPY": "EUR/JPY",
    "AUD/JPY": "AUD/JPY",
    "USD/CHF": "USD/CHF"
}

INTERVAL = "5min"
TRIGGER_POINTS = 4

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def fetch_candles(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={INTERVAL}&outputsize=50&apikey={TD_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "values" not in data:
        raise Exception(f"Błąd danych dla {symbol}: {data.get('message', data)}")
    df = pd.DataFrame(data["values"])[::-1]
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['open'] = pd.to_numeric(df['open'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

def analyze(df):
    points = 0
    close = df['close']
    rsi = RSIIndicator(close=close).rsi()
    if rsi.iloc[-1] < 30: points += 1
    elif rsi.iloc[-1] > 70: points += 1
    bb = BollingerBands(close)
    if close.iloc[-1] < bb.bollinger_lband().iloc[-1]: points += 1
    elif close.iloc[-1] > bb.bollinger_hband().iloc[-1]: points += 1
    stoch = StochasticOscillator(df['high'], df['low'], df['close'])
    if stoch.stoch_signal().iloc[-1] < 20: points += 1
    elif stoch.stoch_signal().iloc[-1] > 80: points += 1
    adx = ADXIndicator(df['high'], df['low'], df['close'])
    if adx.adx().iloc[-1] > 25: points += 1
    ema_fast = EMAIndicator(close, window=10).ema_indicator()
    ema_slow = EMAIndicator(close, window=30).ema_indicator()
    if ema_fast.iloc[-1] > ema_slow.iloc[-1]: points += 1
    return points

def send_signal(pair, points):
    now = datetime.now().strftime('%H:%M:%S')
    signal = f"Sygnał dla {pair} o {now}\nPunkty: {points}/6"
    if points >= TRIGGER_POINTS:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=signal)

def main_loop():
    for pair, symbol in PAIRS.items():
        try:
            df = fetch_candles(symbol)
            points = analyze(df)
            send_signal(pair, points)
        except Exception as e:
            print(f"[BŁĄD] {pair}: {e}")
    print(f"--- Cykle zakończone {datetime.now()} ---")

if __name__ == "__main__":
    main_loop()
