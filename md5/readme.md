# Report mudanças feitas no script .sh
        1   #!/bin/bash
        2
        3 - 
        3 + # Configurações de Benchmark
        4   TAMANHO=10000
        5   VEZES=3
        6
        7 + # Verificação de permissões para perf_event
        8 + PARANOID=$(cat /proc/sys/kernel/perf_event_paranoid)
        9 + if [ "$PARANOID" -gt 0 ]; then
       10 +     echo "AVISO: kernel.perf_event_paranoid é $PARANOID. O benchmark pode falhar."
       11 +     echo "Execute: sudo sysctl -w kernel.perf_event_paranoid=0"
       12 + fi
       13 + 
       14   ## listas com 10 parâmetros
       15   arquivocsv=(
       16   "saida_md5_n_eventos.csv"
      ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
       66
       67   TEXTO_CI="fim cnt n eventos"
       68
       69 + # Garante que estamos no diretório do script
       70 + cd "$(dirname "$0")"
       71 + 
       72 + # Compilação dos arquivos C para ARM Cortex-A53
       73 + echo "Compilando benchmarks para ARM Cortex-A53..."
       74 + for exe in "${arquivoexe[@]}"
       75 + do
       76 +     if [ ! -f "$exe" ]; then
       77 +         echo "Compilando $exe..."
       78 +         gcc -O3 -march=armv8-a -mtune=cortex-a53 "${exe}.c" -o "$exe"
       79 +         if [ $? -ne 0 ]; then
       80 +             echo "Erro ao compilar ${exe}.c"
       81 +             exit 1
       82 +         fi
       83 +     fi
       84 +     chmod +x "$exe"
       85 + done
       86 + 
       87   for k in ${!arquivoexe[@]}
       88   do
       89       csv=${arquivocsv[$k]}
       91       prefix=${novonomeCI[$k]}
       92       head=${header[$k]}
       93
       69 -     COUNT=0
      ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
       94 +     echo "Iniciando benchmark para $exe..."
       95
       96       for j in $(seq 1 $VEZES)
       97       do
       98           rm -f "$csv"
       74 -     echo "$head" > "$csv"
      ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
       99 +         echo "$head" > "$csv"
      100
      101 +         echo "  Rodada $j/$VEZES ($TAMANHO execuções)..."
      102           for i in $(seq 1 $TAMANHO)
      103           do
      104               ./$exe
      105 +             if [ $? -ne 0 ]; then
      106 +                 echo "Erro na execução de $exe na iteração $i"
      107 +                 exit 1
      108 +             fi
      109           done
      110
       81 -         COUNT=$((COUNT+1))
       82 -         nomecsv=${prefix}${COUNT}.csv
       83 - 
      ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
      111 +         nomecsv=${prefix}${j}.csv
      112           mv "$csv" "$nomecsv"
      113
       86 -     sleep 1
       87 - 
       88 -         echo $TEXTO_CI $k $COUNT
      ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
      114 +         sleep 1
      115 +         echo "$TEXTO_CI $k $j"
      116       done
       90 - 
      ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
      117   done
      118 + 
      119 + echo "Benchmark concluído com sucesso."


✦ Analise realizada com sucesso. Abaixo apresento o relatório dos problemas identificados e as correções aplicadas ao seu script .sh.

  Relatório de Análise

   1. Ausência de Compilação: O script original tentava executar binários (ex: ./md5_n1_eventos) que não existiam no diretório, apenas os
      arquivos fonte .c estavam presentes.
   2. Permissões de Contadores de Performance (PMU): O código C utiliza a syscall perf_event_open. Em sistemas Linux (como o ARM Cortex-A53), o
      acesso a esses contadores é restrito por padrão. Se o arquivo /proc/sys/kernel/perf_event_paranoid estiver com valor maior que 0, o
      benchmark falhará ao tentar abrir os eventos.
   3. Falta de Otimização de Arquitetura: Para um benchmark fiel no Cortex-A53, é essencial que o compilador saiba para qual processador está
      gerando código, permitindo o uso eficiente do pipeline e das instruções ARMv8-A.
   4. Caminhos e Execução: O script não validava se estava no diretório correto ou se os binários tinham permissão de execução.

  ---

  Correções aplicadas no script_md5_n_eventos.sh

  O script foi reescrito para incluir:
   * Compilação Automática: Agora o script verifica se o executável existe; caso contrário, ele compila o .c correspondente usando:
      gcc -O3 -march=armv8-a -mtune=cortex-a53.
   * Verificação de Permissões: Adicionado um check inicial que alerta se o perf_event_paranoid precisa ser ajustado (geralmente para 0 ou -1).
   * Gestão de Diretório: Comando cd "$(dirname "$0")" adicionado para garantir que o script funcione independente de onde seja chamado.
   * Verificação de Erros: O script agora interrompe a execução caso uma compilação ou rodada do benchmark falhe, evitando arquivos CSV
     corrompidos ou vazios.

  Como rodar
  Antes de executar o novo script, recomendo rodar o seguinte comando no terminal do ARM para liberar os contadores de performance:

   1 sudo sysctl -w kernel.perf_event_paranoid=0

  Em seguida, basta rodar o script:

   1 chmod +x script_md5_n_eventos.sh
   2 ./script_md5_n_eventos.sh

  O arquivo script_md5_n_eventos.sh já foi atualizado no seu diretório com estas melhorias.


# Relatório de Análise de Benchmark MD5 - ARM Cortex-A53

Este relatório descreve os problemas identificados nos scripts de benchmark e no código-fonte fornecido, com foco especial na execução em arquitetura **ARM Cortex-A53**.

## 1. Problemas Estruturais e de Performance

### Overhead de Execução (Shell Script)
O script `script_md5_n_eventos.sh` executa o benchmark 10.000 vezes (`TAMANHO=10000`) dentro de um loop para cada grupo de eventos.
- **Problema:** Para cada uma das 10.000 iterações, o sistema operacional precisa criar um novo processo, abrir arquivos, inicializar a API `perf_event_open` e fechar tudo ao final.
- **Consequência:** O tempo gasto com o *overhead* do sistema operacional e da inicialização do `perf` é significativamente maior do que o tempo de execução do algoritmo MD5 em si. Isso torna os dados de benchmark ruidosos e imprecisos.
- **Recomendação:** Mover o loop de repetições para **dentro do código C**, medindo a execução de 10.000 iterações em uma única abertura de contadores.

### Contenção de I/O
A função `save_data` no código C abre o arquivo `saida_md5_n_eventos.csv` em modo *append* (`"a"`) a cada execução.
- **Problema:** Com 10.000 execuções rápidas, a constante abertura e fechamento do arquivo gera uma carga desnecessária no sistema de arquivos.
- **Consequência:** Risco de inconsistência nos dados e gargalo de performance no I/O.

## 2. Compatibilidade com ARM Cortex-A53 (PMU)

### Limite de Contadores de Hardware
O processador ARM Cortex-A53 possui uma **Unidade de Monitoramento de Performance (PMU)** que geralmente suporta:
- 1 contador de ciclo dedicado (`CYCLES`).
- **Até 6 contadores de eventos configuráveis.**

**Análise do Código:**
Os arquivos (ex: `md5_n1_eventos.c`) tentam abrir 7 eventos simultâneos (Cycles + 6 eventos RAW).
- **Risco:** Se o kernel ou outros processos já estiverem utilizando algum contador, a chamada `perf_event_open` pode falhar para o último evento ou o sistema pode entrar em modo de *multiplexação* (o que reduz a precisão).
- **Nota:** Os grupos definidos no script parecem respeitar o limite de 6 eventos + Cycles, mas é importante garantir que o sistema esteja limpo de outros perfis de monitoramento.

### Eventos RAW PMU (Cortex-A53)
O código utiliza `pea.type = PERF_TYPE_RAW;` com códigos como `0x00`, `0x01`, etc.
- **Validação:** Estes códigos correspondem aos eventos nativos do ARMv8 (L1 Cache access, L1 Refill, etc.). No entanto, alguns eventos específicos (como os da faixa `0xC0-0xE8` vistos no script) podem variar dependendo da implementação específica do chip (ex: Raspberry Pi 3 vs. outros SoCs).
- **Erro Comum:** Se o evento solicitado não for suportado pela implementação específica do A53 no seu hardware, o `perf_event_open` retornará erro.

## 3. Erros de Lógica no Script Shell

### Gerenciamento de Arquivos CSV
No script:
```bash
for j in $(seq 1 $VEZES)
do
    rm -f "$csv"
    echo "$head" > "$csv"
    for i in $(seq 1 $TAMANHO)
    do
        ./$exe
    done
    # ... move o arquivo
done
```
- **Conflito:** O cabeçalho é escrito uma única vez, mas o executável `./$exe` abre o arquivo em modo *append* 10.000 vezes. Se o executável falhar ou se houver interrupção, o arquivo pode ficar corrompido ou sem o cabeçalho correto para a próxima iteração do loop interno.

## 4. Recomendações de Correção

1.  **Refatoração do Código C:**
    - Envolva a chamada `md5_main()` em um loop de 10.000 iterações.
    - Abra o arquivo CSV apenas uma vez no `main`, ou acumule os resultados em memória e salve ao final.
2.  **Configuração do Sistema:**
    - Certifique-se de que o nível de permissão do perf permite a captura de eventos (`sudo sysctl -w kernel.perf_event_paranoid=0`).
3.  **Verificação de Eventos:**
    - Antes de rodar o benchmark em larga escala, teste cada grupo de eventos com `perf list` ou uma execução única para garantir que o hardware aceita os códigos hexadecimais configurados.
4.  **Afinidade de CPU:**
    - O código já fixa a execução na CPU 0 (`sched_setaffinity`). Certifique-se de que nenhum outro processo pesado esteja rodando neste núcleo durante o benchmark.

---
*Relatório gerado para otimização de benchmarks em sistemas embarcados ARM.*
