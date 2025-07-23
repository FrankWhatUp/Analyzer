from datetime import datetime, timedelta
import os
from StockBinaryTree import StockBinaryTree

class HistoricalDataExporter:
    def __init__(self, tools, output_dir="HistoricalData"):
        self.tools = tools
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export_Data(self, startTime: str, endTime: str, timeframe: str):
        # Clear and repopulate the trees
        self.tools.clear_stock_trees()
        self.tools.populate_stock_trees(startTime, endTime, timeframe)

        # Absolute export path
        export_path = r"C:\Users\franc\Desktop\Engineering_Applications\Industrial\PythonProject69\HistoricalData"

        # Check that the directory exists
        if not os.path.isdir(export_path):
            print(f"[ERROR] Directory does not exist: {export_path}")
            return

        # Export each stock's binary tree to a file
        for symbol, tree in self.tools.stock_trees.items():
            output_file = f"{symbol}_{timeframe}_{startTime[:10]}_to_{endTime[:10]}.txt"
            output_path = os.path.join(export_path, output_file)

            try:
                with open(output_path, "w") as f:  # Creates file if it doesn't exist
                    self._write_tree_to_file(tree, f)
            except Exception as e:
                print(f"[ERROR] Writing file for {symbol} failed: {e}")

    def _write_tree_to_file(self, tree, file_obj):
        def _inorder(node):
            if node is None:
                return
            _inorder(node.left)
            dt = node.timestamp  # Already a datetime object
            file_obj.write(
                f"{dt.isoformat()}, Open: {node.open_price}, High: {node.high_price}, "
                f"Low: {node.low_price}, Close: {node.close_price}, Volume: {node.volume}\n"
            )
            _inorder(node.right)

        _inorder(tree.root)

    def load_stock_tree_from_file(self, file_name, stock_symbol):
        """
        Reads historical stock data from a file in the 'HistoricalData' folder and constructs a StockBinaryTree.

        Format per line:
        2025-06-16T15:00:00+00:00, Open: 214.6275, High: 216.55, Low: 214.58, Close: 215.4125, Volume: 4633664.0
        """
        tree = StockBinaryTree()

        # Join base path with folder and file name
        folder_path = os.path.join(os.path.dirname(__file__), "HistoricalData")
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, "r") as f:
            for line in f:
                try:
                    parts = line.strip().split(", ")
                    timestamp = datetime.fromisoformat(parts[0])

                    data = {}
                    for part in parts[1:]:
                        key, val = part.split(": ")
                        data[key.lower()] = float(val)

                    tree.insert(
                        open_price=data["open"],
                        high_price=data["high"],
                        low_price=data["low"],
                        close_price=data["close"],
                        volume=data["volume"],
                        timestamp=timestamp
                    )

                except Exception as e:
                    print(f"Error parsing line: {line.strip()} — {e}")

        return {stock_symbol: tree}
