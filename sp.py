def build(edges):
    graph = {}

    for edge in edges:
        a, b = edge[0], edge[1]
        if graph.get(a) is None:
            graph[a] = {}
        graph[a][b] = 1
        if graph.get(b) is None:
            graph[b] = {}
        graph[b][a] = 1
    return graph


def BFS_SP(graph, strt_adrs, dest_adrs):
    explored = []
    queue = [[strt_adrs]]
    if strt_adrs == dest_adrs:
        return None
    while queue:
        path = queue.pop(0)
        node = path[-1]
        if node not in explored:
            neighbours = get_neighbours(graph, node)
            for neighbour in neighbours:
                new_path = list(path)
                new_path.append(neighbour)
                queue.append(new_path)
                if neighbour == dest_adrs:
                    return new_path
            explored.append(node)
    return -1


def get_neighbours(graph, node):
    neighbs = graph[node]
    if neighbs is None:
        return []
    return neighbs.keys()

edges = [['a','b'],['a','c'],['b','d'],['c','b']]
graph = build(edges)
strt = input("start:")
end = input("end:")
ans = BFS_SP(graph,strt,end)
print(ans)
