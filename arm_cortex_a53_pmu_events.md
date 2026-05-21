# ARM Cortex-A53 — Eventos PMU

**Performance Monitor Unit · DDI 0500J**  
Descrições detalhadas de todos os eventos do contador de performance do Cortex-A53.

---

## Índice de Categorias

| Categoria | Eventos |
|-----------|---------|
| 🟠 Cache | 0x01, 0x03, 0x04, 0x14, 0x15, 0x16, 0x17, 0x18, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xD0, 0xD1 |
| 🟢 TLB | 0x02, 0x05, 0xD2 |
| 🔴 Branch | 0x0C, 0x0D, 0x0E, 0x10, 0x12, 0x7A, 0xC9, 0xCA, 0xCB, 0xCC |
| 🔵 Instrução | 0x06, 0x07, 0x08 |
| 🟣 Memória | 0x0F, 0x13, 0xC0, 0xC1, 0xC8 |
| ⚫ Barramento | 0x19, 0x1D, 0x60, 0x61 |
| 🟡 Exceção | 0x09, 0x0A, 0x86, 0x87 |
| 🩵 Pipeline/Perf | 0xC7, 0xE0, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8 |
| ⬜ Misc | 0x00, 0x0B, 0x11, 0x1A, 0x1E |

---

## Tabela Completa de Eventos

### 🟠 Cache

---

#### `0x01` — L1I_CACHE_REFILL · *L1 Instruction cache refill*

Ocorre quando uma instrução não está presente na cache L1 (cache miss de instrução). A CPU precisa buscar a linha de cache da memória de nível superior (L2 ou DRAM).

Alta taxa indica baixa localidade do código: loops muito grandes, chamadas frequentes a funções dispersas na memória, ou código muito volumoso.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[0]` | `[0]` |

---

#### `0x03` — L1D_CACHE_REFILL · *L1 Data cache refill*

Miss na cache de dados L1 — o dado requisitado precisa ser buscado da L2 ou da RAM. É um indicador crítico de performance, pois causa pipeline stall enquanto o dado é buscado.

Pode indicar padrões de acesso não sequenciais, estruturas de dados muito grandes, ou má localidade de dados.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[2]` | `[2]` |

---

#### `0x04` — L1D_CACHE · *L1 Data cache access*

Conta todos os acessos à cache de dados L1 (hits + misses). Usado para calcular a taxa de miss da L1:

> **Taxa de miss (%) = (L1D_CACHE_REFILL / L1D_CACHE) × 100**

Uma taxa acima de 5–10% geralmente indica problema de performance relacionado à cache.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[3]` | `[3]` |

---

#### `0x14` — L1I_CACHE · *L1 Instruction cache access*

Todos os acessos à cache de instrução L1 (hits + misses). Junto com `L1I_CACHE_REFILL`, permite calcular a taxa de miss de instrução.

> **Taxa de miss (%) = (L1I_CACHE_REFILL / L1I_CACHE) × 100**

Uma taxa acima de 1–2% já impacta performance significativamente.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[18]` | `[18]` |

---

#### `0x15` — L1D_CACHE_WB · *L1 Data cache Write-Back*

Write-backs da cache de dados L1: quando uma linha modificada (*dirty*) é escrita de volta para a L2 para liberar espaço. Frequente em aplicações com alto volume de escrita.

Alta frequência pode indicar thrashing da L1 (working set maior que a capacidade da L1) ou muitas alocações/liberações de memória.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[19]` | `[19]` |

---

#### `0x16` — L2D_CACHE · *L2 Data cache access*

Acessos à cache de dados L2, acionada apenas quando há miss na L1D. A razão `L2D_CACHE_REFILL / L2D_CACHE` indica a taxa de miss da L2.

O Cortex-A53 possui L2 unificada (dados e instruções) configurável de 128KB a 2MB.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[20]` | `[20]` |

---

#### `0x17` — L2D_CACHE_REFILL · *L2 Data cache refill*

Miss na cache L2 — precisa ir à memória principal (DRAM). É o evento de maior impacto na latência: um miss na L2 pode custar dezenas a centenas de ciclos.

Alta frequência indica que o working set é maior que a L2 total disponível.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[21]` | `[21]` |

---

#### `0x18` — L2D_CACHE_WB · *L2 Data cache Write-Back*

Write-backs da cache L2 para a memória principal. Ocorre quando uma linha dirty é evicta da L2. Em sistemas multi-core, também pode refletir invalidações de coerência de cache entre núcleos.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[22]` | `[22]` |

