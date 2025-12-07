# Implementação e Avaliação de Algoritmos de Busca em Redes P2P

---

# Introdução

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

# Arquivos de Topologia

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

# Descrição dos Algoritmos

## Flooding

Envia a requisição para todos os vizinhos, que repassam aos seus vizinhos, até encontrar o recurso ou o TTL acabar. Garante encontrar o recurso, mas é caro em mensagens.

## Informed Flooding

Mesma lógica do flooding, porém utiliza **cache** quando disponível. No primeiro uso, comporta-se igual ao flooding tradicional.

## Random Walk

Escolhe um único vizinho aleatoriamente a cada passo. Usa poucas mensagens, mas pode falhar.

## Informed Random Walk

Usa cache para guiar o passeio aleatório quando possível. No primeiro uso, é igual ao random walk simples.

---

# Resultados Consolidados

A seguir estão todas as execuções realizadas no projeto.

---

## Topologia: **LINHA**

| Algoritmo            | Mensagens | Nós Visitados  | Encontrou? | Onde? |
| -------------------- | --------- | -------------- | ---------- | ----- |
| Flooding             | 5         | 6              | Sim        | n6    |
| Informed Flooding    | 5         | 6              | Sim        | n6    |
| Random Walk          | 5         | n1, n2, n3, n4 | Não        | –     |
| Informed Random Walk | 5         | n1, n2, n3, n4 | Não        | –     |

---

## Topologia: **ANEL**

| Algoritmo            | Mensagens | Nós Visitados  | Encontrou? | Onde? |
| -------------------- | --------- | -------------- | ---------- | ----- |
| Flooding             | 6         | 6              | Sim        | n4    |
| Informed Flooding    | 6         | 6              | Sim        | n4    |
| Random Walk          | 3         | n1, n2, n6     | Não        | –     |
| Informed Random Walk | 3         | n1, n4, n5, n6 | Sim        | n4    |

---

## Topologia: **MALHA**

| Algoritmo            | Mensagens | Nós Visitados | Encontrou? | Onde? |
| -------------------- | --------- | ------------- | ---------- | ----- |
| Flooding             | 8         | 6             | Sim        | n6    |
| Informed Flooding    | 8         | 6             | Sim        | n6    |
| Random Walk          | 3         | n1, n2        | Não        | –     |
| Informed Random Walk | 3         | n1, n2, n3    | Não        | –     |

---

## Topologia: **DENSA**

| Algoritmo            | Mensagens | Nós Visitados | Encontrou? | Onde? |
| -------------------- | --------- | ------------- | ---------- | ----- |
| Flooding             | 10        | 6             | Sim        | n6    |
| Informed Flooding    | 10        | 6             | Sim        | n6    |
| Random Walk          | 3         | n1, n3, n4    | Não        | –     |
| Informed Random Walk | 3         | n1, n2, n3    | Não        | –     |

---

# Gráficos ASCII

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

# Análise Teórica dos Resultados

## Comparação geral

* Flooding sempre encontra o recurso, mas gasta muitas mensagens.
* Informed Flooding só melhora após buscas repetidas.
* Random Walk usa poucas mensagens, mas pode falhar.
* Informed Random Walk se destaca quando o cache está populado.

## Impacto da topologia

* Linha: caminho único → random walk falha facilmente.
* Anel: duas direções possíveis → informed RW se destaca.
* Malha: conectividade média → flooding cresce mais.
* Densa: flooding explode em mensagens; RW continua leve.

## Análise gráfica

### **Eficiência: taxa de sucesso por custo**

<img width="4471" height="3543" alt="efficiency_comparison" src="https://github.com/user-attachments/assets/2150a82e-035e-4d2f-835a-e6833a4eaf62" />


Os gráficos de eficiência mostram como cada algoritmo performa em termos de **sucesso por mensagem enviada**, variando o TTL e a topologia. Observa-se que:

