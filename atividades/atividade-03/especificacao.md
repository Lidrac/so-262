# Especificação do Gerenciador de Processos

## 1. Visão Geral e Arquitetura do Simulador

### 1.1 CPU Virtual

- **Definição:** Uma abstração em software de uma CPU real com ULA, registradores, etc., simulando seu contexto de execução (guarda o contexto do processo atual).
- É responsável por lidar com o estado do processo atual (ocioso ou ocupado) e permitir a troca de contexto.
- **Contexto:** É o conjunto de informações e dados no estado atual de um programa em execução (permite retomar um programa no exato ponto que parou).

**Variáveis que compõem a CPU virtual:**

- `PC` (Program Counter)
- `estado_atual`
- `registradores`

**Operações da CPU virtual:**

- Copiar os valores atuais de `pc` e `registradores` da CPU virtual para o PCB do processo que está saindo da CPU.
- Copiar as informações e os dados do PCB do novo processo para a CPU virtual.
- Incrementar o `PC` para avançar para a próxima instrução no processo atual.

---

### 1.2 Relógio Lógico

- **Definição:** Contador global de tempo discreto que diz quando um processo vai para o estado de pronto e quando um processo bloqueado pode voltar para o estado de pronto.
- Ou seja, é responsável por sincronizar eventos de preempção (interrupção de um processo pelo Quantum) e desbloqueio de operações de E/S.

**Variáveis que compõem o Relógio:**

- `tempo_decorrido`
- `fatia_tempo` (quantum)

**Operações do Relógio:**

- A cada ciclo de instrução processado é incrementado +1 ao tempo decorrido.
- Se `tempo_decorrido` atinge a `fatia_tempo`, o relógio emite um sinal que interrompe para que seja avaliada a preempção. Caso tenha uma tarefa de maior prioridade, a tarefa de menor prioridade é pausada e o seu contexto é salvo. _(Nota: Esta avaliação de prioridade dependerá do algoritmo em uso)._
- A cada incremento de `tempo_decorrido`, o sistema vai compará-lo com o instante de término de E/S dos processos que estão bloqueados para mudar seu estado para pronto quando o tempo decorrido atingir o instante de término.

---

### 1.3 Ciclo da Simulação

A cada passo da simulação, o sistema realiza as seguintes ações em sequência:

1. A CPU executa a instrução que o `pc` indicou.
2. O Relógio é incrementado +1 (`tempo_decorrido`).
3. Verifica se algum processo bloqueado concluiu sua E/S no momento atual. Caso sim, muda seu estado para pronto.
4. Verifica se o `tempo_decorrido` atingiu `fatia_tempo` (quantum) no processo atual. Caso sim:
   - Salva o contexto da CPU virtual para o PCB.
   - Altera o estado do processo atual para pronto.
   - Chama o próximo processo da fila.
   - Copia o contexto do PCB para a CPU virtual.

---

## 2. Especificação do Bloco de Controle de Processo (PCB)

| Campo do PCB         | Tipo de Dado      | Descrição do Atributo                                                                            |
| :------------------- | :---------------- | :----------------------------------------------------------------------------------------------- |
| **PID**              | Inteiro           | Identificador único gerado na criação de um processo.                                            |
| **Estado Atual**     | Enum/Inteiro      | O momento atual do processo no ciclo de vida (Pronto, Em Execução ou Bloqueado).                 |
| **PC**               | Inteiro           | Indica qual é a próxima instrução (ou linha do arquivo de tarefas) que o processo deve executar. |
| **Registradores**    | Array de Inteiros | Espaço para salvar o valor dos registradores da CPU Virtual quando o processo sofre preempção.   |
| **Prioridade**       | Inteiro           | Nível de prioridade do processo (necessário para o algoritmo de Escalonamento por Prioridade).   |
| **Tempo de Chegada** | Inteiro (Tiques)  | Instante exato do Relógio Lógico em que o processo foi submetido ao sistema.                     |
| **Tempo de CPU**     | Inteiro (Tiques)  | Acumulador de quanto tempo o processo já rodou na CPU (útil para estatísticas finais).           |
| **Tempo de Espera**  | Inteiro (Tiques)  | Acumulador de quanto tempo o processo passou na fila de "Prontos" esperando sua vez.             |
| **Tempo de E/S**     | Inteiro (Tiques)  | Instante no Relógio Lógico em que a operação de bloqueio (I/O) será concluída.                   |

---

# 3. Especificação do Ciclo de Vida e Máquina de Estados

O motor de estados do nosso simulador foi arquitetado com base no modelo de processos sequenciais descrito no Capítulo 2 do livro _Sistemas Operacionais Modernos_ (Tanenbaum & Bos). Para garantir a coerência da simulação da CPU virtual, estabelecemos que cada processo (representado por seu PCB) existirá em um único estado lógico por vez, sendo o chaveamento controlado por interrupções e _syscalls_ simuladas.

---

