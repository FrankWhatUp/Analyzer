import numpy as np
import random
import pickle
from datetime import datetime, timedelta
from FinbertNews import FinbertNews

class QLearningAgent:
    def __init__(self, actions=["Buy", "Hold", "Sell"], learning_rate=0.3, discount_factor=0.8, exploration_rate=0.8, initial_equity=None, start_date = None):
        self.q_table = {}
        self.actions = actions
        self.alpha = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.equity = initial_equity
        self.settled_cashA = initial_equity/2
        self.settled_cashB = initial_equity/2
        self.pending_settlements = []
        self.newsEstimate = FinbertNews()  # Instantiate the class
        self.start_date = start_date

    def get_state_key(self, signal_vector, position, news_text=None, stock_symbol=None, bins_per_signal=5):
        """
        Converts continuous signal_vector and sentiment to a discrete state key.
        Adds a sentiment bin based on FinBERT estimation.
        """
        discrete_state = []

        # --- Technical Indicators ---
        for key in ["sma_diff", "rsi", "macd_hist", "price_change", "volume_ratio"]:
            val = signal_vector[key]
            if key == "rsi":
                norm = (val - 50) / 50
            elif key == "volume_ratio":
                norm = (val - 1) / 2
            elif key == "sma_diff":
                norm = np.tanh(val / 0.5)
            elif key == "macd_hist":
                norm = np.tanh(val / 0.01)
            else:
                norm = np.tanh(val / 1.0)

            capped = max(min(norm, 1), -1)
            bin_index = int((capped + 1) / 2 * bins_per_signal)
            bin_index = min(max(bin_index, 0), bins_per_signal - 1)

            # print(f"[DEBUG] {key.upper():<12} val={val:.4f}, norm={norm:.4f}, capped={capped:.4f}, bin={bin_index}")
            discrete_state.append(bin_index)

        # --- Sentiment Estimation ---
        sentiment_bin = 2  # Default: neutral
        if news_text:
            prob, sentiment = self.newsEstimate.estimate_sentiment(news_text)
            sentiment_bin = {"positive": 0, "negative": 1, "neutral": 2}.get(sentiment, 2)
            # print(f"[DEBUG] SENTIMENT for {stock_symbol}: {sentiment} (prob={prob:.2f}) → bin={sentiment_bin}")
        else:
             print(f"[DEBUG] No news provided for {stock_symbol}, defaulting to 'neutral' bin=2")

        discrete_state.append(sentiment_bin)

        # --- Position State ---
        position_bin = 1 if position == "holding" else 0
        discrete_state.append(position_bin)

        # print(f"[DEBUG] Final state key: {tuple(discrete_state)}\n")
        return tuple(discrete_state)

    def choose_action(self, state_key, stock_symbol, current_price=None,posInfo =None):
        current_position = posInfo

        valid_actions = []
        for action in self.actions:
            if current_position == "flat":
                if action == "Sell":
                    continue  # Can't sell if not holding
                if action == "Buy" and current_price is not None:
                    if not self.can_afford_trade(current_price):
                        continue  # Can't afford this trade
            if current_position == "holding" and action == "Buy":
                continue  # Can't buy if already holding
            valid_actions.append(action)

        if not valid_actions:
            return "Hold"

        if random.random() < self.epsilon:
            return random.choice(valid_actions)

        q_vals = [self.q_table.get((state_key, a), 0.0) for a in valid_actions]
        print(f"[DEBUG] State: {state_key}, Q-vals: {[self.q_table.get((state_key, a), 0.0) for a in valid_actions]}, Valid: {valid_actions}")
        return valid_actions[np.argmax(q_vals)]

    def update(self, state_key, action, reward, next_state_key):
        current_q = self.q_table.get((state_key, action), 0.0)
        max_next_q = max([self.q_table.get((next_state_key, a), 0.0) for a in self.actions])
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[(state_key, action)] = new_q

    def save_q_table(self, filename="q_table.pkl"):
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load_q_table(self, filename="q_table.pkl"):
        try:
            with open(filename, 'rb') as f:
                self.q_table = pickle.load(f)
            print(f"Q-table loaded from {filename}")
        except FileNotFoundError:
            print(f"No existing Q-table found at {filename}. Starting fresh.")

    def can_afford_trade(self, price):
        current_date = datetime.now().date()
        if (current_date - self.start_date).days % 2 == 0:
            max_spend = 0.03 * self.settled_cashA#//////////////////////////////////////////////////////////////
        else:
            max_spend = 0.03 * self.settled_cashB
        return price <= max_spend


    # def release_settled_cash(self):
    #     now = datetime.now()
    #     still_pending = []
    #     for release_time, amount in self.pending_settlements:
    #         if now >= release_time:
    #             self.settled_cash += amount
    #         else:
    #             still_pending.append((release_time, amount))
    #     self.pending_settlements = still_pending
    def release_settled_cash(self):
        now = datetime.now()
        still_pending = []
        for release_time, amount, pool in self.pending_settlements:
            if now >= release_time:
                if pool == 'A':
                    self.settled_cashA += amount
                elif pool == 'B':
                    self.settled_cashB += amount
            else:
                still_pending.append((release_time, amount, pool))
        self.pending_settlements = still_pending
