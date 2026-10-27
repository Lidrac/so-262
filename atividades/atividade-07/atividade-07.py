#!/usr/bin/env python3
"""
Simulador do Algoritmo do Banqueiro (Dijkstra)
Baseado nos conceitos do Capítulo 6 do livro "Sistemas Operacionais Modernos" (Tanenbaum & Bos).

O algoritmo gerencia a alocação de múltiplos tipos de recursos entre processos,
garantindo que o sistema permaneça sempre em um ESTADO SEGURO e evitando impasses (deadlocks).
"""

import copy

class BankersAlgorithm:
    def __init__(self, process_names, total_resources, allocation_matrix, max_matrix):
        """
        Inicializa o simulador.
        :param process_names: Lista de nomes dos processos [P0, P1, ...]
        :param total_resources: Vetor com a quantidade total de cada recurso [R0, R1, ...] (E)
        :param allocation_matrix: Matriz de alocação atual (C)
        :param max_matrix: Matriz de necessidade máxima declarada
        """
        self.process_names = process_names
        self.num_processes = len(process_names)
        self.num_resources = len(total_resources)
        self.total_resources = list(total_resources) # E (Existing)
        self.allocation = copy.deepcopy(allocation_matrix) # C (Current)
        self.max_matrix = copy.deepcopy(max_matrix)
        
        # Calcular matriz de Necessidade (Need = Max - Allocation)
        self.need = [
            [self.max_matrix[i][j] - self.allocation[i][j] for j in range(self.num_resources)]
            for i in range(self.num_processes)
        ]
        
        # Calcular vetor de Recursos Disponíveis (A = E - soma(C))
        self.available = list(self.total_resources)
        for j in range(self.num_resources):
            allocated_sum = sum(self.allocation[i][j] for i in range(self.num_processes))
            self.available[j] -= allocated_sum

    def display_state(self):
        """Exibe o estado atual do sistema de forma estruturada."""
        print("=" * 70)
        print("ESTADO ATUAL DO SISTEMA")
        print("=" * 70)
        print(f"Recursos Totais (E):     {self.total_resources}")
        print(f"Recursos Disponíveis (A): {self.available}")
        print("-" * 70)
        print(f"{'Processo':<10} | {'Alocado (C)':<15} | {'Máximo (Max)':<15} | {'Necessidade (Need)':<15}")
        print("-" * 70)
        for i in range(self.num_processes):
            p_name = self.process_names[i]
            alloc_str = str(self.allocation[i])
            max_str = str(self.max_matrix[i])
            need_str = str(self.need[i])
            print(f"{p_name:<10} | {alloc_str:<15} | {max_str:<15} | {need_str:<15}")
        print("=" * 70)

    def is_safe_state(self, verbose=True):
        """
        Verifica se o estado atual é SEGURO e determina uma sequência segura de execução.
        :param verbose: Imprime os passos da verificação
        :return: Tuple (is_safe: bool, safe_sequence: list)
        """
        work = list(self.available)
        finish = [False] * self.num_processes
        safe_sequence = []

        if verbose:
            print("\n[VERIFICAÇÃO DE ESTADO SEGURO]")
            print(f"Vetor de Trabalho Inicial (Work/Disponível): {work}\n")

        step = 1
        while len(safe_sequence) < self.num_processes:
            found_candidate = False
            for i in range(self.num_processes):
                if not finish[i]:
                    # Verificar se Need[i] <= Work
                    can_satisfy = all(self.need[i][j] <= work[j] for j in range(self.num_resources))
                    if can_satisfy:
                        if verbose:
                            print(f"Passo {step}: {self.process_names[i]} pode ser atendido!")
                            print(f"  Necessidade {self.need[i]} <= Disponível {work}")
                            print(f"  {self.process_names[i]} executa e libera seus recursos alocados: {self.allocation[i]}")
                        
                        # Processo executa e devolve seus recursos alocados
                        for j in range(self.num_resources):
                            work[j] += self.allocation[i][j]
                        
                        finish[i] = True
                        safe_sequence.append(self.process_names[i])
                        found_candidate = True
                        step += 1
                        
                        if verbose:
                            print(f"  Novo Vetor de Trabalho (Work): {work}\n")
                        break
            
            if not found_candidate:
                if verbose:
                    print("❌ ERRO: Nenhum processo pendente pode ser satisfeito com os recursos disponíveis.")
                    print("   O SISTEMA ENCONTRA-SE EM UM ESTADO INSEGURO!")
                return False, []

        if verbose:
            print("✅ SUCESSO: O sistema está em um ESTADO SEGURO!")
            print(f"   Sequência Segura de Execução: {' -> '.join(safe_sequence)}")
        return True, safe_sequence

    def request_resources(self, process_index, request_vector):
        """
        Trata uma requisição de recursos por um processo específico.
        :param process_index: Índice do processo (0, 1, ...)
        :param request_vector: Vetor de requisição [r0, r1, ...]
        :return: bool (Se a requisição foi concedida ou negada)
        """
        p_name = self.process_names[process_index]
        print("\n" + "#" * 70)
        print(f"SOLICITAÇÃO DE RECURSOS PELO PROCESSO {p_name}: {request_vector}")
        print("#" * 70)

        # Passo 1: Verificar se Requisição <= Necessidade (Need)
        for j in range(self.num_resources):
            if request_vector[j] > self.need[process_index][j]:
                print(f"❌ REQUISIÇÃO NEGADA: {p_name} solicitou mais do que sua necessidade máxima declarada.")
                print(f"   Solicitado: {request_vector[j]} > Necessidade {self.need[process_index][j]} para o recurso R{j}")
                return False

        # Passo 2: Verificar se Requisição <= Disponível (Available)
        for j in range(self.num_resources):
            if request_vector[j] > self.available[j]:
                print(f"⏳ PROCESSO BLOQUEADO: Recursos insuficientes disponíveis no momento.")
                print(f"   Solicitado: {request_vector[j]} > Disponível {self.available[j]} para o recurso R{j}")
                print(f"   {p_name} deve aguardar a liberação de recursos por outros processos.")
                return False

        # Passo 3: Tentativa de Alocação (Estado Provisório)
        print("⚠️ TENTATIVA PROVISÓRIA: Recursos disponíveis no momento. Testando alocação...")
        for j in range(self.num_resources):
            self.available[j] -= request_vector[j]
            self.allocation[process_index][j] += request_vector[j]
            self.need[process_index][j] -= request_vector[j]

        # Passo 4: Testar se o Estado Resultante é Seguro
        is_safe, sequence = self.is_safe_state(verbose=True)

        if is_safe:
            print(f"\n✅ REQUISIÇÃO CONCEDIDA A {p_name}!")
            print("   O estado resultante permanece SEGURO.")
            return True
        else:
            # Reverter alocação provisória (Rollback)
            print(f"\n❌ REQUISIÇÃO NEGADA A {p_name}!")
            print("   A alocação levaria a um ESTADO INSEGURO (risco de deadlock). Efetuando rollback...")
            for j in range(self.num_resources):
                self.available[j] += request_vector[j]
                self.allocation[process_index][j] -= request_vector[j]
                self.need[process_index][j] += request_vector[j]
            print("   Estado original restaurado. O processo deve aguardar.")
            return False


