import random
from typing import Set, Tuple, List, Optional

from network import Network
from node import Node


class SearchResult:
    """Contém estatísticas de uma operação de busca."""

    def __init__(
        self,
        found: bool,
        start_node: str,
        resource_id: str,
        found_at: Optional[str],
        visited_nodes: Set[str],
        messages: int,
        algo: str,
    ):
        self.found = found
        self.start_node = start_node
        self.resource_id = resource_id
        self.found_at = found_at
        self.visited_nodes = visited_nodes
        self.messages = messages
        self.algo = algo

    @property
    def num_visited_nodes(self) -> int:
        return len(self.visited_nodes)

    def __repr__(self) -> str:
        return (
            f"SearchResult(found={self.found}, found_at={self.found_at}, "
            f"messages={self.messages}, num_visited={self.num_visited_nodes}, algo={self.algo!r})"
        )


# --------------------------------------------------------------------------- #
#  Algoritmos básicos                                                         #
# --------------------------------------------------------------------------- #

def flooding(network: Network, start_id: str, resource_id: str, ttl: int) -> SearchResult:
    """Busca por inundação (flooding) simples.

    - Envia a requisição a todos os vizinhos.
    - Usa fila (BFS) limitada por TTL.
    - Conta número de mensagens como o total de encaminhamentos de requisições.
    """
    start_id = str(start_id)
    resource_id = str(resource_id)

    if start_id not in network.nodes:
        raise ValueError(f"Nó inicial {start_id} não existe na rede.")

    visited: Set[str] = set()
    queue: List[Tuple[str, int]] = [(start_id, ttl)]
    messages = 0

    while queue:
        current_id, t = queue.pop(0)
        if t < 0:
            continue

        if current_id in visited:
            continue

        visited.add(current_id)
        node = network.nodes[current_id]

        # Verifica se o recurso está neste nó
        if resource_id in node.resources:
            return SearchResult(
                found=True,
                start_node=start_id,
                resource_id=resource_id,
                found_at=current_id,
                visited_nodes=visited,
                messages=messages,
                algo="flooding",
            )

        # Encaminha requisições para todos os vizinhos
        for neigh in node.neighbors:
            if neigh.id not in visited and t > 0:
                queue.append((neigh.id, t - 1))
                messages += 1  # cada envio de mensagem é contado

    return SearchResult(
        found=False,
        start_node=start_id,
        resource_id=resource_id,
        found_at=None,
        visited_nodes=visited,
        messages=messages,
        algo="flooding",
    )


def random_walk(network: Network, start_id: str, resource_id: str, ttl: int) -> SearchResult:
    """Busca por passeio aleatório (random walk).

    - Escolhe apenas um vizinho ao acaso em cada passo.
    - TTL limita o número de saltos.
    - Contabiliza uma mensagem por salto.
    """
    start_id = str(start_id)
    resource_id = str(resource_id)

    if start_id not in network.nodes:
        raise ValueError(f"Nó inicial {start_id} não existe na rede.")

    node: Node = network.nodes[start_id]
    visited: Set[str] = set()
    messages = 0

    while ttl >= 0:
        visited.add(node.id)

        if resource_id in node.resources:
            return SearchResult(
                found=True,
                start_node=start_id,
                resource_id=resource_id,
                found_at=node.id,
                visited_nodes=visited,
                messages=messages,
                algo="random_walk",
            )

        if ttl == 0 or not node.neighbors:
            break

        # escolhe um vizinho aleatório
        next_node = random.choice(node.neighbors)
        messages += 1  # salto = uma mensagem
        ttl -= 1
        node = next_node

    return SearchResult(
        found=False,
        start_node=start_id,
        resource_id=resource_id,
        found_at=None,
        visited_nodes=visited,
        messages=messages,
        algo="random_walk",
    )


# --------------------------------------------------------------------------- #
#  Versões informadas (com cache local em cada nó)                            #
# --------------------------------------------------------------------------- #

def _update_cache_along_path(network: Network, path: List[str], resource_id: str, owner_id: str):
    """Atualiza o cache de todos os nós ao longo do caminho com a info de que
    `owner_id` possui `resource_id`.
    """
    for node_id in path:
        node = network.nodes[node_id]
        node.cache[resource_id] = owner_id


