import numpy as np
import matplotlib.pyplot as plt

class StockMomentumAnalyzer:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_ema(self, prices, window):
        if len(prices) < window:
            return None
        ema = [np.mean(prices[:window])]
        multiplier = 2 / (window + 1)
        for price in prices[window:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        return ema

    def calculate_rsi(self, prices, period=14):
        if len(prices) < period:
            return 50
        gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
        losses = [abs(min(prices[i] - prices[i-1], 0)) for i in range(1, len(prices))]
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100
        if avg_gain == 0:
            return 0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def percentage_change(self, current, previous):
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100

    def extract_signal_vector(self, stock):
        if stock not in self.stock_data or self.stock_data[stock].is_empty():
            print(f"[DEBUG] No data for stock {stock}. Returning neutral signals.")
            return {
                "sma_diff": 0,
                "rsi": 50,
                "macd_hist": 0,
                "price_change": 0,
                "volume_ratio": 1
            }

        prices, volumes = [], []

        def traverse(node):
            if node is None:
                return
            traverse(node.left)
            prices.append(node.close_price)
            volumes.append(node.volume)
            traverse(node.right)

        traverse(self.stock_data[stock].root)

        if len(prices) < 50:
            print(f"[DEBUG] Not enough data points for {stock}. Need 50, got {len(prices)}")
            return {
                "sma_diff": 0,
                "rsi": 50,
                "macd_hist": 0,
                "price_change": 0,
                "volume_ratio": 1
            }

        sma_short = np.mean(prices[-10:])
        sma_long = np.mean(prices[-50:])
        sma_diff = sma_short - sma_long
        # print(f"[DEBUG] {stock} SMA(10)={sma_short:.2f}, SMA(50)={sma_long:.2f}, SMA Diff={sma_diff:.4f}")

        rsi = self.calculate_rsi(prices)
        # print(f"[DEBUG] {stock} RSI={rsi:.2f}")

        ema_12 = self.calculate_ema(prices, 12)
        ema_26 = self.calculate_ema(prices, 26)
        macd_hist = 0
        if ema_12 and ema_26:
            macd = np.array(ema_12[-len(ema_26):]) - np.array(ema_26)
            signal = self.calculate_ema(macd.tolist(), 9)
            if signal:
                macd_hist = macd[-1] - signal[-1]
        # print(f"[DEBUG] {stock} MACD Hist={macd_hist:.4f}")

        last_price = prices[-1]
        prev_price = prices[-2] if len(prices) > 1 else last_price
        price_change = self.percentage_change(last_price, prev_price)
        # print(f"[DEBUG] {stock} Last Price={last_price:.2f}, Prev Price={prev_price:.2f}, % Change={price_change:.2f}")

        avg_vol = np.mean(volumes[-20:])
        volume_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1
        # print(f"[DEBUG] {stock} Volume Ratio={volume_ratio:.4f} (Latest={volumes[-1]}, Avg20={avg_vol:.2f})")

        signal_vector = {
            "sma_diff": sma_diff,
            "rsi": rsi,
            "macd_hist": macd_hist,
            "price_change": price_change,
            "volume_ratio": volume_ratio
        }

        # print(f"[DEBUG] Final Signal Vector for {stock}: {signal_vector}")
        # print("===")

        return signal_vector

    def is_buy_signal(self, stock):
        signal = self.extract_signal_vector(stock)
        return (
            signal["sma_diff"] > 0 and
            40 < signal["rsi"] < 70 and
            signal["macd_hist"] > 0 and
            signal["price_change"] > 0 and
            signal["volume_ratio"] > 1
        )

    def score_for_buying(self, stock):
        signal = self.extract_signal_vector(stock)
        score = 0
        if signal["sma_diff"] > 0: score += 20
        if 40 < signal["rsi"] < 70: score += 20
        if signal["macd_hist"] > 0: score += 20
        if signal["price_change"] > 0: score += 20
        if signal["volume_ratio"] > 1: score += 20
        return min(score, 100)