## 3.1 Definição Arquitetural dos Estados

- **Executando (Running):** O processo possui o domínio da CPU virtual. Suas instruções estão sendo processadas e os registradores de hardware simulados (como o _Program Counter_ - PC e o _Stack Pointer_ - SP) refletem seu contexto atual.
- **Pronto (Ready):** O processo tem todos os recursos em memória e está apto para executar, mas sofreu preempção ou acabou de ser criado. Ele aguarda na _Ready Queue_ (Fila de Prontos) até que o escalonador realize o despacho.
- **Bloqueado (Blocked):** O processo executou uma chamada bloqueante e não pode avançar, mesmo que a CPU esteja ociosa. Ele permanece na fila de espera do dispositivo até que o tratador de interrupções de Entrada/Saída sinalize a conclusão do evento.
- **Finalizado (Terminated):** Estado de _zombie_ ou término. O processo encerrou a execução, liberou a CPU, e o sistema está coletando suas métricas (tempo de _turnaround_, espera) antes de desalocar o PCB.

---

## 3.2 Grafo de Transição de Estados

A máquina de estados finitos que rege o ciclo de vida e a movimentação dos ponteiros de PCB entre as filas do sistema é modelada pelo diagrama abaixo:

```text
         [ Syscall: fork() / CreateProcess() ]
                      │
                      │ (0) Criação
                      ▼
               ┌─────────────┐
        ┌─────▶│   PRONTO    │◀──────────────────┐
        │      └─────────────┘                   │
        │             │                          │
        │             │ (3) Despacho /           │
  (2) Preempção       │     Context Switch       │ (4) Interrupção
  (Timer / Quantum)   ▼                          │     de E/S
               ┌─────────────┐                   │
        └──────│ EM EXECUÇÃO │                   │
               └─────────────┘                   │
                 │         │                     │
                 │         └──(5) Syscall:       │
  (1) Syscall    │                 exit()        │
  Bloqueante     ▼                     │         │
    de E/S┌─────────────┐              ▼         │
          │  BLOQUEADO  │        ┌───────────┐   │
          └─────────────┘        │TERMINATED │   │
                 │               └───────────┘   │
                 └───────────────────────────────┘
```

---

## 3.3 Disparadores de Eventos e Regras de Transição

O _core_ do nosso simulador processa as mudanças de estado sob regras estritas de hardware/software simulado:

### Transição 0: Instanciação do Processo (`fork`)

- **Fluxo:** `[Novo]` $\rightarrow$ `PRONTO`
- **Mecanismo:** Simulamos a chamada de criação. O sistema operacional aloca memória para o Bloco de Controle de Processo (PCB), atribui um `PID` exclusivo, inicializa o _Program Counter_ em 0 e insere o ponteiro deste PCB no final da _Ready Queue_.

### Transição 1: Requisição de I/O (Chamada Bloqueante)

- **Fluxo:** `EM EXECUÇÃO` $\rightarrow$ `BLOQUEADO`
- **Mecanismo:** O processo em execução atinge uma instrução de I/O. Ocorre um _context switch_ de saída: a CPU virtual salva os registradores no PCB, muda a flag de estado para `BLOQUEADO`, insere o processo na fila do respectivo dispositivo e aciona o escalonador.

### Transição 2: Preempção por Relógio (Fim do _Quantum_)

- **Fluxo:** `EM EXECUÇÃO` $\rightarrow$ `PRONTO`
- **Mecanismo:** O _timer_ de hardware simulado dispara uma interrupção indicando que a fatia de tempo daquele processo esgotou. Para evitar monopólio da CPU, o sistema salva o contexto no PCB, altera o estado para `PRONTO` e o realoca na _Ready Queue_ para disputar a CPU novamente.

### Transição 3: Despacho (_Dispatcher_)

- **Fluxo:** `PRONTO` $\rightarrow$ `EM EXECUÇÃO`
- **Mecanismo:** A CPU está livre. O algoritmo do escalonador seleciona o melhor candidato na fila de prontos, executa a restauração de contexto (carregando os dados do PCB de volta para os registradores da CPU) e retoma a execução a partir do _Program Counter_ salvo.

### Transição 4: Conclusão de I/O (Tratador de Interrupção)

- **Fluxo:** `BLOQUEADO` $\rightarrow$ `PRONTO`
- **Mecanismo:** O ciclo de relógio correspondente ao fim da operação de E/S é atingido. Uma interrupção de dispositivo é gerada. O SO remove o processo da fila de bloqueados e o reinsere na fila de prontos, deixando-o elegível para o próximo escalonamento.

### Transição 5: Finalização (`exit`)

- **Fluxo:** `EM EXECUÇÃO` $\rightarrow$ `TERMINATED`
- **Mecanismo:** O processo conclui seu último _burst_ de CPU. A rotina de finalização computa as métricas de desempenho (uso de CPU, _Turnaround_), limpa o espaço de endereçamento simulado e destrói o PCB, liberando o sistema para despachar o próximo da fila.