def informed_flooding(network: Network, start_id: str, resource_id: str, ttl: int) -> SearchResult:
    """Versão informada da busca por inundação.

    - Antes de inundar, o nó verifica seu cache.
    - Durante o caminho, se algum nó do caminho tiver informação em cache, a busca
      pode ser direcionada mais rapidamente.
    - Ao encontrar o recurso, o caminho percorrido é usado para atualizar o cache.
    """
    start_id = str(start_id)
    resource_id = str(resource_id)

    if start_id not in network.nodes:
        raise ValueError(f"Nó inicial {start_id} não existe na rede.")

    start_node = network.nodes[start_id]

    # Se o nó inicial já sabe onde está o recurso (cache), tentamos ir direto
    if resource_id in start_node.cache:
        target_id = start_node.cache[resource_id]
        if target_id in network.nodes:
            messages = 1
            return SearchResult(
                found=True,
                start_node=start_id,
                resource_id=resource_id,
                found_at=target_id,
                visited_nodes={start_id, target_id},
                messages=messages,
                algo="informed_flooding",
            )

    visited: Set[str] = set()
    # fila com tuplas: (id do nó atual, ttl restante, caminho até aqui)
    queue: List[Tuple[str, int, List[str]]] = [(start_id, ttl, [start_id])]
    messages = 0

    while queue:
        current_id, t, path = queue.pop(0)
        if t < 0:
            continue
        if current_id in visited:
            continue

        visited.add(current_id)
        node = network.nodes[current_id]

        # se cache local sabe onde está o recurso, "encurta" o caminho
        if resource_id in node.cache:
            owner_id = node.cache[resource_id]
            if owner_id in network.nodes:
                new_path = path + [owner_id]
                _update_cache_along_path(network, new_path, resource_id, owner_id)
                messages += 1  # mensagem extra para ir diretamente ao dono
                return SearchResult(
                    found=True,
                    start_node=start_id,
                    resource_id=resource_id,
                    found_at=owner_id,
                    visited_nodes=visited.union({owner_id}),
                    messages=messages,
                    algo="informed_flooding",
                )

        # verifica se o próprio nó possui o recurso
        if resource_id in node.resources:
            owner_id = current_id
            _update_cache_along_path(network, path, resource_id, owner_id)
            return SearchResult(
                found=True,
                start_node=start_id,
                resource_id=resource_id,
                found_at=owner_id,
                visited_nodes=visited,
                messages=messages,
                algo="informed_flooding",
            )

        # inundação tradicional, mas mantendo o caminho
        for neigh in node.neighbors:
            if neigh.id not in visited and t > 0:
                queue.append((neigh.id, t - 1, path + [neigh.id]))
                messages += 1

    return SearchResult(
        found=False,
        start_node=start_id,
        resource_id=resource_id,
        found_at=None,
        visited_nodes=visited,
        messages=messages,
        algo="informed_flooding",
    )


def informed_random_walk(network: Network, start_id: str, resource_id: str, ttl: int) -> SearchResult:
    """Versão informada do passeio aleatório.

    - Em cada nó, antes de escolher um vizinho aleatoriamente, verifica o cache.
    - Se souber onde está o recurso, direciona a busca para o nó dono do recurso.
    - Quando o recurso é encontrado, atualiza o cache de todos os nós visitados.
    """
    start_id = str(start_id)
    resource_id = str(resource_id)

    if start_id not in network.nodes:
        raise ValueError(f"Nó inicial {start_id} não existe na rede.")

    node: Node = network.nodes[start_id]
    visited: Set[str] = set()
    path: List[str] = [start_id]
    messages = 0

    while ttl >= 0:
        visited.add(node.id)

        # se o nó atual tem o recurso
        if resource_id in node.resources:
            owner_id = node.id
            _update_cache_along_path(network, path, resource_id, owner_id)
            return SearchResult(
                found=True,
                start_node=start_id,
                resource_id=resource_id,
                found_at=owner_id,
                visited_nodes=visited,
                messages=messages,
                algo="informed_random_walk",
            )

        # se ele não tem, mas o cache sabe onde está
        if resource_id in node.cache:
            owner_id = node.cache[resource_id]
            if owner_id in network.nodes:
                path.append(owner_id)
                _update_cache_along_path(network, path, resource_id, owner_id)
                messages += 1  # mensagem para ir direto ao dono
                visited.add(owner_id)
                return SearchResult(
                    found=True,
                    start_node=start_id,
                    resource_id=resource_id,
                    found_at=owner_id,
                    visited_nodes=visited,
                    messages=messages,
                    algo="informed_random_walk",
                )

        if ttl == 0 or not node.neighbors:
            break

        # escolha aleatória de vizinho
        next_node = random.choice(node.neighbors)
        messages += 1
        ttl -= 1
        node = next_node
        path.append(node.id)

    return SearchResult(
        found=False,
        start_node=start_id,
        resource_id=resource_id,
        found_at=None,
        visited_nodes=visited,
        messages=messages,
        algo="informed_random_walk",
    )


# Mapeamento string -> função, útil para a main/CLI
ALGORITHMS = {
    "flooding": flooding,
    "informed_flooding": informed_flooding,
    "random_walk": random_walk,
    "informed_random_walk": informed_random_walk,
}
