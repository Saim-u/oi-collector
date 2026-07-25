import os, time, requests, pandas as pd

URL = "https://fapi.binance.com/futures/data/openInterestHist"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
PERIOD = "5m"
OUT = "data/oi"

def fetch(symbol):
    end = int(time.time() * 1000)
    start = end - 48 * 3600 * 1000
    r = requests.get(URL, params={
        "symbol": symbol, "period": PERIOD,
        "startTime": start, "endTime": end, "limit": 500,
    }, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    for c in ("sumOpenInterest", "sumOpenInterestValue"):
        df[c] = df[c].astype(float)
    return df.set_index("timestamp").sort_index()

def main():
    os.makedirs(OUT, exist_ok=True)
    for sym in SYMBOLS:
        path = f"{OUT}/{sym}_{PERIOD}.parquet"
        try:
            new = fetch(sym)
        except Exception as e:
            print(f"FAIL {sym}: {e}")
            continue
        if new.empty:
            print(f"EMPTY {sym}")
            continue
        if os.path.exists(path):
            old = pd.read_parquet(path)
            new = pd.concat([old, new])
            new = new[~new.index.duplicated(keep="last")].sort_index()
        new.to_parquet(path)
        gaps = new.index.to_series().diff()
        big = gaps[gaps > pd.Timedelta("15min")]
        print(f"{sym}: {len(new)} rows, {len(big)} gaps, latest {new.index[-1]}")
        time.sleep(0.3)

if __name__ == "__main__":
    main()