---

## 3.4 API de Telemetria: Formato de Logs de Transição

Para fins de _debugging_, auditoria computacional e geração posterior do Gráfico de Gantt, o motor do simulador emitirá logs na saída padrão (`stdout`) sempre que um PCB sofrer alteração de estado. A telemetria seguirá um padrão de _string_ fixo:

```text
[TICK: <clock_atual>] PID=<pid> | <ESTADO_ANTERIOR> -> <ESTADO_NOVO> | EVENTO: <trigger>
```

**Exemplo de saída do simulador:**

```text
[TICK: 0012] PID=1 | PRONTO -> EM_EXECUCAO | EVENTO: DESPACHO
[TICK: 0016] PID=1 | EM_EXECUCAO -> BLOQUEADO | EVENTO: SYSCALL_IO (BURST=4)
[TICK: 0020] PID=1 | BLOQUEADO -> PRONTO | EVENTO: IO_CONCLUIDO
[TICK: 0024] PID=1 | EM_EXECUCAO -> TERMINATED | EVENTO: SYSCALL_EXIT
```

# 4. Especificação do Escalonador de CPU

---

## 4.1 Objetivo do Escalonador

Como o simulador possui uma única CPU virtual, somente um processo poderá estar no estado EXECUTANDO em cada instante. Quando houver mais de um processo no estado PRONTO, será necessário determinar qual deles deverá utilizar a CPU.

O escalonador será responsável por realizar essa seleção de acordo com o algoritmo de escalonamento configurado para a simulação.

O simulador deverá implementar dois algoritmos de escalonamento:

Round Robin (RR);
Prioridade com aging (PRIORIDADE).
Os algoritmos deverão ser selecionáveis por meio do arquivo de entrada, permitindo executar o mesmo conjunto de processos utilizando políticas de escalonamento diferentes.

Como o simulador busca representar características de sistemas interativos, os algoritmos deverão considerar principalmente:

tempo de resposta;
distribuição do tempo de CPU;
justiça entre processos;
prevenção de starvation;
quantidade de preempções;
quantidade de trocas de contexto.
A unidade de tempo utilizada será denominada Unidade de Tempo (UT) e deverá ser mantida de forma consistente em toda a simulação.

---

## 4.2 Algoritmo Round Robin

O algoritmo Round Robin (RR) será baseado em uma fila circular de processos no estado PRONTO.

Todos os processos serão considerados de importância equivalente para fins de escalonamento. Cada processo poderá utilizar a CPU durante um intervalo máximo denominado quantum.

O quantum deverá ser definido no arquivo de entrada e deverá possuir valor inteiro positivo.

O funcionamento do algoritmo será:

O escalonador seleciona o primeiro processo disponível na fila de PRONTO.
O processo passa para o estado EXECUTANDO.
O processo utiliza a CPU durante, no máximo, um quantum.
Se o processo terminar seu surto de CPU antes do término do quantum, a CPU será liberada.
Se o processo solicitar uma operação de E/S, ele passará para BLOQUEADO.
Se o quantum terminar enquanto o processo ainda possuir trabalho de CPU, ocorrerá uma preempção.
Após a preempção, o processo retornará ao estado PRONTO e será colocado no final da fila.
O escalonador selecionará o próximo processo disponível.
Portanto, no Round Robin, a fila de processos prontos será tratada de forma circular:

P1 -> P2 -> P3 -> P4 -> P1 -> ...

Um processo que sofrer preempção não retornará imediatamente para o início da fila. Ele será inserido no final da fila para garantir a distribuição do tempo de CPU.

---

## 4.2.1 Quantum

O quantum representa o tempo máximo consecutivo que um processo poderá utilizar a CPU antes de ser preemptado.

Um quantum muito pequeno poderá aumentar a quantidade de trocas de contexto, enquanto um quantum muito grande poderá aumentar o tempo de resposta dos demais processos.

O simulador deverá utilizar um único valor de quantum definido para cada execução.

Por exemplo:

QUANTUM 10

significa que um processo poderá executar por, no máximo, 10 UT antes que o escalonador avalie uma possível preempção por expiração do quantum.

---

## 4.3 Exemplo de Round Robin

Considere:

Quantum: 35 UT

P1 = 45 UT de CPU
P2 = 30 UT de CPU
P3 = 80 UT de CPU
P4 = 15 UT de CPU
P5 = 50 UT de CPU

Com a fila inicial:

P1 -> P2 -> P3 -> P4 -> P5

e sem operações de E/S, a execução será:

tempo 0 - 35: P1
tempo 35 - 65: P2
tempo 65 - 100: P3
tempo 100 - 115: P4
tempo 115 - 150: P5
tempo 150 - 160: P1
tempo 160 - 195: P3
tempo 195 - 210: P5
tempo 210 - 220: P3

P1, P3 e P5 são preemptados quando atingem o limite de seus respectivos quanta. P2 e P4 terminam antes do término do quantum.

