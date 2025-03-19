from src.data.constants import *
from src.data.constants import POSSIBLE_BUILDINGS

FURNACE_DEPS = {
    24: [EMBASSY, RESEARCH],
    25: [EMBASSY, INFANTRY],
    26: [EMBASSY, MARKSMAN],
    27: [EMBASSY, LANCERS],
    28: [EMBASSY, RESEARCH],
    29: [EMBASSY, INFANTRY],
    30: [EMBASSY, MARKSMAN],
}


def depends_on(building: str, level: int):
    """
    All buildings require their previous level to be built.
    Non-Furnace buildings also require the Furnace to be at the desired level.
    The Furnace always depends on Embassy, as well as one other building that changes with each level.
    
    :param building:
    :param level:
    :return: a list of building-level tuples that the building at the given level depends on
    """
    if building != FURNACE:
        return [('Furnace', level), (building, level - 1)]
    else:
        return [(dep, level - 1) for dep in FURNACE_DEPS[level]]


def main():
    """
    If this library is run as a script, it will plot a dependency tree, partitioned vertically by level.
    """
    import matplotlib.pyplot as plt
    import networkx as nx
    
    # noinspection PyPep8Naming
    G = nx.DiGraph()
    nodes = [(building, level) for building in POSSIBLE_BUILDINGS for level in range(24, 31)]
    extra_nodes = []
    for node in nodes:
        b, l = node
        for dep in depends_on(b, l):
            G.add_edge(dep, node)
    labels = {}
    for node in G.nodes:
        b, l = node
        labels[node] = f"{b[0]}{l}"
    
    # we have to make the multi-partite layout ourselves, so we can put the same building at the same y-coordinate
    pos = {node: (POSSIBLE_BUILDINGS.index(node[0]), node[1]) for node in G.nodes}
    nx.draw(G, pos, with_labels=True, labels=labels)
    plt.show()

if __name__ == '__main__':
    main()
