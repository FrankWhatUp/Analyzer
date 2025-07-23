from StockNode import StockNode

class StockBinaryTree:
    def __init__(self):
        self.root = None

    def insert(self, open_price: float, close_price: float, high_price: float, low_price: float, volume: int, timestamp: float):
        """
        Inserts a new StockNode into the binary tree.
        The tree is ordered based on the timestamp.
        """
        new_node = StockNode(open_price, close_price, high_price, low_price, volume, timestamp)
        if not self.root:
            self.root = new_node
        else:
            self._insert_recursively(self.root, new_node)

    def _insert_recursively(self, current: StockNode, new_node: StockNode):
        """
        Recursively inserts a StockNode in the correct position based on the timestamp.
        """
        if new_node.timestamp < current.timestamp:
            if current.left is None:
                current.left = new_node
            else:
                self._insert_recursively(current.left, new_node)
        else:
            if current.right is None:
                current.right = new_node
            else:
                self._insert_recursively(current.right, new_node)

    def inorder_traversal(self):
        """
        Performs an in-order traversal of the tree and prints each node.
        """
        if self.root is None:
            print("The tree is empty.")
        else:
            print("In-order Traversal:")
            self._inorder_traversal(self.root)

    def _inorder_traversal(self, node: StockNode):
        """
        Recursively performs an in-order traversal and prints nodes.
        """
        if node:
            self._inorder_traversal(node.left)  # Traverse left subtree
            print(node)  # Print current node
            self._inorder_traversal(node.right)  # Traverse right subtree

    def is_empty(self):
        """
        Returns True if the tree is empty, False otherwise.
        """
        return self.root is None

    def clear(self):
        """
        Clears the binary tree by setting the root to None.
        """
        self.root = None

    def get_latest_node(self):
        """
        Returns the StockNode with the latest (rightmost) timestamp in the tree.
        """
        current = self.root
        if not current:
            return None
        while current.right:
            current = current.right
        return current