A sequência demonstra que o Round Robin permite que os processos tenham oportunidades periódicas de utilização da CPU.

---

## 4.4 Algoritmo de Prioridade

No algoritmo de prioridade, cada processo possuirá uma prioridade inicial e uma prioridade atual.

Será utilizada a seguinte convenção:

Quanto menor o valor numérico da prioridade, maior será a prioridade do processo.

Assim:

Prioridade 1 > Prioridade 2 > Prioridade 3 > Prioridade 4

Por exemplo, um processo com prioridade 1 terá preferência sobre um processo com prioridade 3.

Quando a CPU estiver disponível, o escalonador deverá selecionar o processo no estado PRONTO que possuir a menor prioridade numérica.

Caso um processo de prioridade superior entre no estado PRONTO enquanto outro processo estiver executando, poderá ocorrer preempção.

A preempção por prioridade ocorrerá somente quando:

prioridade_do_novo_processo < prioridade_do_processo_atual

Se as prioridades forem iguais, não haverá preempção automática somente pela igualdade. Nesse caso, o desempate será realizado pelo mecanismo de Round Robin.

---

## 4.5 Quantum no Escalonamento por Prioridade

Embora a seleção dos processos seja determinada principalmente pela prioridade, o algoritmo PRIORIDADE também utilizará o quantum configurado.

O quantum será utilizado para limitar o tempo consecutivo de execução de um processo. Quando o quantum expirar, o processo em EXECUTANDO será preemptado e retornará ao estado PRONTO, sendo posteriormente considerado novamente pelo escalonador.

Após a preempção, o escalonador deverá selecionar o processo PRONTO de maior prioridade, ou seja, aquele que possuir o menor valor numérico de prioridade.

Caso o processo que sofreu a preempção continue sendo o processo de maior prioridade, ele poderá ser selecionado novamente imediatamente.

Quando dois ou mais processos possuírem a mesma prioridade, o desempate será realizado utilizando a ordem do Round Robin. Nesse caso, os processos de mesma prioridade compartilharão a CPU de acordo com o quantum.

Dessa forma:

- a prioridade determina qual processo ou grupo de processos possui preferência;
- o quantum determina o tempo máximo consecutivo de execução;
- processos com a mesma prioridade utilizam Round Robin para desempate;
- a expiração do quantum provoca preempção;
- um processo de prioridade superior poderá provocar preempção do processo atual.

Por exemplo:

P1 -> prioridade 2  
P2 -> prioridade 2  
P3 -> prioridade 4

Enquanto P1 e P2 permanecerem com prioridade 2, eles deverão alternar a utilização da CPU por meio do Round Robin. P3 somente deverá receber a CPU quando não houver processos de prioridade efetivamente superior disponíveis.

---

## 4.6 Prevenção de Starvation por Aging

O starvation ocorre quando um processo permanece por tempo excessivo no estado PRONTO porque outros processos possuem prioridade superior e continuam recebendo a CPU.

Para reduzir esse problema, será utilizado um mecanismo de aging.

O aging será aplicado aos processos que permanecerem no estado PRONTO.

A cada avanço de 1 Unidade de Tempo (UT) do relógio lógico, os processos que estiverem no estado PRONTO terão seu valor numérico de prioridade reduzido em uma unidade, respeitando o limite mínimo de 1.

O aging deverá ser aplicado antes da próxima decisão do escalonador. Dessa forma, as prioridades atualizadas serão utilizadas na seleção do próximo processo.

A regra será:

prioridade_atual = max(1, prioridade_atual - 1)

Por exemplo, um processo inicialmente com prioridade 5 poderá evoluir da seguinte forma:

Inicial: 5
Após 1 tick: 4
Após 2 ticks: 3
Após 3 ticks: 2
Após 4 ticks: 1
Após 5 ticks: 1

A prioridade nunca poderá assumir valor inferior a 1.

O aging será aplicado somente a processos que estiverem no estado PRONTO.

Portanto:

processos PRONTO recebem aging;
processos EXECUTANDO não recebem aging;
processos BLOQUEADO não recebem aging;
processos TERMINADO não recebem aging.
A prioridade atual deverá ser armazenada no PCB para que o escalonador possa utilizá-la nas decisões seguintes.

---

## 4.7 Preempção

O simulador deverá distinguir preempção de término ou bloqueio voluntário.

Uma preempção ocorrerá quando um processo for retirado da CPU pelo escalonador antes de concluir sua execução.

Serão consideradas situações de preempção:

expiração do quantum no Round Robin;
expiração do quantum entre processos de mesma prioridade;
chegada de um processo de prioridade superior ao processo atual.

Não serão consideradas preempções:

término do processo;
solicitação de E/S;
CPU entrando em estado IDLE.
Toda preempção deverá ser registrada no log de execução e contabilizada nas estatísticas.

---

## 4.8 Trocas de Contexto