---

#### `0xC2` — *Linefill because of prefetch*

Conta linefills (recargas de linha de cache) originados pelo hardware prefetcher — o mecanismo que antecipa acessos sequenciais e os busca proativamente. Um prefetch eficiente aumenta a taxa de hits ao trazer dados antes de serem necessários.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xC3` — *Instruction Cache Throttle occurred*

Throttling do pipeline de busca de instruções: ativado quando a fila de instruções decodificadas (instruction queue) está cheia e a cache de instrução precisa pausar novos fetches para evitar overflow interno.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xC4` — *Entering read allocate mode*

Transições para o modo de alocação de leitura (write-no-allocate para misses de escrita). Ativado automaticamente ao detectar padrões de acesso sequencial, para evitar poluição da cache com dados que não serão reutilizados.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xC5` — *Read allocate mode*

Ciclos em que o processador está em modo de alocação de leitura. Junto com `0xC4`, permite medir por quanto tempo o processador operou neste modo otimizado para streaming de dados.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xC6` — *Pre-decode error*

Erros de pré-decodificação de instrução na carga para a L1I. Força novo ciclo completo de fetch/decode, causando stall do pipeline. Pode ocorrer com código automodificável ou após invalidação de cache de instrução.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xD0` — *L1 Instruction Cache memory error*

Erros ECC na cache de instrução L1 (dados ou tags). Inclui erros corrigíveis (single-bit) e não-corrigíveis (multi-bit). Disponível no barramento de trace. Qualquer ocorrência deve ser investigada como potencial falha de hardware.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `[23]` |

---

#### `0xD1` — *L1 Data Cache memory error*

Erros ECC na cache de dados L1 (dados, tags ou dirty bits). Pode ser corrigível (SEC — Single Error Correction) ou não-corrigível (DED — Double Error Detection). Crítico para sistemas de alta confiabilidade (automotive, industrial).

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `[24]` |

---

### 🟢 TLB

---

#### `0x02` — L1I_TLB_REFILL · *L1 Instruction TLB refill*

Recarga do TLB de instruções L1. Quando o mapeamento virtual→físico de uma instrução não está no TLB, ocorre uma *page table walk* para encontrar a tradução. Frequente após troca de contexto ou com espaço de instrução muito disperso.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[1]` | `[1]` |

---

#### `0x05` — L1D_TLB_REFILL · *L1 Data TLB refill*

Miss no TLB de dados L1, forçando *page table walk*. Alta frequência indica que o working set de dados está espalhado em muitas páginas de memória virtual, gerando muitas traduções novas.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[4]` | `[4]` |

---

#### `0xD2` — *TLB memory error*

Erros ECC nas estruturas do TLB. Um erro pode causar tradução incorreta de endereço, potencialmente levando a acesso a memória errada. Com ECC habilitado, erros single-bit são corrigidos automaticamente, mas devem ser monitorados.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `[25]` |

---

### 🔴 Branch

---

#### `0x0C` — PC_WRITE_RETIRED · *Software change of PC*

Conta mudanças de fluxo de controle que alteram o PC diretamente via software (BLR/BR com registradores específicos). Comum em máquinas virtuais, interpretadores e código com tabelas de dispatch calculadas em tempo de execução.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[12]` | `[12]` |

---

#### `0x0D` — BR_IMMED_RETIRED · *Immediate branch executed*

Branches com alvo imediato (B, BL, CBZ, CBNZ, TBZ, TBNZ em AArch64) executados arquiteturalmente. O alvo é fixo na instrução, diferente de branches indiretos onde o alvo é calculado em registrador.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[13]` | `[13]` |

---

#### `0x0E` — BR_RETURN_RETIRED · *Procedure return executed*

Retornos de subrotina (RET em AArch64, POP {PC} em AArch32) arquiteturalmente executados. O preditor de branches usa o RAS (*Return Address Stack*) para prever o endereço de retorno. Alta frequência em código com muitas chamadas a funções pequenas.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0x10` — BR_MIS_PRED · *Branch mispredicted*

Branch malpredito ou não-predito. Causa descarte de todas as instruções buscadas especulativamente no caminho errado. No Cortex-A53 com pipeline de 8 estágios, isso representa até ~8 ciclos desperdiçados por misprediction.

> **Taxa ideal: menos de 1–2% do total de branches**

