class StockNode:
    def __init__(self, open_price: float, close_price: float, high_price: float, low_price: float, volume: int, timestamp: float):
        self.open_price = open_price
        self.close_price = close_price
        self.high_price = high_price
        self.low_price = low_price
        self.volume = volume
        self.timestamp = timestamp

        self.left = None  # Left child node
        self.right = None  # Right child node

    def __str__(self):
        return (f"StockNode(Open: {self.open_price}, Close: {self.close_price}, "
                f"High: {self.high_price}, Low: {self.low_price}, Volume: {self.volume}, "
                f"Timestamp: {self.timestamp})")