Uma troca de contexto ocorrerá quando um processo deixar de utilizar a CPU e outro processo passar a utilizá-la.

As principais situações que poderão provocar troca de contexto são:

preempção;
bloqueio por E/S;
término do processo.

A passagem entre IDLE e um processo não será contabilizada como troca de contexto.

O número de trocas de contexto deverá ser compatível com os eventos registrados no log e no gráfico de Gantt.

---

## 4.9 Ordem de Processamento de Eventos

Para garantir que a execução seja determinística, quando dois ou mais eventos ocorrerem no mesmo instante do relógio lógico, o simulador deverá processá-los em uma ordem definida.

A ordem adotada será:

1. conclusão das operações de E/S;
2. transição dos processos liberados para o estado PRONTO;
3. aplicação do aging aos processos que estiverem no estado PRONTO;
4. tratamento da conclusão, bloqueio ou término do processo que estava utilizando a CPU;
5. tratamento da expiração do quantum;
6. verificação de preempção por prioridade;
7. realização do despacho do próximo processo.

A ordem acima deverá ser utilizada de forma consistente durante toda a simulação.

Quando houver mais de um processo elegível para o despacho, serão aplicadas as regras do algoritmo de escalonamento correspondente.

---

# 5. Entrada, Casos de Teste e Saídas

Esta seção define a interface entre o arquivo de entrada e o simulador, além dos formatos mínimos esperados para a saída da execução.

O objetivo é permitir que diferentes conjuntos de processos sejam executados de maneira padronizada e que os resultados possam ser verificados por meio do log, do gráfico de Gantt e das estatísticas.

---

## 5.1 Formato do Arquivo de Entrada

O simulador deverá receber um arquivo de texto contendo a configuração da simulação e a descrição dos processos.

O formato geral será:

ALGORITMO <algoritmo>
QUANTUM <valor>

PROCESSO <PID> <PRIORIDADE> <OPERACAO> <OPERACAO> ...

O campo <algoritmo> deverá possuir um dos seguintes valores:

RR
PRIORIDADE

O campo <valor> do comando QUANTUM deverá ser um número inteiro positivo.

Cada processo deverá possuir:

um PID único;
uma prioridade inicial inteira positiva;
pelo menos uma operação CPU(n).
Os processos declarados no início do arquivo serão considerados processos iniciais e chegarão ao sistema no instante 0.

A ordem em que os processos aparecem no arquivo será utilizada como ordem de inserção na fila inicial de PRONTO quando o algoritmo exigir um desempate por ordem de chegada.

---

## 5.2 Regras de Validação da Entrada

O arquivo de entrada deverá obedecer às seguintes regras:

O PID de cada processo deverá ser único.
A prioridade deverá ser um número inteiro positivo.
O quantum deverá ser um número inteiro positivo.
Os valores de CPU(n) deverão ser inteiros positivos.
Os valores de IO(n) deverão ser inteiros positivos.
Cada processo deverá possuir pelo menos uma operação CPU(n).
As operações deverão ser executadas na ordem em que aparecem.
EXIT, quando utilizado, deverá ser a última operação.
Linhas vazias deverão ser ignoradas.
Linhas iniciadas por # deverão ser consideradas comentários.
Comandos desconhecidos deverão gerar erro.
Valores inválidos deverão gerar erro.
PIDs duplicados deverão gerar erro.
O simulador deverá informar a linha em que ocorreu o erro.
Essas regras têm como objetivo impedir que entradas inválidas provoquem comportamentos indefinidos durante a simulação.

---

## 5.3 Operações dos Processos

As operações disponíveis para os processos serão:

CPU(n);
IO(n);
EXIT;
FORK(PID).

---

### 5.3.1 Operação CPU

A operação:

CPU(n)

representa um surto de utilização da CPU de duração n.

Exemplo:

CPU(20)

representa uma necessidade de 20 UT de CPU.

Caso o processo seja preemptado antes de concluir o surto, o tempo restante deverá ser preservado para execução posterior.

Por exemplo, se um processo estiver executando CPU(20) e sofrer preempção após 7 UT, deverão permanecer 13 UT para serem executadas posteriormente.

---

### 5.3.2 Operação IO

A operação:

IO(n)

representa uma solicitação fictícia de Entrada/Saída.

Ao atingir essa operação, o processo deverá realizar a transição:

EXECUTANDO -> BLOQUEADO

O processo permanecerá bloqueado durante n UT.

Durante esse período, ele:

não poderá utilizar a CPU;
não participará da fila de PRONTO;
não receberá aging.
Após a conclusão da E/S, ocorrerá:

BLOQUEADO -> PRONTO

O processo será novamente disponibilizado ao escalonador.

Exemplo:

PROCESSO P1 3 CPU(10) IO(5) CPU(15) EXIT

O processo P1 executará 10 UT de CPU, permanecerá bloqueado por 5 UT e posteriormente retornará ao estado PRONTO para executar mais 15 UT de CPU.