| Bus externo | Bus de trace |
|-------------|--------------|
| `[15]` | `[15]` |

---

#### `0x12` — BR_PRED · *Predictable branch speculatively executed*

Branches predizíveis executados especulativamente. A razão `BR_MIS_PRED / BR_PRED` indica a taxa de misprediction. Branches biased (quase sempre tomados ou não) são fáceis de prever; branches dependentes de dados aleatórios são difíceis.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[16]` | `[16]` |

---

#### `0x7A` — BR_INDIRECT_SPEC · *Indirect branch speculatively executed*

Branches indiretos executados especulativamente (BLR Xn, BR Xn — alvo em registrador). Mais difíceis de prever que branches imediatos. Relevante para análise de vulnerabilidades Spectre variante 2 (BTI — Branch Target Injection).

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xC9` — *Conditional branch executed*

Branches condicionais executados (B.EQ, B.NE, B.GT, etc. em AArch64). Subset de `BR_IMMED_RETIRED` focado em branches cujo resultado depende das flags de estado (NZCV) de operação anterior.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xCA` — *Indirect branch mispredicted*

Mispredictions de branches indiretos (alvo em registrador). São muito difíceis de prever — requerem BTB (*Branch Target Buffer*) especializado. Alta frequência em código com ponteiros de função, dispatch virtual ou interpretadores.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xCB` — *Indirect branch mispredicted — address miscompare*

Refinamento de `0xCA`: mispredictions de branches indiretos especificamente por *address miscompare* — o preditor previu um endereço diferente do real. Distingue de casos onde o branch simplesmente não estava no BTB (cold miss).

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xCC` — *Conditional branch mispredicted*

Mispredictions de branches condicionais. Taxa de mispredição condicional = `0xCC / 0xC9`. Branches com padrão irregular (condições dependentes de dados de entrada aleatórios) são os mais difíceis de prever.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

### 🔵 Instrução

---

#### `0x06` — LD_RETIRED · *Load instruction retired*

Instrução de carga (load) executada arquiteturalmente com condição satisfeita. *Retired* = completou sem ser descartada por branch misprediction ou exceção. Útil para medir pressão de leitura de memória e calcular IPC.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[5]` | `[5]` |

---

#### `0x07` — ST_RETIRED · *Store instruction retired*

Instrução de armazenamento (store) arquiteturalmente executada. Razão típica load/store é 2:1 a 3:1 em código de propósito geral. Valores muito altos podem indicar código com muita escrita em memória ou uso de MMIO.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[6]` | `[6]` |

---

#### `0x08` — INST_RETIRED · *Instruction architecturally executed*

Contador geral de instruções executadas. Base para calcular:

> **IPC = INST_RETIRED / CPU_CYCLES**  
> **CPI = CPU_CYCLES / INST_RETIRED**

IPC próximo de 1 é razoável no Cortex-A53; valores menores indicam gargalos no pipeline (dependências de dados, misses de cache, branches malpreditos).

| Bus externo | Bus de trace |
|-------------|--------------|
| `[7]` | `[7]` |

---

### 🟣 Memória

---

#### `0x0F` — UNALIGNED_LDST_RETIRED · *Unaligned load or store*

Loads/stores com endereço não-alinhado (ex: acessar um int de 4 bytes em endereço ímpar). Suportados por hardware no Cortex-A53, mas causam penalidade de performance — o acesso é dividido em múltiplas operações internas.

Alta frequência indica necessidade de revisar alinhamento de estruturas de dados.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[14]` | `[14]` |

---

#### `0x13` — MEM_ACCESS · *Data memory access*

Conta qualquer load ou store que gera requisição à hierarquia de memória (L1D, L2, DRAM). Mede a pressão total no subsistema de memória. Diferente de `L1D_CACHE`, que conta apenas acessos à L1.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[17]` | `[17]` |

---

#### `0xC0` — *External memory request*

Requisições enviadas para memória externa ao processador — todos os acessos que saem do chip ou cluster para o controlador de DRAM. Evento específico da implementação Cortex-A53, sem mnemônico ARMv8 padrão.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xC1` — *Non-cacheable external memory request*