def run_demo():
    print("======================================================================")
    print("     SIMULAÇÃO DO ALGORITMO DO BANQUEIRO (TANENBAUM & BOS - CAP 6)    ")
    print("======================================================================")
    
    # Exemplo clássico com 5 processos (P0, P1, P2, P3, P4) e 3 tipos de recursos (R0, R1, R2)
    # Recursos Totais do Sistema: E = [10, 5, 7]
    process_names = ["P0", "P1", "P2", "P3", "P4"]
    total_resources = [10, 5, 7]
    
    # Matriz de Alocação Atual (C)
    allocation = [
        [0, 1, 0],  # P0
        [2, 0, 0],  # P1
        [3, 0, 2],  # P2
        [2, 1, 1],  # P3
        [0, 0, 2]   # P4
    ]
    
    # Matriz de Necessidade Máxima (Max)
    max_matrix = [
        [7, 5, 3],  # P0
        [3, 2, 2],  # P1
        [9, 0, 2],  # P2
        [2, 2, 2],  # P3
        [4, 3, 3]   # P4
    ]

    # Criar instância do simulador
    banker = BankersAlgorithm(process_names, total_resources, allocation, max_matrix)
    
    # 1. Exibir estado inicial
    banker.display_state()
    
    # 2. Testar se o estado inicial é seguro
    is_safe, sequence = banker.is_safe_state(verbose=True)
    
    # 3. Teste de Caso 1: Requisição VÁLIDA e SEGURA feita pelo processo P1
    # P1 solicita [1, 0, 2]
    banker.request_resources(process_index=1, request_vector=[1, 0, 2])
    banker.display_state()

    # 4. Teste de Caso 2: Requisição INSEGURA feita pelo processo P4
    # P4 solicita [3, 3, 0] (Excede disponível ou gera estado inseguro)
    banker.request_resources(process_index=4, request_vector=[3, 3, 0])
    banker.display_state()

if __name__ == "__main__":
    run_demo()