---

### 5.3.3 Operação EXIT

A operação:

EXIT

representará o término explícito do processo.

Ao executar EXIT, o processo deverá realizar:

EXECUTANDO -> TERMINADO

O processo não poderá retornar ao estado PRONTO.

Caso o processo conclua todas as operações sem utilizar EXIT, ele também deverá ser considerado terminado.

---

### 5.3.4 Operação FORK

A operação:

FORK(PID)

representará a criação dinâmica de um processo.

O processo indicado pelo PID deverá estar previamente declarado no arquivo de entrada.

Quando o FORK for executado:

o processo filho será criado;
será criado um PCB próprio para o filho;
o filho receberá o PID definido na declaração;
sua prioridade inicial será aquela definida na declaração do processo;
seu instante de chegada será o instante em que o FORK ocorreu;
o processo filho será colocado no estado PRONTO.
O processo criado poderá provocar preempção do processo atual caso o algoritmo utilizado seja PRIORIDADE e a prioridade do novo processo seja superior.

Um processo deverá ser criado no máximo uma vez.

---

## 5.4 Exemplo de Arquivo de Entrada

Um exemplo utilizando Round Robin será:

Configuração:

ALGORITMO RR
QUANTUM 10

PID PRIORIDADE OPERACOES:

PROCESSO P1 3 CPU(25) IO(10) CPU(15) EXIT
PROCESSO P2 1 CPU(15) IO(5) CPU(20) EXIT
PROCESSO P3 5 CPU(30) EXIT

Nesse exemplo:

P1, P2 e P3 chegam no instante 0;
o quantum é 10 UT;
P1 possui prioridade inicial 3;
P2 possui prioridade inicial 1;
P3 possui prioridade inicial 5.
O mesmo conjunto poderá ser executado pelo algoritmo de prioridade:

ALGORITMO PRIORIDADE
QUANTUM 10

PROCESSO P1 3 CPU(25) IO(10) CPU(15) EXIT
PROCESSO P2 1 CPU(15) IO(5) CPU(20) EXIT
PROCESSO P3 5 CPU(30) EXIT

Nesse segundo caso, a escolha da CPU será baseada na prioridade atual dos processos e no mecanismo de aging.

---

## 5.5 Formato da Saída

Ao término da simulação, o programa deverá apresentar, no mínimo:

log de transições;
gráfico de Gantt;
estatísticas individuais;
estatísticas globais.
Todas as informações deverão utilizar a mesma unidade de tempo.

---

### 5.5.1 Log de Transições

O log deverá registrar as principais transições realizadas pelos processos.

Cada registro deverá conter:

instante;
PID;
estado anterior;
novo estado;
motivo da transição.
Exemplo:

[00] P1: PRONTO -> EXECUTANDO | despacho
[10] P1: EXECUTANDO -> PRONTO | quantum expirado
[10] P2: PRONTO -> EXECUTANDO | despacho
[15] P2: EXECUTANDO -> BLOQUEADO | solicitacao de E/S
[15] P3: PRONTO -> EXECUTANDO | despacho
[20] P2: BLOQUEADO -> PRONTO | E/S concluida

Os motivos deverão identificar, quando aplicável:

criação;
despacho;
quantum expirado;
preempção por prioridade;
solicitação de E/S;
conclusão de E/S;
término.
Quando ocorrer preempção por prioridade, o log deverá identificar o processo que provocou a preempção.

---

### 5.5.2 Gráfico de Gantt

O gráfico de Gantt deverá representar a utilização da CPU em intervalos.

O formato recomendado será:

inicio,fim PID

Por exemplo:

0,10 P1
10,20 P2
20,30 P3
30,40 P1

O intervalo a,b representa a utilização da CPU desde a, inclusive, até b, exclusive.

Intervalos consecutivos pertencentes ao mesmo processo deverão ser consolidados em um único intervalo quando não houver troca de contexto entre eles.

Quando nenhum processo estiver disponível, deverá ser utilizado:

IDLE

Exemplo:

0,5 P1
5,20 IDLE
20,25 P1

O intervalo IDLE deverá ser contabilizado como tempo de CPU ociosa.

---

### 5.5.3 Estatísticas por Processo

Para cada processo, o simulador deverá apresentar:

PID;
prioridade inicial;
prioridade final;
instante de chegada;
instante de término;
tempo total de CPU;
tempo total em PRONTO;
tempo total em BLOQUEADO;
tempo de turnaround;
tempo de resposta;
número de preempções;
número de operações de E/S.

O turnaround será calculado por:

Turnaround = instante_de_termino - instante_de_chegada

O tempo de resposta será:

Tempo_de_resposta =
primeiro_instante_de_execucao - instante_de_chegada

O tempo de espera será o tempo total acumulado no estado PRONTO.

O período em BLOQUEADO não deverá ser contabilizado como tempo de espera.

---

### 5.5.4 Estatísticas Globais

