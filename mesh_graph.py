import networkx as nx
import matplotlib.pyplot as plt

if __name__ == '__main__':
    print(f"running graph...")
    G = nx.Graph()
    G.add_nodes_from([(4, {"color": "red"}), (5, {"color": "green"})])

    subax1 = plt.subplot(121)
    nx.draw(G, with_labels=True, font_weight='bold')
    subax2 = plt.subplot(122)
    nx.draw_shell(G, nlist=[range(5, 10), range(5)], with_labels=True, font_weight='bold')

    plt.show()