import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import networkx as nx
import matplotlib.pyplot as plt
from model_inference.graph_store import get_connection


def build_graph():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user, device FROM edges")
    edges = cursor.fetchall()

    G = nx.Graph()

    for user, device in edges:
        G.add_edge(user, device)

    conn.close()
    return G


def visualize():
    G = build_graph()

    plt.figure(figsize=(8, 6))
    nx.draw(G, with_labels=True, node_size=500, font_size=8)
    plt.title("Fraud Graph Visualization")
    plt.show()


if __name__ == "__main__":
    visualize()