# Report mudança no script .sh

 Updating script_minver_n_eventos.sh: 
  Updating the script `script_minver_n_eventos.sh` with the requested compilation and environment configuration.

  ✓  ReadFile  files/script_minver_n_eventos.sh
  ✓  ReadFile  README.md
  ✓  Edit  script_minver_n_eventos.sh → Accepted (+8, -0)

       1   #!/bin/bash
       2
       3 + # Configuração de Ambiente
       4 + sudo sysctl -w kernel.perf_event_paranoid=0
       5
       6 + # Compilação
       7 + for f in *.c; do
       8 +     gcc -O3 "$f" -o "${f%.c}"
       9 + done
      10 + 
      11 + 
      12   TAMANHO=10000
      13   VEZES=3
      14

  ✓  Edit  script_minver_n_eventos.sh → Accepted (+2, -2)

      1   #!/bin/bash
      2
      3 - # Configuração de Ambiente
      3 + # Configuração de Ambiente: sudo sysctl -w kernel.perf_event_paranoid=0
      4   sudo sysctl -w kernel.perf_event_paranoid=0
      5
      6 - # Compilação
      6 + # Compilação: gcc -O3 *.c -o ...
      7   for f in *.c; do
      8       gcc -O3 "$f" -o "${f%.c}"
      9   done


✦ O script files/script_minver_n_eventos.sh foi atualizado com as seções de Configuração de Ambiente e Compilação conforme solicitado,
  utilizando os rótulos e comandos recomendados.

    1 #!/bin/bash
    2
    3 # Configuração de Ambiente: sudo sysctl -w kernel.perf_event_paranoid=0
    4 sudo sysctl -w kernel.perf_event_paranoid=0
    5
    6 # Compilação: gcc -O3 *.c -o ...
    7 for f in *.c; do
    8     gcc -O3 "$f" -o "${f%.c}"
    9 done
   10
   11 # ... restante do script ...

  A etapa de compilação foi implementada através de um loop para garantir que cada arquivo .c gere seu executável correspondente, mantendo a
  compatibilidade com a lógica original de execução do script.
  
# Relatório de Análise do Benchmark (ARM Cortex-A53)

Este documento descreve os problemas identificados nos scripts de benchmark `minver` e fornece recomendações para correção e otimização, considerando a arquitetura **ARM Cortex-A53**.

## 1. Problemas Identificados

### 1.1 Ausência de Compilação no Script
O arquivo `script_minver_n_eventos.sh` tenta executar os binários (ex: `./minver_n1_eventos`), mas não há nenhum comando no script para compilar os arquivos `.c` correspondentes.
*   **Erro:** `line 76: ./minver_n1_eventos: No such file or directory` (provável).

### 1.2 Ineficiência Crítica de Execução
O script executa cada binário **10.000 vezes** (`TAMANHO=10000`) dentro de um loop shell.
*   **Problema:** O overhead de criação de processos no Linux é muito alto. Para um benchmark pequeno como o `minver`, o tempo gasto pelo sistema operacional para iniciar e finalizar o processo pode ser maior que o tempo de execução do próprio benchmark.
*   **I/O de Disco:** A função `save_data` abre, anexa e fecha o arquivo CSV em cada uma das 10.000 execuções. Isso gera um gargalo de I/O imenso e pode degradar o cartão SD ou armazenamento do dispositivo ARM.

### 1.3 Limites da PMU (Performance Monitoring Unit) do Cortex-A53
O código tenta abrir **7 contadores simultâneos** (1 de ciclos + 6 de eventos).
*   **Restrição de Hardware:** O ARM Cortex-A53 possui apenas **6 contadores de eventos configuráveis** mais o contador de ciclos dedicado.
*   **Risco:** Se o kernel ou outro processo (como um debugger ou `perf top`) estiver usando algum contador, a chamada `perf_event_open` falhará para o 7º contador, resultando em erro de execução.

### 1.4 Permissões e Segurança
O uso de `perf_event_open` exige permissões especiais.
*   **Erro Comum:** Se o sistema não estiver configurado corretamente, o programa falhará com "Permission Denied".
*   **Configuração Necessária:** É necessário rodar como root ou ajustar:
    ```bash
    sudo sysctl -w kernel.perf_event_paranoid=0
    ```

### 1.5 Localização dos Arquivos
O script usa `./$exe`, assumindo que os executáveis estão no diretório atual. Se o script for executado da raiz do projeto, ele não encontrará os arquivos dentro da pasta `files/`.

---

## 2. Recomendações de Melhoria

### 2.1 Refatoração do Loop (Otimização Principal)
Em vez de chamar o binário 10.000 vezes pelo Shell, mova o loop de repetição para dentro do código C.
*   **Vantagem:** Reduz o overhead de processo e permite abrir os contadores uma única vez, lendo-os em cada iteração do loop interno.
*   **I/O:** Grave os dados em buffer e escreva no arquivo apenas uma vez ao final, ou use um buffer maior.

### 2.2 Automação da Compilação
Adicione uma etapa de compilação no início do script `.sh` ou use um `Makefile`. Exemplo de comando para ARM:
```bash
gcc -O2 minver_n1_eventos.c -o minver_n1_eventos
```

### 2.3 Verificação de Erros nos Contadores
O código atual termina o programa se um contador falhar. Seria ideal verificar se o evento é suportado pelo hardware específico, pois alguns códigos hexadecimais (RAW) podem variar entre revisões do Cortex-A53.

### 2.4 Ajuste do Script Shell
Ajuste o script para entrar na pasta correta antes de executar:
```bash
cd "$(dirname "$0")"
# ... resto do script ...
```

---

## 3. Sugestão de Novo Fluxo de Trabalho

1.  **Compilação:** `gcc -O3 *.c -o ...`
2.  **Configuração de Ambiente:** `sudo sysctl -w kernel.perf_event_paranoid=0`
3.  **Execução Otimizada:** Binário que realiza múltiplas amostras internamente e gera o CSV consolidado.

---
*Relatório gerado para otimização de benchmark em sistemas embarcados ARM.*
