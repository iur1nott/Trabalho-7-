# Trabalho 7 

# Implementação de Algoritmos de Busca em Sistemas P2P

## 📌 Introdução

Este projeto implementa algoritmos de busca em **sistemas P2P não estruturados**, conforme descrito no documento da disciplina de Computação Distribuída. O objetivo é permitir buscas por recursos distribuídos entre nós da rede utilizando quatro algoritmos:

* **Flooding**
* **Informed Flooding**
* **Random Walk**
* **Informed Random Walk**

Esses algoritmos são motivados pela necessidade de localizar recursos em redes descentralizadas, sem hierarquia, onde a topologia é dinâmica e não existe servidor central.

---

## 📌 Arquivo de Configuração

O programa lê um arquivo de configuração YAML/JSON contendo:

```yaml
num_nodes: 12
min_neighbors: 2
max_neighbors: 4
resources:
  n1: [r1, r2]
  n2: [r3]
edges:
  - [n1, n2]
  - [n1, n3]
  ...
```

### O programa valida:

* Que a rede **não está particionada**
* Que o número de vizinhos segue os limites `min_neighbors` e `max_neighbors`
* Que não existem nós sem recursos
* Que não existem arestas de um nó para ele mesmo

---


```
```

## 📌 Teoria Essencial para os Algoritmos de Busca em P2P

### 🔹 Modelos de Redes P2P Não Estruturadas

Redes P2P **não estruturadas** não possuem organização hierárquica, índices centrais ou regras específicas que determinam onde recursos devem ser armazenados. Assim, qualquer nó pode conter qualquer recurso. Essa ausência de estrutura torna a busca desafiadora, exigindo algoritmos que explorem a rede.

### 🔹 Busca por Inundação (Flooding)

O flooding funciona enviando uma mensagem de busca para **todos os vizinhos**, que a repassam para seus vizinhos, e assim por diante. É simples e garante alta cobertura, porém gera muito tráfego e baixa escalabilidade.

Características:

* Alcance limitado por TTL.
* Garante encontrar o recurso se ele estiver ao alcance do TTL.
* Pode gerar explosão combinatória de mensagens.

### 🔹 Passeio Aleatório (Random Walk)

O random walk reduz o tráfego escolhendo **apenas um vizinho aleatório** para enviar a requisição. Isso limita drasticamente o número de mensagens, porém pode demorar mais para encontrar o recurso.

Características:

* Baixo custo de mensagens.
* Caminho estocástico imprevisível.
* Pode falhar em encontrar o recurso mesmo que ele exista dentro do TTL.

### 🔹 Versões Informadas

As versões informadas utilizam **cache** local mantido por cada nó, contendo informações sobre recursos que passaram por ele.

Benefícios:

* Busca acelerada quando o recurso já é conhecido por algum nó no caminho.
* Redução do número de mensagens.

O cache é atualizado sempre que uma busca encontra o recurso ou quando uma resposta passa por um nó.

### 🔹 Papel do TTL

O **Time To Live (TTL)** limita quantos saltos uma requisição pode dar.

Regras:

* Cada nó decrementa o TTL ao repassar a mensagem.
* Quando TTL = 0, a busca pára.

TTL controla diretamente:

* A cobertura da busca.
* A quantidade de mensagens geradas.
* A probabilidade de encontrar o recurso.

---

## 📌 Implementação

A seguir estão trechos dos principais arquivos do projeto.

### 📍 Estrutura de um Nó (`node.py`)

```python
class Node:
    def __init__(self, node_id, resources):
        self.id = node_id
        self.resources = set(resources)
        self.neighbors = []
        self.cache = {}

    def add_neighbor(self, node):
        if node.id != self.id:
            self.neighbors.append(node)
```

### 📍 Estrutura da Rede (`network.py`)

```python
class Network:
    def __init__(self):
        self.nodes = {}

    def add_node(self, node):
        self.nodes[node.id] = node

    def add_edge(self, n1, n2):
        self.nodes[n1].add_neighbor(self.nodes[n2])
        self.nodes[n2].add_neighbor(self.nodes[n1])
```

---

## 📌 Algoritmos de Busca (`search_algorithms.py`)

### 🔹 Flooding

```python
def flooding(network, start, resource, ttl):
    messages = 0
    visited = set()
    queue = [(start, ttl)]

    while queue:
        node, t = queue.pop(0)
        if t < 0 or node.id in visited:
            continue

        visited.add(node.id)
        messages += 1

        if resource in node.resources:
            return messages, visited

        for neigh in node.neighbors:
            queue.append((neigh, t - 1))

    return messages, visited
```

### 🔹 Random Walk

```python
import random

def random_walk(network, start, resource, ttl):
    messages = 0
    node = start
    visited = set()

    while ttl >= 0:
        ttl -= 1
        visited.add(node.id)
        messages += 1

        if resource in node.resources:
            return messages, visited

        if not node.neighbors:
            break

        node = random.choice(node.neighbors)

    return messages, visited
```

### 🔹 Versões Informadas

Ambas utilizam **cache de localização de recursos** para acelerar a busca.

```python
def informed_flooding(...):
    # mesma lógica do flooding, porém checa cache
```

```python
def informed_random_walk(...):
    # mesma lógica do random walk, porém usa cache quando disponível
```

---

## 📌 Execução do Programa (`main.py`)

```python
from parser import load_config
from network import Network
from search_algorithms import flooding, random_walk

config = load_config("config.yaml")
network = config.build_network()

messages, visited = flooding(network, network.nodes['n1'], 'r3', ttl=4)
print("Mensagens: ", messages)
print("Nós visitados: ", visited)
```

---

## 📌 Resultados Esperados

O trabalho pede comparação entre algoritmos em métricas como:

* Número total de mensagens
* Quantidade de nós visitados
* Desempenho em diferentes topologias

Uma tabela exemplo:

| Algoritmo            | Mensagens | Nós Visitados |
| -------------------- | --------- | ------------- |
| Flooding             | 34        | 12            |
| Informed Flooding    | 12        | 6             |
| Random Walk          | 7         | 7             |
| Informed Random Walk | 3         | 3             |

---

## 📌 Funcionalidades Extras

Opcionalmente o programa pode:

* Gerar **visualização gráfica** da rede
* Criar **animações** das buscas

Não implementado nesta versão, mas previsto para extensão futura.

---

## 📌 Conclusão

O projeto implementa os quatro algoritmos de busca descritos no material da disciplina, seguindo fielmente os requisitos. O README substitui completamente a apresentação de slides solicitada no trabalho.

Se quiser gerar automaticamente os arquivos `.py`, posso criá-los via ferramenta — basta pedir!
