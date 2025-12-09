import random
from typing import Set, Tuple, List, Optional, Dict, Any

from network import Network
from node import Node


class SearchResult:
    """Contém estatísticas e caminhos de uma operação de busca."""

    def __init__(
        self,
        found: bool,
        start_node: str,
        resource_id: str,
        found_nodes: List[str],
        visited_nodes: Set[str],
        messages: int,
        paths: List[List[str]],
        algo: str,
    ):
        self.found = found
        self.start_node = start_node
        self.resource_id = resource_id
        self.found_nodes = found_nodes
        self.visited_nodes = visited_nodes
        self.messages = messages
        self.paths = paths
        self.algo = algo

    @property
    def num_visited_nodes(self) -> int:
        return len(self.visited_nodes)

    def __repr__(self) -> str:
        return (
            f"SearchResult(found={self.found}, found_nodes={self.found_nodes}, "
            f"messages={self.messages}, num_visited={self.num_visited_nodes}, "
            f"num_paths={len(self.paths)}, algo={self.algo!r})"
        )


# --------------------------------------------------------------------------- #
#  Algoritmos básicos                                                         #
# --------------------------------------------------------------------------- #

def flooding(network: Network, start_id: str, resource_id: str, ttl: int) -> SearchResult:
    """Busca por inundação (flooding) explorando todos os caminhos até o TTL."""
    start_id = str(start_id)
    resource_id = str(resource_id)

    if start_id not in network.nodes:
        raise ValueError(f"Nó inicial {start_id} não existe na rede.")

    visited: Set[str] = set()
    queue: List[Tuple[str, int, List[str]]] = [(start_id, ttl, [start_id])]
    messages = 0
    found_nodes: List[str] = []
    all_paths: List[List[str]] = []

    while queue:
        current_id, t, path = queue.pop(0)
        if t < 0:
            continue

        # Registra o caminho completo percorrido até este nó
        all_paths.append(path.copy())
        visited.add(current_id)
        node = network.nodes[current_id]

        # Verifica se o recurso está neste nó
        if resource_id in node.resources and current_id not in found_nodes:
            found_nodes.append(current_id)

        # Continua explorando mesmo após encontrar o recurso
        if t > 0:
            for neigh in node.neighbors:
                if neigh.id not in path:  # Evita ciclos no mesmo caminho
                    new_path = path + [neigh.id]
                    queue.append((neigh.id, t - 1, new_path))
                    messages += 1

    return SearchResult(
        found=len(found_nodes) > 0,
        start_node=start_id,
        resource_id=resource_id,
        found_nodes=found_nodes,
        visited_nodes=visited,
        messages=messages,
        paths=all_paths,
        algo="flooding",
    )


def random_walk(network: Network, start_id: str, resource_id: str, ttl: int) -> SearchResult:
    """Busca por passeio aleatório explorando múltiplos caminhos."""
    start_id = str(start_id)
    resource_id = str(resource_id)

    if start_id not in network.nodes:
        raise ValueError(f"Nó inicial {start_id} não existe na rede.")

    start_node = network.nodes[start_id]
    visited_global: Set[str] = set([start_id])
    found_nodes: List[str] = []
    all_paths: List[List[str]] = []
    total_messages = 0

    # Gera múltiplos caminhos aleatórios até o limite de TTL
    for _ in range(len(start_node.neighbors)):
        if ttl <= 0:
            break
            
        current_node = start_node
        visited_path: Set[str] = set([start_id])
        path: List[str] = [start_id]
        messages = 0
        current_ttl = ttl

        while current_ttl > 0 and current_node.neighbors:
            # Verifica recurso no nó atual
            if resource_id in current_node.resources and current_node.id not in found_nodes:
                found_nodes.append(current_node.id)

            # Escolhe próximo vizinho aleatório não visitado neste caminho
            unvisited = [n for n in current_node.neighbors if n.id not in visited_path]
            if not unvisited:
                break
                
            next_node = random.choice(unvisited)
            path.append(next_node.id)
            visited_path.add(next_node.id)
            visited_global.add(next_node.id)
            messages += 1
            current_ttl -= 1
            current_node = next_node

        # Verificação final no último nó
        if resource_id in current_node.resources and current_node.id not in found_nodes:
            found_nodes.append(current_node.id)
            
        all_paths.append(path)
        total_messages += messages

    return SearchResult(
        found=len(found_nodes) > 0,
        start_node=start_id,
        resource_id=resource_id,
        found_nodes=found_nodes,
        visited_nodes=visited_global,
        messages=total_messages,
        paths=all_paths,
        algo="random_walk",
    )


# --------------------------------------------------------------------------- #
#  Versões informadas (com cache local em cada nó)                            #
# --------------------------------------------------------------------------- #

def _update_cache_along_path(network: Network, path: List[str], resource_id: str, owner_id: str):
    """Atualiza o cache de todos os nós ao longo do caminho."""
    for node_id in path:
        node = network.nodes[node_id]
        node.cache[resource_id] = owner_id