* **Flooding** e **Informed Flooding** apresentam eficiência moderada e relativamente estável, pois enviam muitas mensagens para garantir a descoberta.
* **Random Walk** mostra baixa eficiência em quase todas as topologias para TTLs pequenos, refletindo seu caráter probabilístico.
* **Informed Random Walk**, por outro lado, atinge a maior eficiência nos cenários onde o TTL é suficiente para alcançar a região do grafo onde o recurso está, especialmente em topologias mais conectadas como *malha* e *densa*.
* No geral, quando o cache é utilizável, o Informed RW domina totalmente os demais em termos de eficiência por mensagem.

Esses gráficos reforçam o trade-off entre **confiabilidade (flooding)** e **eficiência (random walk)**.

### **Tempo de Execução vs TTL**

<img width="4766" height="3542" alt="execution_time_analysis" src="https://github.com/user-attachments/assets/c1184bf1-c9af-4d16-bc6f-0492c59c611d" />


Os tempos de execução mostram como a complexidade prática de cada algoritmo cresce conforme o TTL aumenta:

* **Flooding** é consistentemente um dos algoritmos mais lentos, pois envolve a disseminação massiva da mensagem.
* **Informed Flooding** é bem mais rápido porque, após o primeiro uso, sua busca se torna direcionada pelo cache. Isso é visível pela queda acentuada do tempo.
* **Random Walk** apresenta os maiores tempos à medida que o TTL cresce, especialmente em topologias maiores, pois depende de longas sequências de passos individuais.
* **Informed Random Walk** é o mais rápido de todos, mantendo um tempo quase constante, independentemente do TTL, devido à navegação mais previsível oferecida pelo cache.

Esses resultados evidenciam que o **uso de cache reduz drasticamente a latência**, principalmente nos métodos informados.

### **Eficiência de Busca: Nós Visitados por Mensagem**

<img width="4767" height="3542" alt="search_efficiency" src="https://github.com/user-attachments/assets/481a0258-32c5-46fc-bec5-a0d06559ec74" />


Os gráficos de nós visitados por mensagem detalham melhor o "custo interno" da busca:

* **Flooding** visita sempre um número alto de nós, como esperado, já que faz broadcast.
* **Informed Flooding** tende a reduzir esse número conforme o TTL aumenta e o cache acumula informações, aproximando-se do limite mínimo necessário.
* **Random Walk** visita poucos nós, mas de forma pouco eficaz, pois a baixa exploração pode impedir que o recurso seja encontrado.
* **Informed Random Walk** visita poucos nós *e* mantém boa taxa de sucesso nas topologias em que o cache favorece caminhos curtos, tornando-o o algoritmo mais eficiente no longo prazo.

Aqui fica evidente a diferença entre **baixo custo com baixa eficiência (RW)** e **baixo custo com alta eficiência (informed RW)**.

### **Comparação Geral de Mensagens por Topologia**

<img width="1600" height="960" alt="image" src="https://github.com/user-attachments/assets/0f0a7b6f-e29d-4f10-ab0c-abfb20bfbc51" />


O gráfico de barras confirma a forte tendência já vista:

* Flooding e Informed Flooding sempre geram o maior volume de mensagens, proporcional à densidade da topologia.
* Random Walk e Informed Random Walk geram um número fixo (três) de mensagens, independentemente da densidade.
* A consistência dos random walks no eixo das mensagens mostra porque são tão atrativos para sistemas com limitação de largura de banda.
* O custo explosivo do flooding nas topologias mais densas evidencia seu uso restrito a cenários onde o sucesso é mais importante que o custo.

Esse gráfico sintetiza bem o **trade-off central do trabalho: custo vs confiabilidade**.

---

# Conclusão

Os experimentos demonstram o trade-off clássico em redes P2P entre **custo de comunicação** e **probabilidade de sucesso da busca**. Flooding garante descoberta, mas com custo elevado. Random Walk reduz o custo, mas pode falhar. Métodos informados melhoram significativamente quando há reutilização de cache.

Na prática, sistemas P2P reais utilizam estratégias híbridas, combinando:

* cache distribuído,
* random walks paralelos,
* flooding com limitação de TTL.

Esta implementação e análise permitem compreender profundamente o funcionamento e impacto desses algoritmos em diferentes topologias.

---

Se quiser, posso integrar esta versão final ao GitHub em formato markdown otimizado.