O simulador deverá apresentar:

tempo total da simulação;
tempo total de CPU ocupada;
tempo total de CPU ociosa;
percentual de utilização da CPU;
número total de trocas de contexto;
número total de preempções;
tempo médio de espera;
tempo médio de turnaround;
tempo médio de resposta.
A utilização da CPU será calculada por:

Utilização =
(CPU ocupada / tempo total da simulação) × 100

Também deverá ser válida a relação:

Tempo total da simulação =
CPU ocupada + CPU ociosa

As médias deverão ser calculadas considerando todos os processos terminados na simulação.

---

### 5.5.5 Exemplo de Saída

Um exemplo de saída poderá ser:

===== LOG DE TRANSICOES =====

[00] P1: PRONTO -> EXECUTANDO | despacho
[10] P1: EXECUTANDO -> PRONTO | quantum expirado
[10] P2: PRONTO -> EXECUTANDO | despacho
[15] P2: EXECUTANDO -> BLOQUEADO | solicitacao de E/S
[15] P3: PRONTO -> EXECUTANDO | despacho
...

===== GRAFICO DE GANTT =====

0,10 P1
10,15 P2
15,25 P3
25,35 P1
35,40 IDLE
...

===== ESTATISTICAS =====

Tempo total da simulacao: 100 UT
CPU ocupada: 92 UT
CPU ociosa: 8 UT
Utilizacao da CPU: 92.00%

Trocas de contexto: 12
Preempcoes: 9

PID PRI_INICIAL PRI_FINAL CPU ESPERA BLOQUEADO TURNAROUND RESPOSTA PREEMP IO
P1 3 1 40 25 10 70 0 4 1
P2 1 1 30 15 5 50 10 3 1
P3 5 2 22 20 0 60 20 2 0

Tempo medio de espera: 20.00 UT
Tempo medio de turnaround: 60.00 UT
Tempo medio de resposta: 10.00 UT

Os valores apresentados são apenas ilustrativos e não representam necessariamente os resultados de um caso de teste específico.

---

## 5.6 Casos de Teste

Os casos de teste deverão verificar individualmente os mecanismos fundamentais do simulador.

Cada caso deverá possuir uma entrada definida e um comportamento esperado que permita identificar possíveis erros na implementação.

---

### 5.6.1 Caso 1 — Round Robin Básico

Objetivo: verificar a distribuição circular da CPU e a preempção por expiração do quantum.

ALGORITMO RR
QUANTUM 10

PROCESSO P1 1 CPU(25) EXIT
PROCESSO P2 1 CPU(15) EXIT
PROCESSO P3 1 CPU(20) EXIT

Deverá ser verificado:

funcionamento da fila circular;
respeito ao quantum;
preempção;
reinserção no final da fila;
término dos processos.

---

### 5.6.2 Caso 2 — Término Antes do Quantum

Objetivo: verificar se um processo que termina antes do quantum não é contabilizado como preemptado.

ALGORITMO RR
QUANTUM 10

PROCESSO P1 1 CPU(5) EXIT
PROCESSO P2 1 CPU(20) EXIT

P1 deverá executar por 5 UT e terminar.

A saída de P1 da CPU deverá ser registrada como término, e não como preempção.

---

### 5.6.3 Caso 3 — E/S

Objetivo: verificar as transições entre EXECUTANDO, BLOQUEADO e PRONTO.

ALGORITMO RR
QUANTUM 10

PROCESSO P1 1 CPU(5) IO(10) CPU(5) EXIT
PROCESSO P2 2 CPU(20) EXIT

Deverão ser registradas:

EXECUTANDO -> BLOQUEADO
BLOQUEADO -> PRONTO

Enquanto estiver bloqueado, P1 não poderá utilizar a CPU.

---

### 5.6.4 Caso 4 — Prioridades Diferentes

Objetivo: verificar a seleção baseada na prioridade.

ALGORITMO PRIORIDADE
QUANTUM 10

PROCESSO P1 3 CPU(20) EXIT
PROCESSO P2 1 CPU(10) EXIT
PROCESSO P3 5 CPU(10) EXIT

P2 possui a maior prioridade inicial porque 1 é o menor valor numérico.

---

### 5.6.5 Caso 5 — Preempção por Prioridade

Objetivo: verificar a preempção quando um processo de prioridade superior retorna ao estado PRONTO.

ALGORITMO PRIORIDADE
QUANTUM 10

PROCESSO P1 5 CPU(30) EXIT
PROCESSO P2 1 CPU(5) IO(5) CPU(10) EXIT

Quando P2 concluir a E/S e retornar ao estado PRONTO, sua prioridade deverá ser comparada com a prioridade do processo atualmente em execução.

Caso P1 esteja executando, P2 deverá provocar preempção por possuir prioridade superior.

---

### 5.6.6 Caso 6 — Aging

Objetivo: verificar a prevenção de starvation.

ALGORITMO PRIORIDADE
QUANTUM 10

