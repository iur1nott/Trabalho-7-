import json
import random
import time
import statistics
from typing import Dict, List, Tuple, Any
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from network import Network
from search_algorithms import ALGORITHMS

class P2PBenchmark:
    """Classe para realizar benchmarks dos algoritmos de busca P2P"""
    
    def __init__(self):
        self.results = {}
        
    def load_topology(self, config_file: str) -> Tuple[Network, Dict[str, List[str]]]:
        """Carrega uma topologia do arquivo JSON"""
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        network = Network()
        
        # Cria nós
        for node_id, resources in data["resources"].items():
            network.add_node(node_id, resources)
        
        # Cria arestas
        for edge in data["edges"]:
            network.add_edge(edge[0], edge[1])
        
        # Valida a rede
        network.validate(
            num_nodes=data["num_nodes"],
            min_neighbors=data["min_neighbors"],
            max_neighbors=data["max_neighbors"]
        )
        
        # Retorna a rede e o mapeamento de recursos
        resource_map = {}
        for node_id, resources in data["resources"].items():
            for resource in resources:
                if resource not in resource_map:
                    resource_map[resource] = []
                resource_map[resource].append(node_id)
        
        return network, resource_map
    
    def run_single_test(self, network: Network, start_node: str, 
                       resource_id: str, ttl: int, algorithm: str) -> Dict[str, Any]:
        """Executa um único teste e retorna as métricas"""
        algo_fn = ALGORITHMS[algorithm]
        
        start_time = time.perf_counter()
        result = algo_fn(
            network=network,
            start_id=start_node,
            resource_id=resource_id,
            ttl=ttl
        )
        end_time = time.perf_counter()
        
        return {
            'found': result.found,
            'execution_time': (end_time - start_time) * 1000,  # ms
            'messages': result.messages,
            'visited_nodes': len(result.visited_nodes),
            'success': result.found,
            'found_at': result.found_at
        }
    
    def run_benchmark(self, config_files: List[str], algorithms: List[str], 
                     ttl_values: List[int], num_tests: int = 100) -> Dict[str, Any]:
        """Executa benchmark completo para múltiplas configurações"""
        
        all_results = {}
        
        for config_file in config_files:
            config_name = config_file.split('/')[-1].split('.')[0]
            print(f"\n{'='*60}")
            print(f"Testando topologia: {config_name}")
            print(f"{'='*60}")
            
            # Carrega a rede
            network, resource_map = self.load_topology(config_file)
            nodes = list(network.nodes.keys())
            
            config_results = {}
            
            for algorithm in algorithms:
                print(f"\n  Algoritmo: {algorithm}")
                print(f"  {'-'*40}")
                
                algo_results = {}
                
                for ttl in ttl_values:
                    print(f"    TTL={ttl}: ", end='', flush=True)
                    
                    # Métricas acumuladas
                    metrics = {
                        'success_rate': [],
                        'execution_times': [],
                        'message_counts': [],
                        'visited_counts': [],
                        'latency_efficiency': []  # mensagens/ms
                    }
                    
                    # Executa múltiplos testes
                    for test_num in range(num_tests):
                        # Escolhe nó inicial aleatório
                        start_node = random.choice(nodes)
                        
                        # Escolhe recurso aleatório que existe na rede
                        available_resources = list(resource_map.keys())
                        if not available_resources:
                            continue
                        resource_id = random.choice(available_resources)
                        
                        # Executa o teste
                        test_result = self.run_single_test(
                            network=network,
                            start_node=start_node,
                            resource_id=resource_id,
                            ttl=ttl,
                            algorithm=algorithm
                        )
                        
                        # Acumula métricas
                        metrics['success_rate'].append(1 if test_result['success'] else 0)
                        metrics['execution_times'].append(test_result['execution_time'])
                        metrics['message_counts'].append(test_result['messages'])
                        metrics['visited_counts'].append(test_result['visited_nodes'])
                        
                        # Calcula eficiência de latência (quanto menor, melhor)
                        if test_result['execution_time'] > 0:
                            latency_eff = test_result['messages'] / test_result['execution_time']
                            metrics['latency_efficiency'].append(latency_eff)
                        
                        if test_num % 20 == 0:
                            print(".", end='', flush=True)
                    
                    print()  # Nova linha após os pontos de progresso
                    
                    # Calcula estatísticas para este TTL
                    algo_results[ttl] = {
                        'success_rate_mean': statistics.mean(metrics['success_rate']) * 100,
                        'success_rate_std': statistics.stdev(metrics['success_rate']) * 100 if len(metrics['success_rate']) > 1 else 0,
                        
                        'execution_time_mean': statistics.mean(metrics['execution_times']),
                        'execution_time_std': statistics.stdev(metrics['execution_times']) if len(metrics['execution_times']) > 1 else 0,
                        
                        'messages_mean': statistics.mean(metrics['message_counts']),
                        'messages_std': statistics.stdev(metrics['message_counts']) if len(metrics['message_counts']) > 1 else 0,
                        
                        'visited_mean': statistics.mean(metrics['visited_counts']),
                        'visited_std': statistics.stdev(metrics['visited_counts']) if len(metrics['visited_counts']) > 1 else 0,
                        
                        'latency_eff_mean': statistics.mean(metrics['latency_efficiency']) if metrics['latency_efficiency'] else 0,
                        'latency_eff_std': statistics.stdev(metrics['latency_efficiency']) if len(metrics['latency_efficiency']) > 1 else 0,
                    }
                
                config_results[algorithm] = algo_results
            
            all_results[config_name] = config_results
        
        self.results = all_results
        return all_results
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Salva os resultados em um arquivo JSON"""
        with open(filename, 'w') as f:
            # Converte para formato serializável
            json_results = {}
            for topology, algo_data in self.results.items():
                json_results[topology] = {}
                for algo, ttl_data in algo_data.items():
                    json_results[topology][algo] = ttl_data
            
            json.dump(json_results, f, indent=2)
        print(f"\nResultados salvos em {filename}")
    
    def plot_comparative_results(self):
        """Gera gráficos comparativos dos resultados com visualizações mais significativas"""
        if not self.results:
            print("Nenhum resultado para plotar!")
            return
        
        topologies = list(self.results.keys())
        algorithms = list(self.results[topologies[0]].keys())
        ttl_values = sorted(list(self.results[topologies[0]][algorithms[0]].keys()))
        
        # Configuração do estilo dos gráficos
        plt.style.use('seaborn-v0_8-whitegrid')
        colors = cm.get_cmap('tab10', len(algorithms))
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'X']
        line_styles = ['-', '--', '-.', ':']
        
        # 1. Taxa de Sucesso por Topologia e Algoritmo (mantido mas melhorado)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True, sharey=True)
        fig.suptitle('Taxa de Sucesso por TTL e Topologia', fontsize=18, fontweight='bold', y=0.98)
        
        for idx, topology in enumerate(topologies):
            ax = axes[idx // 2, idx % 2]
            
            for algo_idx, algorithm in enumerate(algorithms):
                success_rates = []
                for ttl in ttl_values:
                    success_rates.append(self.results[topology][algorithm][ttl]['success_rate_mean'])
                
                ax.plot(ttl_values, success_rates, 
                       marker=markers[algo_idx % len(markers)],
                       linestyle=line_styles[algo_idx % len(line_styles)],
                       color=colors(algo_idx),
                       linewidth=2.5,
                       markersize=9,
                       markerfacecolor='white',
                       markeredgewidth=2,
                       label=algorithm.replace('_', ' ').title(),
                       alpha=0.9)
            
            ax.set_title(f'Topologia: {topology.replace("_", " ").title()}', fontsize=14, fontweight='bold', pad=15)
            ax.set_ylabel('Taxa de Sucesso (%)', fontsize=12)
            ax.set_xlabel('TTL', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.7, which='both')
            ax.set_ylim(-5, 105)
            ax.set_xlim(min(ttl_values)-1, max(ttl_values)+1)
        
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=len(algorithms), 
                  bbox_to_anchor=(0.5, 0.96), fontsize=12, frameon=True, shadow=True)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig('success_rate_comparison.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # 2. Análise de Custo-Benefício: Mensagens vs Sucesso (NOVO GRÁFICO)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True)
        fig.suptitle('Análise de Custo-Benefício: Mensagens vs Taxa de Sucesso', fontsize=18, fontweight='bold', y=0.98)
        
        for idx, topology in enumerate(topologies):
            ax = axes[idx // 2, idx % 2]
            
            # Coletar dados para o gráfico de bolhas
            all_messages = []
            all_success = []
            all_sizes = []  # Tamanho proporcional ao TTL
            all_colors = []  # Cor por algoritmo
            
            for algo_idx, algorithm in enumerate(algorithms):
                for ttl in ttl_values:
                    stats = self.results[topology][algorithm][ttl]
                    all_messages.append(stats['messages_mean'])
                    all_success.append(stats['success_rate_mean'])
                    all_sizes.append(ttl * 5)  # Tamanho proporcional ao TTL
                    all_colors.append(colors(algo_idx))
            
            # Calcular limites para escala logarítmica
            min_msg = max(1, min(all_messages) * 0.8)
            max_msg = max(all_messages) * 1.2
            
            # Criar gráfico de dispersão com tamanhos proporcionais ao TTL
            scatter = ax.scatter(all_messages, all_success, 
                               s=all_sizes, 
                               c=range(len(all_colors)), 
                               cmap='tab10',
                               alpha=0.7,
                               edgecolors='w',
                               linewidth=1)
            
            # Adicionar linhas de tendência por algoritmo
            for algo_idx, algorithm in enumerate(algorithms):
                messages = []
                success = []
                for ttl in ttl_values:
                    stats = self.results[topology][algorithm][ttl]
                    messages.append(stats['messages_mean'])
                    success.append(stats['success_rate_mean'])
                
                # Suavizar a linha de tendência
                if len(messages) > 1:
                    z = np.polyfit(messages, success, 2)
                    p = np.poly1d(z)
                    x_trend = np.linspace(min(messages), max(messages), 50)
                    ax.plot(x_trend, p(x_trend), 
                           color=colors(algo_idx), 
                           linestyle=line_styles[algo_idx % len(line_styles)],
                           linewidth=2.5,
                           alpha=0.8,
                           label=algorithm.replace('_', ' ').title())
            
            ax.set_title(f'Topologia: {topology.replace("_", " ").title()}', fontsize=14, fontweight='bold', pad=15)
            ax.set_ylabel('Taxa de Sucesso (%)', fontsize=12)
            ax.set_xlabel('Número Médio de Mensagens (escala log)', fontsize=12)
            ax.set_xscale('log')
            ax.set_xlim(min_msg, max_msg)
            ax.set_ylim(-5, 105)
            ax.grid(True, linestyle='--', alpha=0.7, which='both')
            
            # Adicionar anotações para TTLs extremos
            for ttl in [min(ttl_values), max(ttl_values)]:
                for algo_idx, algorithm in enumerate(algorithms):
                    stats = self.results[topology][algorithm][ttl]
                    ax.annotate(f'TTL={ttl}', 
                              (stats['messages_mean'], stats['success_rate_mean']),
                              xytext=(5, 5), textcoords='offset points',
                              fontsize=9, alpha=0.8)
        
        # Criar legenda para algoritmos
        handles = [plt.Line2D([0], [0], color=colors(i), lw=2.5, 
                 ls=line_styles[i % len(line_styles)], 
                 label=algorithms[i].replace('_', ' ').title()) 
                 for i in range(len(algorithms))]
        fig.legend(handles, [alg.replace('_', ' ').title() for alg in algorithms], 
                  loc='upper center', ncol=len(algorithms),
                  bbox_to_anchor=(0.5, 0.96), fontsize=12, frameon=True, shadow=True)
        
        # Adicionar legenda de tamanho (TTL)
        ax = axes[1, 1]
        legend_elements = [
            plt.scatter([], [], s=ttl*5, color='gray', alpha=0.7, edgecolors='w', linewidth=1, 
                       label=f'TTL={ttl}') for ttl in [min(ttl_values), np.median(ttl_values).astype(int), max(ttl_values)]
        ]
        ax.legend(handles=legend_elements, loc='lower right', title='Tamanho do Ponto', 
                 fontsize=10, frameon=True, shadow=True)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig('cost_benefit_analysis.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # 3. Eficiência de Busca: Nós Visitados por Mensagem (NOVO GRÁFICO)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharey=True)
        fig.suptitle('Eficiência de Busca: Nós Visitados por Mensagem', fontsize=18, fontweight='bold', y=0.98)
        
        for idx, topology in enumerate(topologies):
            ax = axes[idx // 2, idx % 2]
            
            for algo_idx, algorithm in enumerate(algorithms):
                efficiency = []
                for ttl in ttl_values:
                    stats = self.results[topology][algorithm][ttl]
                    # Evitar divisão por zero
                    msg = max(1, stats['messages_mean'])
                    eff = stats['visited_mean'] / msg
                    efficiency.append(eff)
                
                ax.plot(ttl_values, efficiency,
                       marker=markers[algo_idx % len(markers)],
                       linestyle=line_styles[algo_idx % len(line_styles)],
                       color=colors(algo_idx),
                       linewidth=2.5,
                       markersize=9,
                       markerfacecolor='white',
                       markeredgewidth=2,
                       label=algorithm.replace('_', ' ').title(),
                       alpha=0.9)
            
            ax.set_title(f'Topologia: {topology.replace("_", " ").title()}', fontsize=14, fontweight='bold', pad=15)
            ax.set_ylabel('Nós Visitados por Mensagem', fontsize=12)
            ax.set_xlabel('TTL', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.7, which='both')
            ax.set_yscale('log')
        
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=len(algorithms),
                  bbox_to_anchor=(0.5, 0.96), fontsize=12, frameon=True, shadow=True)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig('search_efficiency.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # 4. Análise de Tempo de Execução (NOVO GRÁFICO)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True)
        fig.suptitle('Tempo de Execução vs TTL', fontsize=18, fontweight='bold', y=0.98)
        
        for idx, topology in enumerate(topologies):
            ax = axes[idx // 2, idx % 2]
            
            for algo_idx, algorithm in enumerate(algorithms):
                times = []
                for ttl in ttl_values:
                    times.append(self.results[topology][algorithm][ttl]['execution_time_mean'])
                
                ax.plot(ttl_values, times,
                       marker=markers[algo_idx % len(markers)],
                       linestyle=line_styles[algo_idx % len(line_styles)],
                       color=colors(algo_idx),
                       linewidth=2.5,
                       markersize=9,
                       markerfacecolor='white',
                       markeredgewidth=2,
                       label=algorithm.replace('_', ' ').title(),
                       alpha=0.9)
            
            ax.set_title(f'Topologia: {topology.replace("_", " ").title()}', fontsize=14, fontweight='bold', pad=15)
            ax.set_ylabel('Tempo de Execução (ms)', fontsize=12)
            ax.set_xlabel('TTL', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.7, which='both')
            ax.set_yscale('log')
        
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=len(algorithms),
                  bbox_to_anchor=(0.5, 0.96), fontsize=12, frameon=True, shadow=True)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig('execution_time_analysis.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # 5. Comparação Direta para TTL=10 (CORRIGIDO)
        fig, ax = plt.subplots(figsize=(14, 8))
        
        ttl_fixed = 10
        bar_width = 0.15
        x = np.arange(len(topologies))
        
        bar_containers = []
        for algo_idx, algorithm in enumerate(algorithms):
            values = []
            errors = []
            for topology in topologies:
                if ttl_fixed in self.results[topology][algorithm]:
                    stats = self.results[topology][algorithm][ttl_fixed]
                    values.append(stats['success_rate_mean'])
                    errors.append(stats['success_rate_std'])
                else:
                    values.append(0)
                    errors.append(0)
            
            # Cria as barras SEM barras de erro primeiro
            bars = ax.bar(x + algo_idx * bar_width - (len(algorithms)-1) * bar_width/2, 
                          values, bar_width,
                          label=algorithm.replace('_', ' ').title(), 
                          color=colors(algo_idx), 
                          alpha=0.85,
                          edgecolor='black',
                          linewidth=1)
            bar_containers.append(bars)
            
            # Adiciona as barras de erro separadamente
            ax.errorbar(x + algo_idx * bar_width - (len(algorithms)-1) * bar_width/2,
                        values, yerr=errors,
                        fmt='none', ecolor='black', capsize=5, capthick=1.5, elinewidth=1.5)
        
        ax.set_xlabel('Topologia', fontsize=14)
        ax.set_ylabel('Taxa de Sucesso (%)', fontsize=14)
        ax.set_title(f'Comparação Direta para TTL={ttl_fixed}', fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([t.replace('_', ' ').title() for t in topologies], fontsize=12)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=len(algorithms), fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        ax.set_ylim(0, 110)
        
        # Agora bar_label() funciona porque bars é um BarContainer
        for bars in bar_containers:
            ax.bar_label(bars, fmt='%.1f%%', padding=3, fontsize=10, rotation=45)
        
        plt.tight_layout()
        plt.savefig('direct_comparison_ttl10.png', dpi=300, bbox_inches='tight')
        plt.close(fig) 
        # 6. Análise de Robustez: Desvio Padrão da Taxa de Sucesso (NOVO GRÁFICO)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True)
        fig.suptitle('Robustez: Desvio Padrão da Taxa de Sucesso', fontsize=18, fontweight='bold', y=0.98)
        
        for idx, topology in enumerate(topologies):
            ax = axes[idx // 2, idx % 2]
            
            for algo_idx, algorithm in enumerate(algorithms):
                std_devs = []
                for ttl in ttl_values:
                    std_devs.append(self.results[topology][algorithm][ttl]['success_rate_std'])
                
                ax.plot(ttl_values, std_devs,
                       marker=markers[algo_idx % len(markers)],
                       linestyle=line_styles[algo_idx % len(line_styles)],
                       color=colors(algo_idx),
                       linewidth=2.5,
                       markersize=9,
                       markerfacecolor='white',
                       markeredgewidth=2,
                       label=algorithm.replace('_', ' ').title(),
                       alpha=0.9)
            
            ax.set_title(f'Topologia: {topology.replace("_", " ").title()}', fontsize=14, fontweight='bold', pad=15)
            ax.set_ylabel('Desvio Padrão (%)', fontsize=12)
            ax.set_xlabel('TTL', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.7, which='both')
            ax.set_ylim(0, max(25, max(std_devs) * 1.2) if std_devs else 25)
        
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=len(algorithms),
                  bbox_to_anchor=(0.5, 0.96), fontsize=12, frameon=True, shadow=True)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig('robustness_analysis.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        print("\nGráficos melhorados salvos nos arquivos PNG:")
        print("- success_rate_comparison.png")
        print("- cost_benefit_analysis.png (novo)")
        print("- search_efficiency.png (novo)")
        print("- execution_time_analysis.png (novo)")
        print("- direct_comparison_ttl10.png")
        print("- robustness_analysis.png (novo)")

    def print_summary_statistics(self):
        """Imprime estatísticas resumidas dos resultados"""
        print("\n" + "="*80)
        print("RESUMO ESTATÍSTICO DOS TESTES")
        print("="*80)
        
        for topology in self.results:
            print(f"\nTopologia: {topology.upper()}")
            print("-" * 40)
            
            for algorithm in self.results[topology]:
                print(f"\n  Algoritmo: {algorithm}")
                
                # Para TTL=10 (valor comum)
                if 10 in self.results[topology][algorithm]:
                    stats = self.results[topology][algorithm][10]
                    print(f"    TTL=10:")
                    print(f"      Taxa de Sucesso: {stats['success_rate_mean']:.2f}%")
                    print(f"      Mensagens Médias: {stats['messages_mean']:.1f}")
                    print(f"      Nós Visitados: {stats['visited_mean']:.1f}")
                    print(f"      Tempo Execução: {stats['execution_time_mean']:.3f} ms")
                
                # Melhor TTL para este algoritmo (maior taxa de sucesso)
                best_ttl = None
                best_success = 0
                
                for ttl in self.results[topology][algorithm]:
                    success = self.results[topology][algorithm][ttl]['success_rate_mean']
                    if success > best_success:
                        best_success = success
                        best_ttl = ttl
                
                if best_ttl:
                    stats = self.results[topology][algorithm][best_ttl]
                    print(f"    Melhor TTL ({best_ttl}): {best_success:.2f}% sucesso")
                    print(f"      Custo: {stats['messages_mean']:.1f} mensagens")


def main():
    """Função principal para executar o benchmark"""
    
    # Configurações dos testes
    config_files = ["anel.json", "densa.json", "linha.json", "malha.json"]
    algorithms = ["flooding", "informed_flooding", "random_walk", "informed_random_walk"]
    ttl_values = [2, 4, 6, 8, 10, 12, 15, 20]
    num_tests = 50  # Número de testes por combinação (reduza para testes mais rápidos)
    
    print("="*80)
    print("BENCHMARK DE ALGORITMOS DE BUSCA P2P")
    print("="*80)
    print(f"Topologias: {', '.join(config_files)}")
    print(f"Algoritmos: {', '.join(algorithms)}")
    print(f"TTLs testados: {ttl_values}")
    print(f"Testes por combinação: {num_tests}")
    print(f"Total aproximado de execuções: {len(config_files) * len(algorithms) * len(ttl_values) * num_tests}")
    print("="*80)
    
    # Cria e executa o benchmark
    benchmark = P2PBenchmark()
    
    try:
        results = benchmark.run_benchmark(
            config_files=config_files,
            algorithms=algorithms,
            ttl_values=ttl_values,
            num_tests=num_tests
        )
        
        # Salva resultados
        benchmark.save_results()
        
        # Imprime estatísticas
        benchmark.print_summary_statistics()
        
        # Gera gráficos
        print("\nGerando gráficos...")
        benchmark.plot_comparative_results()
        
        print("\nBenchmark concluído com sucesso!")
        
    except FileNotFoundError as e:
        print(f"\nERRO: Arquivo de configuração não encontrado: {e}")
        print("Certifique-se de que os arquivos JSON estão no mesmo diretório:")
        print("  - anel.json")
        print("  - densa.json")
        print("  - linha.json")
        print("  - malha.json")
    except Exception as e:
        print(f"\nERRO durante a execução: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
