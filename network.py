from node import Node


class Network:
    """Representa a rede P2P não estruturada."""

    def __init__(self):
        self.nodes = {}      # id -> Node
        self._edges = set()  # conjunto de arestas (min(id1, id2), max(id1, id2))

    def add_node(self, node_id, resources):
        node_id = str(node_id)
        if node_id in self.nodes:
            raise ValueError(f"Já existe nó com id {node_id}")
        self.nodes[node_id] = Node(node_id, resources)

    def add_edge(self, n1, n2):
        n1 = str(n1)
        n2 = str(n2)
        if n1 == n2:
            raise ValueError(f"Aresta inválida: nó {n1} não pode se ligar a si mesmo")
        if n1 not in self.nodes or n2 not in self.nodes:
            raise ValueError(f"Tentativa de criar aresta entre nós inexistentes: {n1}, {n2}")

        a = min(n1, n2)
        b = max(n1, n2)
        if (a, b) in self._edges:
            return  # evita duplicadas

        self._edges.add((a, b))
        self.nodes[n1].add_neighbor(self.nodes[n2])
        self.nodes[n2].add_neighbor(self.nodes[n1])

    # ----------------- Validações exigidas pelo enunciado ----------------- #
    def validate(self, num_nodes, min_neighbors, max_neighbors):
        """Valida a rede conforme os requisitos do trabalho.

        1. A rede não pode estar particionada (grafo conexo).
        2. Cada nó deve ter número de vizinhos entre min_neighbors e max_neighbors.
        3. Não pode haver nós sem recursos.
        4. Não pode haver arestas de um nó para ele mesmo (checado em add_edge).
        """
        self._validate_node_count(num_nodes)
        self._validate_no_empty_resources()
        self._validate_neighbors_degree(min_neighbors, max_neighbors)
        self._validate_connectivity()

    def _validate_node_count(self, num_nodes):
        if len(self.nodes) != num_nodes:
            raise ValueError(
                f"Número de nós na rede ({len(self.nodes)}) não bate com num_nodes={num_nodes}"
            )

    def _validate_no_empty_resources(self):
        for node in self.nodes.values():
            if not node.resources:
                raise ValueError(
                    f"Nó {node.id} não possui recursos (violação do requisito 3)."
                )

    def _validate_neighbors_degree(self, min_neighbors, max_neighbors):
        for node in self.nodes.values():
            degree = len(node.neighbors)
            if degree < min_neighbors or degree > max_neighbors:
                raise ValueError(
                    f"Nó {node.id} possui {degree} vizinhos, fora do intervalo "
                    f"[{min_neighbors}, {max_neighbors}] (violação do requisito 2)."
                )

    def _validate_connectivity(self):
        if not self.nodes:
            raise ValueError("Rede vazia não é permitida.")

        # BFS a partir de um nó arbitrário
        start_id = next(iter(self.nodes))
        visited = set()
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            node = self.nodes[current]
            for neigh in node.neighbors:
                if neigh.id not in visited:
                    queue.append(neigh.id)

        if len(visited) != len(self.nodes):
            raise ValueError(
                f"A rede está particionada: apenas {len(visited)} de {len(self.nodes)} nós são alcançáveis."
            )