PROCESSO P1 1 CPU(50) EXIT
PROCESSO P2 5 CPU(10) EXIT
PROCESSO P3 5 CPU(10) EXIT

P2 e P3 deverão sofrer aging enquanto permanecerem no estado PRONTO.

O teste deverá verificar que:

a prioridade diminui gradualmente;
o valor mínimo é 1;
processos em PRONTO recebem aging;
processos em EXECUTANDO não recebem aging;
processos em BLOQUEADO não recebem aging;
processos de baixa prioridade conseguem eventualmente receber CPU.

---

### 5.6.7 Caso 7 — Desempate por Round Robin

Objetivo: verificar o desempate entre processos com a mesma prioridade.

ALGORITMO PRIORIDADE
QUANTUM 10

PROCESSO P1 2 CPU(25) EXIT
PROCESSO P2 2 CPU(25) EXIT
PROCESSO P3 5 CPU(10) EXIT

P1 e P2 possuem a mesma prioridade.

O escalonador deverá utilizar Round Robin para alternar a CPU entre processos que estejam no mesmo nível de prioridade.

---

### 5.6.8 Caso 8 — CPU Ociosa

Objetivo: verificar o comportamento quando não existir processo no estado PRONTO.

ALGORITMO RR
QUANTUM 10

PROCESSO P1 1 CPU(5) IO(15) CPU(5) EXIT

Após P1 solicitar E/S, a CPU ficará ociosa até a conclusão da operação.

O gráfico deverá registrar:

0,5 P1
5,20 IDLE
20,25 P1

O intervalo IDLE deverá ser contabilizado nas estatísticas.

---

### 5.6.9 Caso 9 — Criação por FORK

Objetivo: verificar a criação dinâmica de um processo.

ALGORITMO RR
QUANTUM 10

PROCESSO P1 3 CPU(5) FORK(P2) CPU(10) EXIT
PROCESSO P2 2 CPU(10) EXIT

P2 deverá ser criado somente quando P1 executar:

FORK(P2)

O processo filho deverá:

possuir seu próprio PCB;
possuir PID próprio;
entrar no estado PRONTO;
possuir instante de chegada igual ao instante do FORK;
ser inserido na fila de processos prontos.

---

### 5.6.10 Caso 10 — Comparação entre Algoritmos

Objetivo: demonstrar que diferentes algoritmos podem produzir diferentes ordens de execução e métricas.

Round Robin
ALGORITMO RR
QUANTUM 10

PROCESSO P1 1 CPU(30) EXIT
PROCESSO P2 3 CPU(20) EXIT
PROCESSO P3 5 CPU(40) EXIT

Prioridade
ALGORITMO PRIORIDADE
QUANTUM 10

PROCESSO P1 1 CPU(30) EXIT
PROCESSO P2 3 CPU(20) EXIT
PROCESSO P3 5 CPU(40) EXIT

Os resultados deverão ser comparados considerando:

ordem de execução;
tempo médio de espera;
tempo médio de resposta;
tempo médio de turnaround;
número de preempções;
número de trocas de contexto;
utilização da CPU.
O objetivo será demonstrar o impacto da política de escalonamento sobre o comportamento do simulador.

---

## 5.7 Critérios de Validação

A implementação será considerada válida quando:

nenhum processo estiver simultaneamente em mais de um estado;
processos bloqueados não utilizarem a CPU;
processos terminados não retornarem ao estado PRONTO;
o Round Robin respeitar o quantum;
processos preemptados pelo Round Robin retornarem ao final da fila;
o escalonador de prioridade selecionar o processo de menor valor numérico de prioridade;
valores menores representarem prioridades maiores;
o aging for aplicado somente aos processos PRONTO;
a prioridade nunca seja menor que 1;
processos de mesma prioridade utilizem Round Robin como desempate;
preempções por prioridade ocorram somente quando um processo de prioridade superior entrar no estado PRONTO;
solicitações de E/S provoquem EXECUTANDO -> BLOQUEADO;
conclusões de E/S provoquem BLOQUEADO -> PRONTO;
o término provoque EXECUTANDO -> TERMINADO;
processos criados por FORK possuam PCB próprio;
os PIDs sejam únicos;
o log registre as principais transições;
o gráfico de Gantt registre todos os intervalos de CPU;
períodos sem processos prontos sejam registrados como IDLE;
o tempo de CPU ocupado seja compatível com o Gantt;
o tempo de CPU ociosa seja compatível com os intervalos IDLE;
a utilização da CPU seja calculada corretamente;
o tempo de espera considere somente o estado PRONTO;
o tempo bloqueado não seja contabilizado como tempo de espera;
o tempo de resposta seja calculado a partir do instante de chegada;
o turnaround seja calculado a partir do instante de chegada e do término;
as estatísticas sejam compatíveis com o log;
o simulador rejeite entradas inválidas;
a execução seja determinística para uma mesma entrada.
