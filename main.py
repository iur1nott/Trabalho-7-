import argparse
import json
import os
from typing import Tuple, Dict, Any, List

from network import Network
from search_algorithms import ALGORITHMS


# ---------------------------------------------------------------------------
# Funções de carga de configuração (substituem o config_parser.py aqui dentro)
# ---------------------------------------------------------------------------

def _load_yaml(path: str) -> Dict[str, Any]:
    """Tenta carregar YAML usando PyYAML, se estiver disponível."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Para usar arquivos YAML, instale a dependência opcional 'pyyaml' (pip install pyyaml).\n"
            "Ou então use arquivos JSON como configuração."
        ) from exc

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path: str) -> Tuple[Network, Dict[str, Any]]:
    """Carrega o arquivo de configuração e constrói a Network.

    Formato esperado (YAML ou JSON):

    {
      "num_nodes": 12,
      "min_neighbors": 2,
      "max_neighbors": 4,
      "resources": {
        "n1": ["r1", "r2"],
        "n2": ["r3"]
      },
      "edges": [
        ["n1", "n2"],
        ["n1", "n3"]
      ]
    }
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        data = _load_yaml(path)
    elif ext == ".json":
        data = _load_json(path)
    else:
        # tentativa simples: primeiro JSON, depois YAML
        try:
            data = _load_json(path)
        except Exception:
            data = _load_yaml(path)

    required = ["num_nodes", "min_neighbors", "max_neighbors", "resources", "edges"]
    for key in required:
        if key not in data:
            raise ValueError(f"Campo obrigatório '{key}' ausente no arquivo de configuração.")

    num_nodes = int(data["num_nodes"])
    min_neighbors = int(data["min_neighbors"])
    max_neighbors = int(data["max_neighbors"])

    resources_map: Dict[str, List[str]] = data["resources"]
    edges = data["edges"]

    network = Network()

    # Cria nós
    for node_id, resources in resources_map.items():
        network.add_node(node_id, resources)

    # Cria arestas
    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            raise ValueError(f"Aresta inválida no arquivo de configuração: {edge!r}")
        n1, n2 = edge
        network.add_edge(n1, n2)

    # Executa validações da rede
    network.validate(
        num_nodes=num_nodes,
        min_neighbors=min_neighbors,
        max_neighbors=max_neighbors,
    )

    return network, {
        "num_nodes": num_nodes,
        "min_neighbors": min_neighbors,
        "max_neighbors": max_neighbors,
    }


# ---------------------------------------------------------------------------
# CLI (interface de linha de comando)
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Implementação de algoritmos de busca em sistemas P2P não estruturados."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Caminho para o arquivo de configuração (JSON ou YAML).",
    )
    parser.add_argument(
        "--node_id",
        required=True,
        help="Identificador do nó que inicia a busca (ex: n1).",
    )
    parser.add_argument(
        "--resource_id",
        required=True,
        help="Identificador do recurso a ser buscado (ex: r1).",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        required=True,
        help="Valor do TTL (número máximo de saltos da busca).",
    )
    parser.add_argument(
        "--algo",
        required=True,
        choices=list(ALGORITHMS.keys()),
        help="Algoritmo de busca a ser utilizado.",
    )
    return parser.parse_args()


def main():
    print(">>> ENTROU NA MAIN <<<")  # DEBUG

    args = parse_args()

    # Carrega rede a partir do arquivo de configuração
    network, meta = load_config(args.config)

    algo_name = args.algo
    algo_fn = ALGORITHMS[algo_name]

    print("=== Configuração da Rede ===")
    print(f"num_nodes      = {meta['num_nodes']}")
    print(f"min_neighbors  = {meta['min_neighbors']}")
    print(f"max_neighbors  = {meta['max_neighbors']}")
    print()

    # Executa a operação de busca
    result = algo_fn(
        network=network,
        start_id=args.node_id,
        resource_id=args.resource_id,
        ttl=args.ttl,
    )

    print("=== Resultado da Busca ===")
    print(f"Algoritmo           : {result.algo}")
    print(f"Nó inicial          : {result.start_node}")
    print(f"Recurso buscado     : {result.resource_id}")
    print(f"Encontrado?         : {'sim' if result.found else 'não'}")
    if result.found:
        print(f"Encontrado no nó    : {result.found_at}")
    print(f"Mensagens trocadas  : {result.messages}")
    print(f"Nós envolvidos      : {result.num_visited_nodes}")
    print(f"Nós visitados       : {sorted(result.visited_nodes)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n[ERRO DURANTE A EXECUÇÃO]")
        print(e)
    finally:
        input("\nPressione ENTER para sair...")
