import os
import requests
import time
from datetime import datetime

TOKEN = os.environ.get("BOT_TOKEN", "")

def calc_sma(arr, p):
    if len(arr) < p:
        return None
    return sum(arr[-p:]) / p

def calc_rsi(closes, p=14):
    if len(closes) < p + 1:
        return None
    gains, losses = 0, 0
    for i in range(len(closes) - p, len(closes)):
        d = closes[i] - closes[i-1]
        if d > 0: gains += d
        else: losses += abs(d)
    ag, al = gains/p, losses/p
    if al == 0: return 100
    return round(100 - 100/(1 + ag/al))

def calc_macd(closes):
    if len(closes) < 26:
        return None
    def ema(arr, p):
        k = 2/(p+1)
        e = arr[0]
        for x in arr[1:]: e = x*k + e*(1-k)
        return e
    return ema(closes[-12:], 12) - ema(closes[-26:], 26)

def calc_stoch(highs, lows, closes, p=14):
    if len(closes) < p:
        return None
    hh = max(highs[-p:])
    ll = min(lows[-p:])
    if hh == ll: return 50
    return round((closes[-1] - ll) / (hh - ll) * 100)

def get_btc_data():
    try:
        klines = requests.get(
            "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=200",
            timeout=10
        ).json()
        ticker = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT",
            timeout=10
        ).json()
        fear_raw = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10).json()

        closes = [float(k[4]) for k in klines]
        highs  = [float(k[2]) for k in klines]
        lows   = [float(k[3]) for k in klines]
        prev   = klines[-2]

        price  = float(ticker["lastPrice"])
        change = float(ticker["priceChangePercent"])
        vol    = float(ticker["quoteVolume"])

        rsi   = calc_rsi(closes)
        macd  = calc_macd(closes)
        stoch = calc_stoch(highs, lows, closes)
        ma50  = calc_sma(closes, 50)
        ma100 = calc_sma(closes, 100)
        ma200 = calc_sma(closes, 200)

        ph = float(prev[2])
        pl = float(prev[3])
        pc = float(prev[4])
        pp = (ph + pl + pc) / 3

        fear_val = int(fear_raw["data"][0]["value"])
        fear_lab = fear_raw["data"][0]["value_classification"]

        trend = "боковик"
        if ma50 and ma200:
            if price > ma50 and price > ma200 and ma50 > ma200:
                trend = "БЫЧИЙ"
            elif price < ma50 and price < ma200:
                trend = "МЕДВЕЖИЙ"

        verdict = "ВОЗДЕРЖАТЬСЯ"
        if rsi and stoch:
            if rsi < 35 and stoch < 25:
                verdict = "ВОЗМОЖЕН ЛОНГ"
            elif rsi > 70 and stoch > 80:
                verdict = "ОСТОРОЖНО ПЕРЕКУПЛЕН"

        now = datetime.utcnow().strftime("%d.%m.%Y %H:%M UTC")

        msg = (
            f"BTC АНАЛИТИК | {now}\n\n"
            f"ЦЕНА: ${price:,.0f} ({'+' if change >= 0 else ''}{change:.2f}%)\n"
            f"Объём 24ч: ${vol/1e9:.1f}B\n"
            f"Тренд: {trend}\n\n"
            f"ОСЦИЛЛЯТОРЫ\n"
            f"RSI(14): {rsi if rsi else '—'}\n"
            f"Stochastic: {stoch if stoch else '—'}\n"
            f"MACD: {'бычий' if macd and macd > 0 else 'медвежий'}\n\n"
            f"СКОЛЬЗЯЩИЕ СРЕДНИЕ\n"
            f"MA50:  ${ma50:,.0f} ({'выше' if ma50 and price > ma50 else 'ниже'})\n"
            f"MA100: ${ma100:,.0f} ({'выше' if ma100 and price > ma100 else 'ниже'})\n"
            f"MA200: ${ma200:,.0f} ({'выше' if ma200 and price > ma200 else 'ниже'})\n\n"
            f"ПИВОТЫ\n"
            f"R3: ${pp + 2*(ph-pl):,.0f}\n"
            f"R2: ${pp + (ph-pl):,.0f}\n"
            f"R1: ${2*pp - pl:,.0f}\n"
            f"P:  ${pp:,.0f}\n"
            f"S1: ${2*pp - ph:,.0f}\n"
            f"S2: ${pp - (ph-pl):,.0f}\n"
            f"S3: ${pl - 2*(ph-pp):,.0f}\n\n"
            f"СТРАХ И ЖАДНОСТЬ: {fear_val}/100 — {fear_lab}\n\n"
            f"ВЕРДИКТ: {verdict}"
        )
        return msg
    except Exception as e:
        return f"Ошибка: {str(e)}"

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        return r.json()
    except:
        return {"result": []}

def main():
    print("BTC Bot запущен")
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates.get("result", []):
            of
