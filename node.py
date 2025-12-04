class Node:
    """Representa um nó da rede P2P.

    Cada nó possui:
    - um identificador (string)
    - um conjunto de recursos
    - uma lista de vizinhos (outros nós)
    - um cache local com mapeamento: recurso -> id do nó que possui o recurso
    """

    def __init__(self, node_id, resources=None):
        self.id = str(node_id)
        self.resources = set(resources or [])
        self.neighbors = []
        self.cache = {}  # resource_id -> node_id

    def add_neighbor(self, other: "Node") -> None:
        """Adiciona um vizinho ao nó (grafo não direcionado é tratado na Network)."""
        if other.id == self.id:
            # não adiciona auto-loop, validação completa é feita na Network
            return
        if other not in self.neighbors:
            self.neighbors.append(other)

    def __repr__(self) -> str:
        return f"Node(id={self.id!r}, resources={sorted(self.resources)!r})"
