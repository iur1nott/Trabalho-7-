# Implementação e Avaliação de Algoritmos de Busca em Redes P2P

---

# 📌 Introdução

Sistemas P2P não estruturados dependem de algoritmos de busca para localizar recursos distribuídos entre os nós, sem coordenadores centrais. Neste trabalho foram implementados e avaliados quatro algoritmos:

* **Flooding**
* **Informed Flooding**
* **Random Walk**
* **Informed Random Walk**

Cada algoritmo foi testado em quatro topologias:

* Linha
* Anel
* Malha
* Densa

Todos os testes foram executados com o programa implementado no projeto.

---

# 📁 Arquivos de Topologia

O projeto utiliza configurações JSON que descrevem:

* número de nós
* limites de vizinhos
* recursos por nó
* arestas (conectividade)

As topologias avaliadas são:

* `linha.json`
* `anel.json`
* `malha.json`
* `densa.json`

---

# 🧠 Descrição dos Algoritmos

## 🔹 Flooding

Envia a requisição para todos os vizinhos, que repassam aos seus vizinhos, até encontrar o recurso ou o TTL acabar. Garante encontrar o recurso, mas é caro em mensagens.

## 🔹 Informed Flooding

Mesma lógica do flooding, porém utiliza **cache** quando disponível. No primeiro uso, comporta-se igual ao flooding tradicional.

## 🔹 Random Walk

Escolhe um único vizinho aleatoriamente a cada passo. Usa poucas mensagens, mas pode falhar.

## 🔹 Informed Random Walk

Usa cache para guiar o passeio aleatório quando possível. No primeiro uso, é igual ao random walk simples.

---

# 📊 Resultados Consolidados

A seguir estão todas as execuções realizadas no projeto.

---

## 🔷 Topologia: **LINHA**

| Algoritmo            | Mensagens | Nós Visitados  | Encontrou? | Onde? |
| -------------------- | --------- | -------------- | ---------- | ----- |
| Flooding             | 5         | 6              | Sim        | n6    |
| Informed Flooding    | 5         | 6              | Sim        | n6    |
| Random Walk          | 5         | n1, n2, n3, n4 | Não        | –     |
| Informed Random Walk | 5         | n1, n2, n3, n4 | Não        | –     |

---

## 🔷 Topologia: **ANEL**

| Algoritmo            | Mensagens | Nós Visitados  | Encontrou? | Onde? |
| -------------------- | --------- | -------------- | ---------- | ----- |
| Flooding             | 6         | 6              | Sim        | n4    |
| Informed Flooding    | 6         | 6              | Sim        | n4    |
| Random Walk          | 3         | n1, n2, n6     | Não        | –     |
| Informed Random Walk | 3         | n1, n4, n5, n6 | Sim        | n4    |

---

## 🔷 Topologia: **MALHA**

| Algoritmo            | Mensagens | Nós Visitados | Encontrou? | Onde? |
| -------------------- | --------- | ------------- | ---------- | ----- |
| Flooding             | 8         | 6             | Sim        | n6    |
| Informed Flooding    | 8         | 6             | Sim        | n6    |
| Random Walk          | 3         | n1, n2        | Não        | –     |
| Informed Random Walk | 3         | n1, n2, n3    | Não        | –     |

---

## 🔷 Topologia: **DENSA**

| Algoritmo            | Mensagens | Nós Visitados | Encontrou? | Onde? |
| -------------------- | --------- | ------------- | ---------- | ----- |
| Flooding             | 10        | 6             | Sim        | n6    |
| Informed Flooding    | 10        | 6             | Sim        | n6    |
| Random Walk          | 3         | n1, n3, n4    | Não        | –     |
| Informed Random Walk | 3         | n1, n2, n3    | Não        | –     |

---

# 📈 Gráficos ASCII

## LINHA

```
Flooding           █████ (5)
Informed Flooding  █████ (5)
Random Walk        █████ (5)
Informed R. Walk   █████ (5)
```

## ANEL

```
Flooding           ██████ (6)
Informed Flooding  ██████ (6)
Random Walk        ███ (3)
Informed R. Walk   ███ (3)
```

## MALHA

```
Flooding           ████████ (8)
Informed Flooding  ████████ (8)
Random Walk        ███ (3)
Informed R. Walk   ███ (3)
```

## DENSA

```
Flooding           ██████████ (10)
Informed Flooding  ██████████ (10)
Random Walk        ███ (3)
Informed R. Walk   ███ (3)
```

---

# 🧾 Análise Teórica dos Resultados

## 📌 Comparação Geral

* Flooding sempre encontra o recurso, mas gasta muitas mensagens.
* Informed Flooding só melhora após buscas repetidas.
* Random Walk usa poucas mensagens, mas pode falhar.
* Informed Random Walk se destaca quando o cache está populado.

## 📌 Impacto da Topologia

* Linha: caminho único → random walk falha facilmente.
* Anel: duas direções possíveis → informed RW se destaca.
* Malha: conectividade média → flooding cresce mais.
* Densa: flooding explode em mensagens; RW continua leve.

---

# 🏁 Conclusão

Os experimentos demonstram o trade-off clássico em redes P2P entre **custo de comunicação** e **probabilidade de sucesso da busca**. Flooding garante descoberta, mas com custo elevado. Random Walk reduz o custo, mas pode falhar. Métodos informados melhoram significativamente quando há reutilização de cache.

Na prática, sistemas P2P reais utilizam estratégias híbridas, combinando:

* cache distribuído,
* random walks paralelos,
* flooding com limitação de TTL.

Esta implementação e análise permitem compreender profundamente o funcionamento e impacto desses algoritmos em diferentes topologias.

---

Se quiser, posso integrar esta versão final ao GitHub em formato markdown otimizado.
