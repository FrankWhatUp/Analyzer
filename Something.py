from HistoricalDataExporter import HistoricalDataExporter
from QLearningAgent import QLearningAgent
from StockAnalyzer import StockMomentumAnalyzer
from Strategy import LiveTradingTrainer
from Tools import SimplifiedTools
from datetime import datetime, timedelta
import os
import time

# === API & Agent Setup ===
api_key = "PKS0QSGZK3C6C41W7EOO"
api_secret = "zsQB6O1vNVByAhnGX7Ps7dehgwWbpucja48oJziB"
tools = SimplifiedTools(api_key, api_secret)
current_day = datetime.now().date()
agent = QLearningAgent(actions=["Buy", "Hold", "Sell"], learning_rate=0.6, discount_factor=0.4, exploration_rate=0.8, initial_equity=100000000, start_date = current_day)
agent.load_q_table()

# === CONFIG ===
timeframe = "hour"
window_size_hours = 10 * 24  # 7 days of hourly data
training_hours = 24 * 24    # approx 2 months (60 days)
start_reference = datetime.now() - timedelta(hours=training_hours + window_size_hours)

for i in range(training_hours):
    start_time = start_reference + timedelta(hours=i)
    end_time = start_time + timedelta(hours=window_size_hours)

    start_iso = start_time.isoformat() + "Z"
    end_iso = end_time.isoformat() + "Z"

    #///////// If trading is not going well: Retrain but keep track of price when bought

    # === Get News and Parse ===
    raw_news = tools.get_news("Doesnt matter", start_iso, end_iso)
    results = tools.extract_symbols_and_headlines(raw_news[1])
    stock_to_headlines = {}

    for entry in results:
        try:
            symbols = entry[0]
            headline = entry[1]
            for symbol in symbols:
                if symbol:
                    stock_to_headlines.setdefault(symbol, []).append(headline)
        except (IndexError, TypeError):
            continue

    # === Prioritize Stocks ===
    mentioned = list(stock_to_headlines.keys())
    unmentioned = [s for s in tools.stocks if s not in mentioned]
    prioritized_stocks = mentioned + unmentioned
    tools.stocks = prioritized_stocks
    tools.ensure_held_stocks_are_tracked("posHold.txt")

    # === Train on each stock ===
    for stock in tools.stocks:
        trainer = LiveTradingTrainer(
            stock_list=[stock],
            analyzer=None,
            agent=agent,
            tools=tools,
            log_file="trade_log.txt"
        )

        file_name = f"{stock}_hour_{start_time.date()}_to_{end_time.date()}.txt"

        exporter_writer = HistoricalDataExporter(tools)
        exporter_writer.export_Data(start_iso, end_iso, timeframe)

        folder_path = os.path.join(os.path.dirname(__file__), "HistoricalData")
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            print(f"[Hour {i + 1}] Skipping (missing file): {file_name}")
            continue

        exporter_reader = HistoricalDataExporter(tools)
        stock_tree_dict = exporter_reader.load_stock_tree_from_file(file_name, stock)
        analyzer = StockMomentumAnalyzer(stock_tree_dict)
        trainer.analyzer = analyzer

        news_text = stock_to_headlines.get(stock, [])
        trainer.run2(stock=stock, stock_trees=stock_tree_dict, news_text=news_text)

    agent.save_q_table()
    print(f"[{i + 1}/{training_hours}] Completed: {start_time} to {end_time}")
    time.sleep(100)
