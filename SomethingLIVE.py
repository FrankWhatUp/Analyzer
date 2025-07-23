from HistoricalDataExporter import HistoricalDataExporter
from QLearningAgent import QLearningAgent
from StockAnalyzer import StockMomentumAnalyzer
from Strategy import LiveTradingTrainer
from Tools import SimplifiedTools
from datetime import datetime, timedelta
import os
import time

api_key = "PKS0QSGZK3C6C41W7EOO"
api_secret = "zsQB6O1vNVByAhnGX7Ps7dehgwWbpucja48oJziB"
tools = SimplifiedTools(api_key, api_secret)
current_day = datetime.today().date()
agent = QLearningAgent(actions=["Buy", "Hold", "Sell"], learning_rate=0.3, discount_factor=0.8, exploration_rate=0.3, initial_equity=1000, start_date = current_day)
agent.load_q_table()


timeframe = "hour"
window_size_days = 11
poll_interval = 1800  # seconds = 5 minutes between checks

print("Starting live adaptive training...")

while True:
    # === Set live date range ===
    end_time = datetime.utcnow() - timedelta(hours=3)
    start_time = end_time - timedelta(days=window_size_days)

    start_iso = start_time.isoformat() + "Z"
    end_iso = end_time.isoformat() + "Z"

    agent.release_settled_cash()

    # === Get news and symbols ===
    try:
        raw_news = tools.get_news("Doesnt matter", start_iso, end_iso)
        results = tools.extract_symbols_and_headlines(raw_news[1])
    except Exception as e:
        print("[WARN] News API failed:", e)
        results = []

    stock_to_headlines = {}
    for entry in results:
        try:
            symbols = entry[0]
            headline = entry[1]
            for symbol in symbols:
                if symbol:
                    stock_to_headlines.setdefault(symbol, []).append(headline)
        except:
            continue

    # === Prioritize stocks ===
    mentioned = list(stock_to_headlines.keys())
    unmentioned = [s for s in tools.stocks if s not in mentioned]
    tools.stocks = mentioned + unmentioned
    tools.ensure_held_stocks_are_tracked("posHold.txt")

    # === Process each stock ===
    for stock in tools.stocks:
        trainer = LiveTradingTrainer(
            stock_list=[stock],
            analyzer=None,
            agent=agent,
            tools=tools,
            log_file="trade_log.txt"
        )

        # === Download recent data ===
        try:
            exporter_writer = HistoricalDataExporter(tools)
            exporter_writer.export_Data(start_iso, end_iso, timeframe)
        except Exception as e:
            print(f"[{stock}] Error fetching data: {e}")
            continue

        file_name = f"{stock}_hour_{start_time.date()}_to_{end_time.date()}.txt"
        folder_path = os.path.join(os.path.dirname(__file__), "HistoricalData")
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            print(f"[{stock}] Missing file: {file_name}")
            continue

        # === Run training pass ===
        stock_tree_dict = HistoricalDataExporter(tools).load_stock_tree_from_file(file_name, stock)
        analyzer = StockMomentumAnalyzer(stock_tree_dict)
        trainer.analyzer = analyzer
        headlines = stock_to_headlines.get(stock, [])
        trainer.run2(stock=stock, stock_trees=stock_tree_dict, news_text=headlines)

    agent.save_q_table()
    print("[INFO] Waiting for next live cycle...")
    time.sleep(poll_interval)