def informed_flooding(network: Network, start_id: str, resource_id: str, ttl: int) -> SearchResult:
    """Versão informada da busca por inundação explorando todos os caminhos."""
    start_id = str(start_id)
    resource_id = str(resource_id)

    if start_id not in network.nodes:
        raise ValueError(f"Nó inicial {start_id} não existe na rede.")

    start_node = network.nodes[start_id]
    visited: Set[str] = set()
    queue: List[Tuple[str, int, List[str]]] = [(start_id, ttl, [start_id])]
    messages = 0
    found_nodes: List[str] = []
    all_paths: List[List[str]] = []
    found_via_cache: Dict[str, str] = {}  # resource_id -> owner_id

    while queue:
        current_id, t, path = queue.pop(0)
        if t < 0:
            continue

        all_paths.append(path.copy())
        visited.add(current_id)
        node = network.nodes[current_id]

        # Verifica cache local primeiro
        if resource_id in node.cache:
            owner_id = node.cache[resource_id]
            if owner_id not in found_nodes and owner_id in network.nodes:
                found_nodes.append(owner_id)
                found_via_cache[resource_id] = owner_id
                # Atualiza cache para todos os nós no caminho até aqui
                _update_cache_along_path(network, path, resource_id, owner_id)

        # Verifica recursos locais
        if resource_id in node.resources and current_id not in found_nodes:
            found_nodes.append(current_id)
            _update_cache_along_path(network, path, resource_id, current_id)

        # Continua explorando mesmo após encontrar
        if t > 0:
            for neigh in node.neighbors:
                if neigh.id not in path:  # Evita ciclos no mesmo caminho
                    new_path = path + [neigh.id]
                    queue.append((neigh.id, t - 1, new_path))
                    messages += 1

    # Atualiza cache para todos os caminhos que levaram a recursos encontrados
    for owner_id in found_nodes:
        for path in all_paths:
            if owner_id in path:
                _update_cache_along_path(network, path, resource_id, owner_id)

    return SearchResult(
        found=len(found_nodes) > 0,
        start_node=start_id,
        resource_id=resource_id,
        found_nodes=found_nodes,
        visited_nodes=visited,
        messages=messages,
        paths=all_paths,
        algo="informed_flooding",
    )


def informed_random_walk(network: Network, start_id: str, resource_id: str, ttl: int) -> SearchResult:
    """Versão informada do passeio aleatório explorando múltiplos caminhos."""
    start_id = str(start_id)
    resource_id = str(resource_id)

    if start_id not in network.nodes:
        raise ValueError(f"Nó inicial {start_id} não existe na rede.")

    start_node = network.nodes[start_id]
    visited_global: Set[str] = set([start_id])
    found_nodes: List[str] = []
    all_paths: List[List[str]] = []
    total_messages = 0
    found_via_cache: Dict[str, str] = {}

    # Gera múltiplos caminhos aleatórios
    for _ in range(len(start_node.neighbors)):
        if ttl <= 0:
            break
            
        current_node = start_node
        visited_path: Set[str] = set([start_id])
        path: List[str] = [start_id]
        messages = 0
        current_ttl = ttl

        while current_ttl > 0 and current_node.neighbors:
            # Verifica cache local
            if resource_id in current_node.cache:
                owner_id = current_node.cache[resource_id]
                if owner_id not in found_nodes and owner_id in network.nodes:
                    found_nodes.append(owner_id)
                    found_via_cache[resource_id] = owner_id
                    path.append(owner_id)
                    visited_path.add(owner_id)
                    visited_global.add(owner_id)
                    messages += 1
                    # Atualiza cache para o caminho completo
                    _update_cache_along_path(network, path, resource_id, owner_id)
                    break

            # Verifica recursos locais
            if resource_id in current_node.resources and current_node.id not in found_nodes:
                found_nodes.append(current_node.id)
                _update_cache_along_path(network, path, resource_id, current_node.id)

            # Escolhe próximo vizinho
            unvisited = [n for n in current_node.neighbors if n.id not in visited_path]
            if not unvisited:
                break
                
            next_node = random.choice(unvisited)
            path.append(next_node.id)
            visited_path.add(next_node.id)
            visited_global.add(next_node.id)
            messages += 1
            current_ttl -= 1
            current_node = next_node

        # Verificação final no último nó
        if resource_id in current_node.resources and current_node.id not in found_nodes:
            found_nodes.append(current_node.id)
            _update_cache_along_path(network, path, resource_id, current_node.id)
            
        all_paths.append(path)
        total_messages += messages

    # Atualiza cache para todos os caminhos que levaram a recursos
    for owner_id in found_nodes:
        for path in all_paths:
            if owner_id in path:
                _update_cache_along_path(network, path, resource_id, owner_id)

    return SearchResult(
        found=len(found_nodes) > 0,
        start_node=start_id,
        resource_id=resource_id,
        found_nodes=found_nodes,
        visited_nodes=visited_global,
        messages=total_messages,
        paths=all_paths,
        algo="informed_random_walk",
    )


# Mapeamento string -> função
ALGORITHMS = {
    "flooding": flooding,
    "informed_flooding": informed_flooding,
    "random_walk": random_walk,
    "informed_random_walk": informed_random_walk,
}