Requisições de memória marcada como não-cacheável (Device ou Normal Non-Cacheable nos atributos MMU). Comum para acessos a registradores de periféricos mapeados em memória (MMIO). Não pode ser acelerado por cache.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xC8` — *SCU Snooped data from another CPU*

O SCU (*Snoop Control Unit*) satisfez uma requisição deste CPU buscando dados modificados no cache de outro CPU no mesmo cluster (em vez de ir à memória principal). Mede comunicação inter-core via coerência de cache — comum em código paralelo com dados compartilhados.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

### ⚫ Barramento

---

#### `0x19` — BUS_ACCESS · *Bus access*

Conta transações que saem do cluster do processador para memória externa ou periféricos. Mede o tráfego total no barramento AXI/ACE. Alta frequência indica pouco reuso de dados nas caches e pressão no controlador de memória.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0x1D` — BUS_CYCLES · *Bus cycle*

Ciclos do barramento de memória (que pode operar em frequência diferente do núcleo). Útil para análise de eficiência do barramento e cálculo de ocupação. Junto com `BUS_ACCESS`, permite calcular a largura de banda efetiva utilizada.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0x60` — BUS_ACCESS_LD · *Bus access — Read*

Acessos de leitura ao barramento de memória (subset de `BUS_ACCESS`). Leituras normalmente dominam o tráfego, pois misses de cache de instrução e dados geram leituras à DRAM.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0x61` — BUS_ACCESS_ST · *Bus access — Write*

Acessos de escrita ao barramento (write-backs de caches e stores até a DRAM). A razão leitura/escrita típica no barramento é de 3:1 a 5:1 em workloads gerais.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

### 🟡 Exceção

---

#### `0x09` — EXC_TAKEN · *Exception taken*

Conta todas as exceções tomadas: IRQ, FIQ, falhas de página (*page faults*), erros de alinhamento, chamadas de sistema (SVC), armadilhas de depuração, etc.

Alta frequência pode indicar excesso de chamadas de sistema, muitas interrupções de hardware ou *thrashing* de memória virtual.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[9]` | `[9]` |

---

#### `0x0A` — EXC_RETURN · *Exception return*

Conta execuções da instrução de retorno de exceção (ERET no AArch64). Complementa `EXC_TAKEN` — uma diferença grande entre os dois pode indicar aninhamento profundo de exceções ou exceções não tratadas.

| Bus externo | Bus de trace |
|-------------|--------------|
| `[10]` | `[10]` |

---

#### `0x86` — EXC_IRQ · *Exception taken — IRQ*

Conta apenas as exceções do tipo IRQ (*Interrupt Request*) — interrupções de hardware de nível normal. Cada IRQ tem overhead de salvar/restaurar contexto + executar a ISR — tipicamente dezenas a centenas de ciclos por interrupção.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0x87` — EXC_FIQ · *Exception taken — FIQ*

Interrupções de alta prioridade (*Fast Interrupt Request*) com latência reduzida. Em AArch32 possui banco de registradores dedicado. Em AArch64 é tratado como IRQ de maior prioridade pelo GIC (*Generic Interrupt Controller*).

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

### 🩵 Pipeline / Performance Impact

> Estes eventos da faixa `0xE0–0xE8` quantificam em ciclos o custo de cada tipo de stall no pipeline — úteis para identificar o principal gargalo de performance de um workload.

---

#### `0xC7` — *Store buffer full stall*

Ciclos em que um store causou stall porque o store buffer estava cheio. O store buffer permite que stores sejam executados especulativamente antes de serem confirmados na cache. Quando cheio, o pipeline para. Indica alta pressão de escrita.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE0` — *IQ empty — no identified stall cause*

Ciclos em que a fila de instrução (DPU IQ) está vazia sem causa identificada de stall — o frontend não fornece instruções por razão não coberta pelos eventos `0xE1`–`0xE3`. Pode indicar stalls de busca não categorizados ou ineficiência geral do frontend.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE1` — *IQ empty — instruction cache miss*

Ciclos com DPU IQ vazio especificamente por miss de cache de instrução sendo processado. Quantifica diretamente o custo em ciclos de stall dos eventos `L1I_CACHE_REFILL` — ou seja, ciclos desperdiçados esperando instrução da L2/DRAM.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE2` — *IQ empty — instruction TLB miss*

Ciclos com DPU IQ vazio por miss no TLB de instrução. Quantifica o impacto de performance das *page table walks* causadas por `L1I_TLB_REFILL` — frequente em sistemas com uso intenso de memória virtual ou troca de contexto.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE3` — *IQ empty — pre-decode error*

