from datetime import datetime
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, NewsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import StopLimitOrderRequest
from alpaca.trading.enums import OrderType
from alpaca.data import NewsClient

class StockTrader:
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

        # Initialize Alpaca clients in paper trading mode
        self.trading_client = TradingClient(api_key, secret_key, paper=True)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        self.news_client = NewsClient(api_key, secret_key)

    def get_account_info(self):
        account = self.trading_client.get_account()
        print(f"Account ID: {account.id}, Equity: {account.equity}, Cash: {account.cash}")
        if account.trading_blocked:
            print("Account is currently restricted from trading.")

    def check_asset_tradability(self, symbol: str):
        asset = self.trading_client.get_asset(symbol)
        if asset.tradable:
            print(f"{symbol} is tradable.")
        else:
            print(f"{symbol} is not tradable.")

    def get_stock_info(self, symbol: str, start_time: str, end_time: str, timeframe: str = "minute"):
        timeframe_mapping = {
            "minute": TimeFrame.Minute,
            "hour": TimeFrame.Hour,
            "day": TimeFrame.Day
        }

        if timeframe not in timeframe_mapping:
            print("Invalid timeframe. Choose from 'minute', 'hour', or 'day'.")
            return

        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except ValueError:
            print("Invalid datetime format. Please use ISO 8601 (e.g., 2023-01-01T00:00:00Z)")
            return

        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe_mapping[timeframe],
            start=start_dt,
            end=end_dt
        )

        try:
            bars = self.data_client.get_stock_bars(request_params)
            # Insert stock data into the tree
            for bar in bars[symbol]:
                self.tree.insert(
                    bar.open,
                    bar.close,
                    bar.high,
                    bar.low,
                    bar.volume,
                    bar.timestamp
                )
        except Exception as e:
            print("Error fetching stock data:", e)

    def order_stock(self, symbol: str, quantity: int):
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )
        try:
            order = self.trading_client.submit_order(market_order)
            print(f"Buy order placed for {quantity} shares of {symbol}. Order ID: {order.id}")
            return str(order.id)  # Return order ID as string
        except Exception as e:
            print("Error placing buy order:", e)

    def short_stock(self, symbol: str, quantity: int):
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        try:
            order = self.trading_client.submit_order(market_order)
            print(f"Short sell order placed for {quantity} shares of {symbol}. Order ID: {order.id}")
            return str(order.id)  # Ensure return is a string for consistency
        except Exception as e:
            print("Error placing short sell order:", e)

    def check_order_status(self, order_id: str):
        try:
            order = self.trading_client.get_order_by_id(order_id)
            if order.status == "filled":
                print(f"Order {order_id} is filled. Proceeding with the sell order.")
            else:
                print(f"Order {order_id} is not filled yet. Status: {order.status}")
        except Exception as e:
            print(f"Error checking order status: {e}")

    def order_with_stop_loss(self, symbol: str, quantity: int, side: str, stop_loss_percent: float):
        """
        Places a market order (buy or short-sell) and sets a stop-loss order. Also stores orders in the order history tree.

        :param symbol: Stock ticker symbol.
        :param quantity: Number of shares to buy or short-sell.
        :param side: "BUY" for long or "SELL" for short.
        :param stop_loss_percent: Stop-loss percentage from the entry price.
        """
        if side not in ["BUY", "SELL"]:
            print("Invalid order side. Use 'BUY' for long or 'SELL' for short.")
            return

        # Place Market Order
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY if side == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )

        try:
            order = self.trading_client.submit_order(market_order)
            print(f"{side} order placed for {quantity} shares of {symbol}. Order ID: {order.id}")

            # Store order in the order history tree
            self.order_history.insert(symbol, quantity, order.id)

            # Get the last traded price (entry price)
            latest_bar = self.data_client.get_stock_bars(
                StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Day,
                    limit=1
                )
            )
            entry_price = latest_bar[symbol][0].close if latest_bar[symbol] else None

            if entry_price is None:
                print(f"Failed to fetch entry price for {symbol}. Stop-loss not placed.")
                return

            # Calculate stop-loss price
            stop_loss_price = round(
                entry_price * (1 - stop_loss_percent / 100) if side == "BUY" else entry_price * (
                        1 + stop_loss_percent / 100),
                2
            )

            # Place Stop Order
            stop_order = StopLimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.SELL if side == "BUY" else OrderSide.BUY,  # Opposite to close position
                stop_price=stop_loss_price,
                limit_price=stop_loss_price,  # Needed for stop-limit orders
                order_type=OrderType.STOP_LIMIT,
                time_in_force=TimeInForce.GTC
            )

            stop_loss = self.trading_client.submit_order(stop_order)
            print(f"Stop-loss order placed at ${stop_loss_price} for {symbol}. Stop Order ID: {stop_loss.id}")

            # Store stop-loss order in the order history tree
            self.order_history.insert(symbol, quantity, stop_loss.id)

            return order.id, stop_loss.id  # Return order IDs for tracking

        except Exception as e:
            print("Error placing order:", e)



    def get_stock_news(self, symbol: str, limit: int = 5, start_time: datetime = None,
                       end_time: datetime = None) -> list:
        """
        Fetches news headlines for a stock symbol within an optional time range.
        """
        try:
            request_kwargs = {
                "symbol": symbol,
                "limit": limit
            }

            if start_time:
                request_kwargs["start"] = start_time
            if end_time:
                request_kwargs["end"] = end_time

            news_request = NewsRequest(**request_kwargs)

            news_items, _ = self.news_client.get_news(news_request)

            # If news_items is a list of strings (headlines), return it directly
            print(f"[NEWS] Retrieved {len(news_items)} headlines for {symbol} from {start_time} to {end_time}")
            return news_items

        except Exception as e:
            print(f"[ERROR] Failed to fetch news for {symbol}: {e}")
            return []


