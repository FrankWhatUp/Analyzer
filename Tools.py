from datetime import datetime, timedelta
from StockBinaryTree import StockBinaryTree
from Communication import StockTrader
import os


class SimplifiedTools:
    def __init__(self, api_key: str, api_secret: str):
        self.trader = StockTrader(api_key, api_secret)
        # self.stocks = [
        #     "AAPL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "GOOGL", "AMD", "NFLX", "PLTR",
        #     "F", "NOK", "SIRI", "SOFI", "SNAP", "BTG", "ET", "TTWO",
        #     "CYN", "CVNA", "TOST", "CB", "AXON", "CAVA", "BRK.B", "V", "JNJ", "PG", "TSM",
        #     "PM", "NRG", "GE", "CVS", "UBER", "DDOG", "TW", "INTU",
        #     "AVGO", "ORCL", "QCOM", "INTC", "COST", "TXN", "CSCO", "PEP", "UNH", "JPM", "HD", "NKE", "AMGN"
        # ]
        self.stocks = [
            "BMY",  # Bristol-Myers Squibb (Healthcare)
            "LLY",  # Eli Lilly (Healthcare)
            "ABBV",  # AbbVie (Healthcare)
            "MRK",  # Merck & Co. (Healthcare)
            "PFE",  # Pfizer (Pharma)
            "XOM",  # Exxon Mobil (Energy)
            "CVX",  # Chevron (Energy)
            "SLB",  # Schlumberger (Energy Services)
            "COP",  # ConocoPhillips (Energy)

            "CAT",  # Caterpillar (Industrials)
            "LMT",  # Lockheed Martin (Aerospace/Defense)
            "GEHC",  # GE Healthcare

            "T",  # AT&T (Telecom)
            "VZ",  # Verizon (Telecom)
            "TMUS",  # T-Mobile US (Telecom)


            "WMT",  # Walmart (Consumer)
            "DG",  # Dollar General (Consumer)
            "MCD",  # McDonald's (Fast food)
            "SBUX",  # Starbucks (Consumer)

            "KO",  # Coca-Cola (Consumer Staples)
            "MO",  # Altria (Tobacco)
            "GIS",  # General Mills (Food)
            "KHC",  # Kraft Heinz

            "BAC",  # Bank of America (Finance)
            "WFC",  # Wells Fargo
            "GS",  # Goldman Sachs
            "MS",  # Morgan Stanley
            "USB",  # U.S. Bancorp

            "BK",  # Bank of New York Mellon
            "SCHW",  # Charles Schwab
            "AFL",  # Aflac (Insurance)
            "TRV",  # Travelers (Insurance)

            "RTX",  # RTX Corp (Aerospace/Defense)
            "BA",  # Boeing
            "UPS",  # United Parcel Service
            "FDX",  # FedEx

            "ADP",  # ADP (HR software/services)
            "PAYX",  # Paychex (Payroll)
            "CL",  # Colgate-Palmolive
            "EL",  # Estée Lauder
            "DHR",  # Danaher
            "MMM",  # 3M
            "HCA",  # HCA Healthcare
            "ZBH"  # Zimmer Biomet (Medical Devices)
        ]
        self.stock_trees = {}

    @staticmethod
    def get_timeframe(choice: int):
        now = datetime.now() - timedelta(hours=24)  # Ensure latest data is at least 1 hour old

        timeframes = {
            1: (now - timedelta(hours=24), now, "hour"),
            2: (now - timedelta(days=7), now, "day"),
            3: (now - timedelta(days=7), now, "hour"),
            4: (now - timedelta(days=14), now, "hour"),
            5: (now - timedelta(days=30), now, "day"),
            6: (now - timedelta(weeks=52), now, "day")
        }

        return timeframes.get(choice, (None, None, None))

    def populate_stock_trees(self, start_time: str, end_time: str, timeframe: str):
        for stock in self.stocks:
            self.trader.tree = StockBinaryTree()  # Create a new tree for each stock
            self.trader.get_stock_info(stock, start_time, end_time, timeframe)  # Fetch stock data
            self.stock_trees[stock] = self.trader.tree  # Assign the tree to the dictionary

    def clear_stock_trees(self):
        for stock, tree in self.stock_trees.items():
            tree.clear()

    def traverse_stock_trees(self):
        for stock, tree in self.stock_trees.items():
            if tree:
                print(f"Traversing tree for {stock}:")
                tree.inorder_traversal()
            else:
                print(f"Stock tree for {stock} is empty or not populated.")

    def run_analysis(self, timeframe_choice: int):
        time_frame = self.get_timeframe(timeframe_choice)

        if time_frame[0] and time_frame[1]:
            start_time = time_frame[0].isoformat() + "Z"
            end_time = time_frame[1].isoformat() + "Z"
            timeframe = time_frame[2]

            self.clear_stock_trees()
            self.populate_stock_trees(start_time, end_time, timeframe)
            self.traverse_stock_trees()
            return self.stock_trees
        else:
            print("Invalid timeframe selection. Cannot proceed.")

    def get_latest_node(self, stock: str):
        tree = self.stock_trees.get(stock)
        if tree:
            return tree.get_latest_node()
        return None

    def get_news(self, symbol: str, start_time: datetime = None, end_time: datetime = None):
        """
        Wrapper to fetch news using trader with optional time filtering.

        :param symbol: Stock ticker symbol
        :param start_time: Start of the news time window (datetime)
        :param end_time: End of the news time window (datetime)
        :return: List of news headlines (strings)
        """
        news = self.trader.get_stock_news(symbol, start_time=start_time, end_time=end_time)
        return news

    def extract_symbols_and_headlines(self, news_dict):
        """
        Extracts a list of (symbols, headline) tuples from a dictionary with News objects.
        Handles symbols with market prefixes like 'TSX:CAE' → 'CAE'.

        :param news_dict: A dictionary with key 'news' whose value is a list of News objects
        :return: List of tuples: [(symbols_list, headline_str), ...]
        """
        result = []

        try:
            articles = news_dict["news"]
            for article in articles:
                raw_symbols = getattr(article, "symbols", [])
                headline = getattr(article, "headline", "")

                cleaned_symbols = []
                for sym in raw_symbols:
                    if isinstance(sym, str):
                        # If symbol includes market prefix like "TSX:CAE"
                        if ":" in sym:
                            sym = sym.split(":")[1].strip()
                        # Handle cases like comma-separated values (optional)
                        for s in sym.split(","):
                            cleaned = s.strip().upper()
                            if cleaned:
                                cleaned_symbols.append(cleaned)
                    elif isinstance(sym, list):
                        cleaned_symbols.extend(sym)  # fallback if already list of strings

                result.append((cleaned_symbols, headline))

        except Exception as e:
            print(f"[ERROR] Failed to extract headlines: {e}")

        return result

    def ensure_held_stocks_are_tracked(self, posHold_file: str, max_stocks: int = 30):
        """
        Ensures all currently 'holding' stocks from posHold.txt are kept in self.stocks,
        avoiding duplicates and malformed entries.
        """
        held_stocks = set()

        # Read the posHold.txt file and collect valid 'holding' stocks
        if os.path.exists(posHold_file):
            with open(posHold_file, "r") as f:
                for line in f:
                    parts = line.strip().split(":")
                    if len(parts) >= 2:
                        symbol = parts[0].strip().upper()
                        position = parts[1].strip().lower()
                        if position == "holding":
                            held_stocks.add(symbol)

        # Prioritize held stocks and avoid duplicates
        existing_stocks = list(dict.fromkeys(self.stocks))  # Deduplicate original stock list
        updated_list = list(held_stocks) + [s for s in existing_stocks if s not in held_stocks]
        print(updated_list)
        # Trim to max allowed
        self.stocks = updated_list[:max_stocks]