Ciclos com DPU IQ vazio por erros de pré-decodificação (relacionado a `0xC6`). Quantifica o custo em ciclos dos erros de pré-decode, que forçam um novo ciclo completo de fetch/decode.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE4` — *Interlock — not FP/SIMD or AGU*

Ciclos com interlock (stall por dependência RAW — *Read After Write*) em instruções inteiras, excluindo SIMD/FP e load/store aguardando endereço. Uma instrução precisa do resultado de outra instrução inteira que ainda não completou.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE5` — *Interlock — load/store AGU*

Ciclos com interlock porque um load ou store aguarda o cálculo de endereço no AGU (*Address Generation Unit*). Ocorre quando o endereço de memória depende do resultado de uma instrução anterior ainda em execução.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE6` — *Interlock — Advanced SIMD or FP*

Ciclos com interlock causados por instruções NEON (Advanced SIMD) ou Floating-Point, que têm latências maiores que inteiras (tipicamente 3–6 ciclos). Uma instrução dependente do resultado de operação SIMD/FP pode causar stall de múltiplos ciclos.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE7` — *Wr stage stall — load miss*

Ciclos em que o estágio Wr (*Write-back*) do pipeline está parado porque um load não encontrou seu dado na cache. O pipeline aguarda o dado ser buscado da L2 ou DRAM. Um miss L1 pode custar 10+ ciclos de stall — um dos gargalos mais impactantes.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0xE8` — *Wr stage stall — store*

Ciclos em que o estágio Wr está parado por causa de um store. Pode ocorrer por store buffer cheio (relacionado a `0xC7`) ou conflito de banco na cache. Indica pressão no caminho de escrita do pipeline.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

### ⬜ Misc

---

#### `0x00` — SW_INCR · *Software Increment*

Incrementa um contador por software, escrevendo no registrador `PMSWINC_EL0`. Não conta automaticamente — útil para marcar pontos específicos no código, medir seções críticas, ou como contador de eventos definidos pelo programador.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0x0B` — CID_WRITE_RETIRED · *Change to Context ID retired*

Conta escritas no registrador CONTEXTIDR, normalmente feitas pelo SO em trocas de contexto entre processos. Útil para medir a frequência de context switches e seu impacto (invalidam BTB, partes do TLB, etc.).

| Bus externo | Bus de trace |
|-------------|--------------|
| `[11]` | `[11]` |

---

#### `0x11` — CPU_CYCLES · *CPU cycle counter*

Ciclos de clock do processador. Denominador essencial para todas as métricas de performance:

> **IPC = INST_RETIRED / CPU_CYCLES**  
> **CPI = CPU_CYCLES / INST_RETIRED**

Pode ser configurado com divisor de frequência para evitar overflow em medições longas em contadores de 32 bits.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0x1A` — MEMORY_ERROR · *Local memory error*

Conta erros ECC nas caches (single-bit corrigíveis ou multi-bit não-corrigíveis). Qualquer incremento deve ser investigado como potencial indicador de falha de hardware, memória defeituosa ou interferência eletromagnética.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

#### `0x1E` — CHAIN · *Odd counter chain mode*

Modo especial que encadeia dois contadores PMU adjacentes (par + ímpar) para formar um contador de 64 bits. O contador ímpar recebe carry do contador par. Necessário para eventos que possam causar overflow rapidamente em contadores de 32 bits, como `CPU_CYCLES` em alta frequência.

| Bus externo | Bus de trace |
|-------------|--------------|
| `-` | `-` |

---

## Fórmulas Úteis

| Métrica | Fórmula |
|---------|---------|
| IPC (Instruções por Ciclo) | `INST_RETIRED / CPU_CYCLES` |
| Taxa de miss L1D (%) | `L1D_CACHE_REFILL / L1D_CACHE × 100` |
| Taxa de miss L1I (%) | `L1I_CACHE_REFILL / L1I_CACHE × 100` |
| Taxa de miss L2 (%) | `L2D_CACHE_REFILL / L2D_CACHE × 100` |
| Taxa de misprediction (%) | `BR_MIS_PRED / BR_PRED × 100` |
| Razão Load/Store | `LD_RETIRED / ST_RETIRED` |
| Ciclos de stall por instrução | `(CPU_CYCLES - INST_RETIRED) / INST_RETIRED` |

---

*Fonte: ARM Cortex-A53 MPCore Processor Technical Reference Manual, DDI 0500J — Copyright © 2013–2018 Arm*
