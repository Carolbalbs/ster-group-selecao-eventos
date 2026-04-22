# Real-Time Systems Research Group (STER) 
### Análise de Eventos PMU 

Este projeto é uma ferramenta de análise de eventos de contadores de performance (PMU) para processadores ARM Cortex-A53. Ele permite visualizar e calcular métricas avançadas (como Entropia de Shannon, Bimodalidade de Sarle e Informação Mútua) para identificar gargalos e comportamentos anômalos em diferentes benchmarks.

## 🚀 Como Executar

### 1. Pré-requisitos
Certifique-se de ter o Python 3.13+ instalado. É recomendado o uso de um ambiente virtual.

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar o ambiente virtual (Linux/macOS)
source .venv/bin/activate

# Ativar o ambiente virtual (Windows)
# .venv\Scripts\activate
```

### 2. Instalação de Dependências
Instale as bibliotecas necessárias listadas no `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Execução do Dashboard Interativo
O dashboard permite navegar pelos benchmarks e visualizar os dados de forma gráfica.

```bash
python dashboard.py
```
Após executar, abra o navegador no endereço: `http://localhost:8050`

### 4. Execução do Script de Processamento (Batch)
O arquivo `script.py` pode ser usado para processar pastas inteiras e gerar tabelas de métricas consolidadas em Excel ou CSV.

*Nota: Antes de executar, você pode precisar editar as variáveis `PASTA_DADOS` e `PASTA_RESULTADOS` dentro do `script.py` para apontar para o diretório desejado.*

```bash
python script.py
```

## 📁 Estrutura de Dados e Carregamento

O projeto está organizado por benchmarks e intervalos de tempo:

- **Benchmarks incluídos:** `bs`, `cnt`, `fibcall_perf_ite`, `matmult`, `msort`.
- **Subdiretórios:** Cada benchmark contém subpastas `intervalo1`, `intervalo2`, `intervalo3`.
- **Formato dos Arquivos:** 
  - Os arquivos devem ser `.csv`.
  - O separador utilizado é o ponto e vírgula (`;`).
  - É obrigatório que os arquivos contenham uma coluna chamada `CYCLES`, que é utilizada como alvo (target) para os cálculos de correlação e impacto.

## 📊 Métricas Calculadas

- **MI Global:** Informação mútua entre o evento e os ciclos de CPU.
- **Impacto Bilateral:** Identifica picos excessivos ou quedas abruptas de performance.
- **Bimodalidade (Sarle):** Detecta se o comportamento do evento se divide em dois regimes distintos.
- **Entropia de Shannon:** Mede a imprevisibilidade/variabilidade do evento.
- **Índice Global:** Uma métrica ponderada (Base 2) que combina Informação Mútua e Impacto para ranquear os eventos mais críticos.

## 🛠️ Tecnologias Utilizadas

- **Dash/Plotly:** Para a interface web e gráficos interativos.
- **Pandas/Numpy:** Para manipulação de dados.
- **Scikit-learn:** Para cálculos de Informação Mútua (Regression).
- **Scipy:** Para cálculos estatísticos avançados.
