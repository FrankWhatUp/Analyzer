import time
from datetime import datetime, timedelta
import os

class LiveTradingTrainer:
    def __init__(self, stock_list, analyzer, agent, tools, log_file='trade_log.txt',price_file='pricetracking.txt', posHold ='posHold.txt'):
        self.stock_list = stock_list
        self.analyzer = analyzer
        self.agent = agent
        self.log_file = log_file
        self.tools = tools
        self.prev_state_action = {}  # {stock: (state_key, action, price)}
        self.price_file = price_file
        self.position_file = posHold
        self.prev_action_file = "prevAction.txt"
        self.statekey_file = "statekeys.txt"

    def log_decision(self, stock, action, state_key, current_price=None, reward=None):
        with open(self.log_file, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            reward_str = f", Reward = {reward:.4f}" if reward is not None else ""
            price_str = f", Price = {current_price:.2f}" if current_price is not None else ", Price = N/A"
            equity_str = f", Equity = {self.agent.equity:.2f}"
            f.write(f"[{timestamp}] {stock}: Action = {action}, State = {state_key}{price_str}{reward_str}{equity_str}\n")

    # def can_execute_buy(self, current_price):
    #     max_spend = 0.3 * self.agent.equity
    #     max_affordable = int(max_spend // current_price)
    #     return max_affordable > 0, max_affordable

    def execute_buy(self, stock, current_price, shares):
        total_cost = shares * current_price
        self.agent.settled_cash -= total_cost
        self.agent.equity -= total_cost
        self.save_position(stock,"holding",shares)

    def execute_buy(self, stock, current_price, shares):
        total_cost = shares * current_price
        day_index = (datetime.now().date() - self.agent.start_date).days

        if day_index % 2 == 0:
            self.agent.settled_cashA -= total_cost
        else:
            self.agent.settled_cashB -= total_cost

        self.agent.equity -= total_cost
        self.save_position(stock, "holding", shares, current_price)

    # def execute_sell(self, stock, current_price):
    #     pos, shares = self.get_position(stock)
    #     if pos == "holding":
    #         proceeds = shares * current_price
    #         release_time = datetime.now() + timedelta(days=2)  # 2-day settlement
    #         self.agent.pending_settlements.append((release_time, proceeds))
    #         self.agent.equity += proceeds
    #         self.save_position(stock,"flat",0)
    
    def execute_sell(self, stock, current_price):
        pos, shares,_ = self.get_position(stock)
        if pos == "holding":
            proceeds = shares * current_price
            release_time = datetime.now() + timedelta(days=2)

            # Determine the correct pool
            day_index = (datetime.now().date() - self.agent.start_date).days
            pool = 'A' if day_index % 2 == 0 else 'B'

            self.agent.pending_settlements.append((release_time, proceeds, pool))
            self.agent.equity += proceeds
            self.save_position(stock, "flat", 0, 0)

    # def save_price(self,stock: str, price: float):
    #     """
    #     Saves or updates the price of the given stock in the pricetracking.txt file.
    #     """
    #     PRICE_FILE = self.price_file
    #     stock = stock.upper()
    #     updated = False
    #     lines = []
    #
    #     # Read existing lines
    #     if os.path.exists(PRICE_FILE):
    #         with open(PRICE_FILE, "r") as f:
    #             for line in f:
    #                 symbol, _, old_price = line.strip().partition(":")
    #                 if symbol.strip().upper() == stock:
    #                     lines.append(f"{stock} : {price}\n")
    #                     updated = True
    #                 else:
    #                     lines.append(line)
    #
    #     # Add new entry if not found
    #     if not updated:
    #         lines.append(f"{stock} : {price}\n")
    #
    #     # Write back to file
    #     with open(PRICE_FILE, "w") as f:
    #         f.writelines(lines)

    def get_price(self,stock: str):
        """
        Returns the most recently saved price of the given stock.
        Returns None if the stock is not found.
        """
        PRICE_FILE = self.price_file
        stock = stock.upper()

        if not os.path.exists(PRICE_FILE):
            return None

        with open(PRICE_FILE, "r") as f:
            for line in f:
                symbol, _, value = line.strip().partition(":")
                if symbol.strip().upper() == stock:
                    try:
                        return float(value.strip())
                    except ValueError:
                        return None
        return None

    def save_position(self, stock: str, position: str, shares: int = 0, pricePerShare: float = 0):
        """
        Saves or updates the position ('holding' or 'flat') and number of shares of the given stock in posHold.txt.
        Format: SYMBOL : POSITION : SHARES
        """
        POSITION_FILE = self.position_file
        stock = stock.upper()
        position = position.lower()
        updated = False
        lines = []

        # Read existing entries
        if os.path.exists(POSITION_FILE):
            with open(POSITION_FILE, "r") as f:
                for line in f:
                    symbol, _, rest = line.strip().partition(":")
                    if symbol.strip().upper() == stock:
                        lines.append(f"{stock} : {position} : {shares} : {pricePerShare}\n")
                        updated = True
                    else:
                        lines.append(line)

        # Add new entry if not found
        if not updated:
            lines.append(f"{stock} : {position} : {shares} : {pricePerShare}\n")

        # Write updated content
        with open(POSITION_FILE, "w") as f:
            f.writelines(lines)

    def get_position(self, stock: str):
        """
        Returns the most recently saved position, number of shares, and bought price of the given stock.
        Defaults to ('flat', 0, 0.0) if not found or invalid.
        Format expected in posHold.txt: SYMBOL : POSITION : SHARES : PRICE
        """
        POSITION_FILE = self.position_file
        stock = stock.upper()

        if not os.path.exists(POSITION_FILE):
            return "flat", 0, 0.0

        with open(POSITION_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) >= 3:
                    symbol = parts[0].strip().upper()
                    position = parts[1].strip().lower()

                    try:
                        shares = int(parts[2].strip())
                    except ValueError:
                        shares = 0

                    # Default price if not present
                    boughtPrice = 0.0
                    if len(parts) >= 4:
                        try:
                            boughtPrice = float(parts[3].strip())
                        except ValueError:
                            boughtPrice = 0.0

                    if symbol == stock and position in ["holding", "flat"]:
                        return position, shares, boughtPrice

        return "flat", 0, 0.0

    def get_prev_action(self, stock: str):
        """
        Returns the most recently saved action of the given stock.
        Defaults to 'Hold' if not found or invalid.
        """
        ACTION_FILE = self.prev_action_file
        stock = stock.upper()

        if not os.path.exists(ACTION_FILE):
            print("No action file ==========================")
            return "Hold"

        with open(ACTION_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    symbol = parts[0].strip().upper()
                    action = parts[1].strip().capitalize()  # Capitalize ensures match
                    if symbol == stock and action in ["Buy", "Sell", "Hold"]:
                        return action
        return "Hold"

    def save_prev_action(self, stock: str, action: str):
        """
        Saves or updates the previous action ('buy', 'sell', 'hold') of the given stock in prevAction.txt.
        """
        ACTION_FILE = self.prev_action_file  # e.g., set in __init__ as self.prev_action_file = "prevAction.txt"
        stock = stock.upper()
        updated = False
        lines = []

        if os.path.exists(ACTION_FILE):
            with open(ACTION_FILE, "r") as f:
                for line in f:
                    symbol, _, old_action = line.strip().partition(":")
                    if symbol.strip().upper() == stock:
                        lines.append(f"{stock} : {action}\n")
                        updated = True
                    else:
                        lines.append(line)

        if not updated:
            lines.append(f"{stock} : {action}\n")

        with open(ACTION_FILE, "w") as f:
            f.writelines(lines)

    def save_state_key(self, stock: str, state_key: tuple):
        """
        Saves or updates the discrete state_key tuple of the given stock in statekeys.txt.
        """
        STATEKEY_FILE = self.statekey_file  # e.g., "statekeys.txt"
        stock = stock.upper()
        updated = False
        lines = []

        key_str = ",".join(map(str, state_key))

        # Read existing entries
        if os.path.exists(STATEKEY_FILE):
            with open(STATEKEY_FILE, "r") as f:
                for line in f:
                    symbol, _, old_key = line.strip().partition(":")
                    if symbol.strip().upper() == stock:
                        lines.append(f"{stock} : {key_str}\n")
                        updated = True
                    else:
                        lines.append(line)

        # Add new entry if not found
        if not updated:
            lines.append(f"{stock} : {key_str}\n")

        # Write updated content
        with open(STATEKEY_FILE, "w") as f:
            f.writelines(lines)

    def get_stateSaved_key(self, stock: str):
        """
        Retrieves the most recently saved state_key tuple of the given stock from statekeys.txt.
        Returns None if not found or invalid.
        """
        STATEKEY_FILE = self.statekey_file
        stock = stock.upper()

        if not os.path.exists(STATEKEY_FILE):
            return None

        with open(STATEKEY_FILE, "r") as f:
            for line in f:
                symbol, _, value = line.strip().partition(":")
                if symbol.strip().upper() == stock:
                    key_str = value.strip()
                    try:
                        return tuple(int(x) for x in key_str.split(","))
                    except ValueError:
                        return None
        return

    # def compute_reward(self, stock: str, prev_action: str, current_price: float):
    #     """
    #     Calculates reward based on action context, price movement, and opportunity cost.
    #     Parameters:
    #         stock         - Stock symbol (str)
    #         prev_action   - Agent's previous action (str): "Buy", "Sell", or "Hold"
    #         current_price - Latest market price (float)
    #     Returns:
    #         reward (float)
    #     """
    #     prev_price = self.get_price(stock)
    #     prev_position, _, boughtPrice = self.get_position(stock)
    #
    #     if prev_price is None or current_price is None or boughtPrice is None:
    #         return 0.0  # Not enough data
    #
    #     # Price delta (normalized)
    #     price_change = (current_price - prev_price) / prev_price
    #
    #     # === Reward Logic ===
    #     reward = 0.0
    #
    #     if prev_action == "Buy":
    #         reward = 0.2  # Encourage action
    #         # Don't yet penalize incorrect buys — let time reveal outcome
    #
    #     elif prev_action == "Sell":
    #         if price_change < 0:
    #             reward = abs(price_change) * 1.0 + 0.3  # Sold before loss → bonus
    #         else:
    #             reward = -price_change * 0.5  # Penalize bad timing
    #
    #     elif prev_action == "Hold":
    #         if prev_position == "holding":
    #             reward = price_change * 0.3  # Reward/punish slow gains/losses
    #         else:
    #             # If flat and price moved a lot, punish missing the move
    #             if abs(price_change) > 0.02:
    #                 reward = -0.2  # Missed opportunity penalty
    #             else:
    #                 reward = -0.01  # Slight decay to discourage endless inaction
    #
    #     if price_change == 0:
    #         reward = 0.0
    #     # Clip to avoid extreme updates
    #     reward = max(min(reward, 1.0), -1.0)
    #     return reward

    def compute_reward(self, stock: str, prev_action: str, current_price: float):
        """
        Calculates reward based on action context, price movement, and opportunity cost.
        Parameters:
            stock         - Stock symbol (str)
            prev_action   - Agent's previous action (str): "Buy", "Sell", or "Hold"
            current_price - Latest market price (float)
        Returns:
            reward (float)
        """
        prev_position, _, boughtPrice = self.get_position(stock)

        if current_price is None or boughtPrice is None or boughtPrice <= 0.0:
            return 0.0  # Not enough or invalid data

        # Price delta (normalized return since buy)
        price_change = (current_price - boughtPrice) / boughtPrice

        # === Reward Logic ===
        reward = 0.0

        if prev_action == "Buy":
            reward = 0.02  # Encourage action

        elif prev_action == "Sell":
            if price_change < 0:
                reward = abs(price_change) * 1.0 + 0.3  # Sold before loss → bonus
            else:
                reward = -price_change * 0.5  # Penalize bad timing

        elif prev_action == "Hold":
            if prev_position == "holding":
                reward = price_change * 0.3  # Reward/punish slow gains/losses
            else:
                if abs(price_change) > 0.02:
                    reward = -0.2  # Missed opportunity penalty
                else:
                    reward = -0.01  # Slight decay to discourage endless inaction

        if price_change == 0:
            reward = 0.0

        # Clip reward to range [-1.0, 1.0]
        reward = max(min(reward, 1.0), -1.0)
        return reward

    def run2(self, stock, stock_trees, news_text):
        """
        Processes a single stock tree once and exits.
        Expects stock_trees to be a dictionary with one stock: { 'AAPL': StockBinaryTree() }
        """
        # print("Running single-pass training using provided stock tree...")
        decision_count = 0

        if not stock_trees or stock not in stock_trees:
            print(f"No stock tree provided for {stock}.")
            return
        print("Analising: ",stock)

        self.analyzer.stock_data = stock_trees
        self.agent.release_settled_cash()

        latest_node = stock_trees[stock].get_latest_node()
        current_price = latest_node.close_price if latest_node else None
        pos,_,_ = self.get_position(stock)

        day_index = (datetime.now().date() - self.agent.start_date).days

        if day_index % 2 == 0:
            if current_price is not None:
                if self.agent.settled_cashA < current_price and pos == 'flat':
                    return
        else:
            if current_price is not None:
                if self.agent.settled_cashB < current_price and pos == 'flat':
                    return

        reward = 0
        current_position = pos
        signal_vector = self.analyzer.extract_signal_vector(stock)
        state_key = self.agent.get_state_key(
            signal_vector,
            current_position,
            news_text=news_text,
            stock_symbol=stock
        )
        if current_position is None:
            current_position = "flat"

        if current_price is None:
            print(f"[{stock}] No latest price found. Skipping.")
            return
        action = self.agent.choose_action(state_key, stock, current_price, current_position)

        # === Q-Learning Update Based on Previous Action ===
        prev_state = self.get_stateSaved_key(stock)
        print("Stoc,Action,Prev_State",stock, action, prev_state)
        prev_action = self.get_prev_action(stock)
        prev_position,_,prev_price = self.get_position(stock)

        if prev_state is not None and prev_action is not None and prev_price is not None and prev_position is not None:
            reward = self.compute_reward(stock, prev_action, current_price)
            self.agent.update(prev_state, prev_action, reward, state_key)
            priceChange = current_price - prev_price

            if priceChange == 0.0:
                action = "Hold"

        # === Execute Trade ===
        if action == "Buy":
            # can_buy, max_shares = self.can_execute_buy(current_price)
            # if not can_buy:
            #     action = "Hold"
            # else:
            max_shares = 1
            self.execute_buy(stock, current_price, max_shares)

        elif action == "Sell":
            if current_position == "holding":
                self.execute_sell(stock, current_price)
            else:
                action = "Hold"

        # Explicitly handle "Hold" action
        if action == "Hold":
            if current_position != "holding":
                self.save_position(stock, "flat", 0)

        # === Store state for next step ===
        self.save_state_key(stock,state_key)
        self.save_prev_action(stock,action)

        print(f"[Preview] {stock}: Action = {action}, State = {state_key}, Price = {current_price}, Reward = {reward}")
        # === Log decision ===
        self.log_decision(stock, action, state_key, current_price, reward)

