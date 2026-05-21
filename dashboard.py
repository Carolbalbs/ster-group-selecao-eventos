import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import numpy as np
from scipy.stats import entropy, skew, kurtosis
from sklearn.feature_selection import mutual_info_regression

# --- Math Functions from script.py ---
def calc_entropia_shannon(serie):
    if serie.nunique() <= 1:
        return 0.0
    counts = serie.value_counts(normalize=True)
    return entropy(counts, base=2)

def calc_bimodalidade_sarle(serie):
    if serie.nunique() <= 1:
        return 0.0
    s = skew(serie)
    k = kurtosis(serie, fisher=False) 
    if k == 0:
        return 0.0
    return (s**2 + 1) / k

def calculate_metrics(df):
    if 'CYCLES' not in df.columns:
        return pd.DataFrame()
    
    df.columns = df.columns.str.strip()
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    
    if df.empty:
        return pd.DataFrame()

    y_target = df['CYCLES']
    X_raw = df.drop(columns=['CYCLES'])
    
    if X_raw.empty:
        return pd.DataFrame()

    limiar_crise = y_target.quantile(0.95)
    mask_crise = y_target >= limiar_crise
    y_crise = y_target[mask_crise]
    X_crise = X_raw[mask_crise]
    
    # MI Global
    try:
        mi_global_scores = mutual_info_regression(X_raw, y_target, random_state=42)
    except Exception as e:
        print(f"Error in MI Regression: {e}")
        mi_global_scores = [0.0] * len(X_raw.columns)
    
    resultados = []
    for idx, evento in enumerate(X_raw.columns):
        serie = X_raw[evento]
        
        media = serie.mean()
        cv = (serie.std() / media) if media != 0 else 0
        curtose_fisher = serie.kurtosis()
        shannon = calc_entropia_shannon(serie)
        
        p50 = serie.median()
        p99_9 = serie.quantile(0.999)
        p0_1 = serie.quantile(0.001)
        
        impacto_direito = (p99_9 - p50) / max(1, p50)
        impacto_esquerdo = (p50 - p0_1) / max(1, p0_1)
        impacto_abs = max(impacto_direito, impacto_esquerdo)
        
        bc_sarle = calc_bimodalidade_sarle(serie)
        
        serie_crise = X_crise[evento]
        if serie_crise.nunique() > 1:
            try:
                mi_condicionada = mutual_info_regression(serie_crise.values.reshape(-1, 1), y_crise, random_state=42)[0]
            except:
                mi_condicionada = 0.0
        else:
            mi_condicionada = 0.0
            
        resultados.append({
            'Evento': evento,
            'MI Global': mi_global_scores[idx],
            'Impacto Bilateral': impacto_abs,
            'Bimodal': bc_sarle,
            'MI P95': mi_condicionada,
            'Curtose': curtose_fisher,
            'Entropia': shannon,
            'Média': media,
            'CV': cv
        })
    
    df_res = pd.DataFrame(resultados)
    if not df_res.empty:
        # Normalização para Índice Global
        mi_min, mi_max = df_res['MI Global'].min(), df_res['MI Global'].max()
        df_res['Norm_MI'] = (df_res['MI Global'] - mi_min) / (mi_max - mi_min) if mi_max > mi_min else 0
        
        imp_min, imp_max = df_res['Impacto Bilateral'].min(), df_res['Impacto Bilateral'].max()
        df_res['Norm_Impacto'] = (df_res['Impacto Bilateral'] - imp_min) / (imp_max - imp_min) if imp_max > imp_min else 0
        
        df_res['Índice Global'] = (df_res['Norm_MI'] * 2) + df_res['Norm_Impacto']
        df_res = df_res.sort_values(by='Índice Global', ascending=False)
        
    return df_res

# --- Event Mapping (ARM Cortex-A53) ---
EVENT_GLOSSARY = {
    '0x00': {'Mnemonic': 'SW_INCR', 'Description': 'Software increment. O contador é incrementado apenas por escritas no registrador PMSWINC_EL0. Útil para marcar seções críticas ou eventos definidos pelo programador.'},
    '0x01': {'Mnemonic': 'L1I_CACHE_REFILL', 'Description': 'L1 Instruction cache refill. Miss na cache de instrução L1. A CPU busca a linha na L2 ou DRAM. Alta taxa indica baixa localidade de código (loops grandes ou chamadas dispersas).'},
    '0x02': {'Mnemonic': 'L1I_TLB_REFILL', 'Description': 'L1 Instruction TLB refill. Recarga do TLB de instruções L1 devido a miss no mapeamento virtual-físico. Comum após trocas de contexto ou código muito fragmentado.'},
    '0x03': {'Mnemonic': 'L1D_CACHE_REFILL', 'Description': 'L1 Data cache refill. Miss na cache de dados L1. O dado deve ser buscado na L2 ou RAM. Causa pipeline stall e indica padrões de acesso não sequenciais ou working set grande.'},
    '0x04': {'Mnemonic': 'L1D_CACHE', 'Description': 'L1 Data cache access. Conta todos os acessos (hits + misses) à cache L1D. Essencial para calcular a taxa de miss da cache de dados.'},
    '0x05': {'Mnemonic': 'L1D_TLB_REFILL', 'Description': 'L1 Data TLB refill. Miss no TLB de dados L1, forçando um page table walk. Indica que os dados estão espalhados por muitas páginas virtuais.'},
    '0x06': {'Mnemonic': 'LD_RETIRED', 'Description': 'Instruction architecturally executed, load. Instrução de carga (load) executada com sucesso. Mede a pressão de leitura de memória.'},
    '0x07': {'Mnemonic': 'ST_RETIRED', 'Description': 'Instruction architecturally executed, store. Instrução de escrita (store) executada. Razões altas podem indicar uso intenso de escrita ou MMIO.'},
    '0x08': {'Mnemonic': 'INST_RETIRED', 'Description': 'Instruction architecturally executed. Contador geral de instruções concluídas. Base para o cálculo de IPC (Instruções por Ciclo).'},
    '0x09': {'Mnemonic': 'EXC_TAKEN', 'Description': 'Exception taken. Total de exceções tomadas (IRQ, FIQ, page faults, SVC, etc.). Alta frequência indica excesso de interrupções ou chamadas de sistema.'},
    '0x0A': {'Mnemonic': 'EXC_RETURN', 'Description': 'Exception return. Execução da instrução de retorno de exceção (ERET).'},
    '0x0B': {'Mnemonic': 'CID_WRITE_RETIRED', 'Description': 'Change to Context ID retired. Escritas no registrador de ID de contexto, típicas de trocas de processos pelo SO.'},
    '0x0C': {'Mnemonic': 'PC_WRITE_RETIRED', 'Description': 'Software change of the PC. Mudanças de fluxo de controle via software (BR/BLR). Comum em dispatch tables e interpretadores.'},
    '0x0D': {'Mnemonic': 'BR_IMMED_RETIRED', 'Description': 'Immediate branch executed. Branches com alvo fixo na instrução (B, BL, CBZ) executados.'},
    '0x0E': {'Mnemonic': 'BR_RETURN_RETIRED', 'Description': 'Procedure return executed. Retornos de subrotina executados. O preditor usa o RAS (Return Address Stack) para este evento.'},
    '0x0F': {'Mnemonic': 'UNALIGNED_LDST_RETIRED', 'Description': 'Unaligned load or store. Acessos a endereços não alinhados. Causam penalidade de performance pois são divididos em múltiplas operações internas.'},
    '0x10': {'Mnemonic': 'BR_MIS_PRED', 'Description': 'Branch mispredicted. Branches malpreditos ou não preditos, resultando em descarte do pipeline e desperdício de ciclos (~8 ciclos no A53).'},
    '0x11': {'Mnemonic': 'CPU_CYCLES', 'Description': 'Cycle. Ciclos de clock do processador. Denominador base para quase todas as métricas de performance.'},
    '0x12': {'Mnemonic': 'BR_PRED', 'Description': 'Predictable branch speculatively executed. Branches predizíveis executados especulativamente.'},
    '0x13': {'Mnemonic': 'MEM_ACCESS', 'Description': 'Data memory access. Qualquer acesso que gere requisição à hierarquia de memória (L1, L2, DRAM).'},
    '0x14': {'Mnemonic': 'L1I_CACHE', 'Description': 'L1 Instruction cache access. Acessos totais à cache de instrução L1.'},
    '0x15': {'Mnemonic': 'L1D_CACHE_WB', 'Description': 'L1 Data cache Write-Back. Escrita de linhas sujas (dirty) da L1 para a L2. Indica thrashing da L1 ou alto volume de escritas.'},
    '0x16': {'Mnemonic': 'L2D_CACHE', 'Description': 'L2 Data cache access. Acessos à cache L2 unificada (dados e instruções).'},
    '0x17': {'Mnemonic': 'L2D_CACHE_REFILL', 'Description': 'L2 Data cache refill. Miss na cache L2 exigindo acesso à memória principal (DRAM). Evento de altíssima latência.'},
    '0x18': {'Mnemonic': 'L2D_CACHE_WB', 'Description': 'L2 Data cache Write-Back. Write-backs da L2 para a memória principal.'},
    '0x19': {'Mnemonic': 'BUS_ACCESS', 'Description': 'Bus access. Transações que saem do cluster para memória externa ou periféricos via barramento AXI/ACE.'},
    '0x1A': {'Mnemonic': 'MEMORY_ERROR', 'Description': 'Local memory error. Erros ECC nas caches. Indicador de falha de hardware ou interferência.'},
    '0x1D': {'Mnemonic': 'BUS_CYCLES', 'Description': 'Bus cycle. Ciclos do barramento de memória, útil para medir largura de banda efetiva.'},
    '0x1E': {'Mnemonic': 'CHAIN', 'Description': 'Odd performance counter chain mode. Encadeamento de contadores para formar um contador de 64 bits.'},
    '0x60': {'Mnemonic': 'BUS_ACCESS_LD', 'Description': 'Bus access - Read. Acessos de leitura ao barramento de memória.'},
    '0x61': {'Mnemonic': 'BUS_ACCESS_ST', 'Description': 'Bus access - Write. Acessos de escrita ao barramento de memória.'},
    '0x7A': {'Mnemonic': 'BR_INDIRECT_SPEC', 'Description': 'Branch speculatively executed - Indirect branch. Branches indiretos (alvo em registrador) executados especulativamente.'},
    '0x86': {'Mnemonic': 'EXC_IRQ', 'Description': 'Exception taken, IRQ. Interrupções de hardware de nível normal.'},
    '0x87': {'Mnemonic': 'EXC_FIQ', 'Description': 'Exception taken, FIQ. Interrupções de hardware de alta prioridade.'},
    '0xC0': {'Mnemonic': '-', 'Description': 'External memory request. Requisições enviadas para o controlador de memória externa (DRAM).'},
    '0xC1': {'Mnemonic': '-', 'Description': 'Non-cacheable external memory request. Acessos a memória não-cacheável (MMIO/Periféricos).'},
    '0xC2': {'Mnemonic': '-', 'Description': 'Linefill because of prefetch. Recargas de linha de cache disparadas pelo hardware prefetcher.'},
    '0xC3': {'Mnemonic': '-', 'Description': 'Instruction Cache Throttle occurred. Pausa no fetch de instruções por fila de decodificação cheia.'},
    '0xC4': {'Mnemonic': '-', 'Description': 'Entering read allocate mode. Transição para modo de alocação de leitura para evitar poluição da cache em streamings.'},
    '0xC5': {'Mnemonic': '-', 'Description': 'Read allocate mode. Ciclos operando em modo de alocação de leitura.'},
    '0xC6': {'Mnemonic': '-', 'Description': 'Pre-decode error. Erros de pré-decodificação na carga para L1I, forçando reinício do fetch.'},
    '0xC7': {'Mnemonic': '-', 'Description': 'Store buffer full stall. Pipeline parado porque o store buffer está cheio (alta pressão de escrita).'},
    '0xC8': {'Mnemonic': '-', 'Description': 'SCU Snooped data from another CPU. Dados obtidos da cache de outro núcleo via SCU (coerência de cache).'},
    '0xC9': {'Mnemonic': '-', 'Description': 'Conditional branch executed. Branches condicionais (B.EQ, B.NE, etc.) executados.'},
    '0xCA': {'Mnemonic': '-', 'Description': 'Indirect branch mispredicted. Erro de predição em branches indiretos (ponteiros de função/dispatch).'},
    '0xCB': {'Mnemonic': '-', 'Description': 'Indirect branch mispredicted - address miscompare. Misprediction por discordância de endereço no alvo predito.'},
    '0xCC': {'Mnemonic': '-', 'Description': 'Conditional branch mispredicted. Erro de predição em branches condicionais.'},
    '0xD0': {'Mnemonic': '-', 'Description': 'L1 Instruction Cache memory error. Erros ECC na cache de instrução L1.'},
    '0xD1': {'Mnemonic': '-', 'Description': 'L1 Data Cache memory error. Erros ECC na cache de dados L1.'},
    '0xD2': {'Mnemonic': '-', 'Description': 'TLB memory error. Erros ECC nas estruturas do TLB.'},
    '0xE0': {'Mnemonic': '-', 'Description': 'IQ empty - no identified stall cause. Frontend não fornece instruções por causa não categorizada.'},
    '0xE1': {'Mnemonic': '-', 'Description': 'IQ empty - instruction cache miss. Ciclos de stall esperando recarga da cache de instrução (L1I miss).'},
    '0xE2': {'Mnemonic': '-', 'Description': 'IQ empty - instruction TLB miss. Ciclos de stall esperando page table walk do TLB de instrução.'},
    '0xE3': {'Mnemonic': '-', 'Description': 'IQ empty - pre-decode error. Ciclos de stall devido a erros de pré-decodificação.'},
    '0xE4': {'Mnemonic': '-', 'Description': 'Interlock - not FP/SIMD or AGU. Stall por dependência de dados (RAW) em instruções inteiras.'},
    '0xE5': {'Mnemonic': '-', 'Description': 'Interlock - load/store AGU. Stall porque o cálculo do endereço depende de instrução anterior.'},
    '0xE6': {'Mnemonic': '-', 'Description': 'Interlock - Advanced SIMD or FP. Stall por dependência em instruções NEON ou Ponto Flutuante.'},
    '0xE7': {'Mnemonic': '-', 'Description': 'Wr stage stall - load miss. Ciclos em que o pipeline aguarda um load miss ser resolvido na L2/DRAM.'},
    '0xE8': {'Mnemonic': '-', 'Description': 'Wr stage stall - store. Stall no estágio de escrita, comumente por store buffer cheio.'},
}

# Transform glossary for DataTable
glossary_data = [{'Código': k, 'Mnemônico': v['Mnemonic'], 'Atividade/Descrição': v['Description']} for k, v in EVENT_GLOSSARY.items()]

# --- Dashboard Setup ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

BENCHMARKS = ['bs', 'cnt', 'fibcall_perf_ite', 'matmult', 'msort','complex','count_negative','cubic','dijkstra','md5','miner']
INTERVALS = ['intervalo1', 'intervalo2', 'intervalo3']

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1([
            "(STER) Real-Time Systems Research Group",
            html.Br(),
            "Dashboard de Análise de Eventos 📊"
        ], className="text-center my-4"), width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Label("Benchmark:"),
            dcc.Dropdown(id='benchmark-select', options=[{'label': b, 'value': b} for b in BENCHMARKS], value='bs')
        ], width=3),
        dbc.Col([
            html.Label("Intervalo:"),
            dcc.Dropdown(id='interval-select', options=[{'label': i, 'value': i} for i in INTERVALS], value='intervalo1')
        ], width=3),
        dbc.Col([
            html.Label("Arquivo:"),
            dcc.Dropdown(id='file-select')
        ], width=6),
    ], className="mb-4"),
    
    dcc.Loading(
        id="loading-content",
        type="circle",
        children=dbc.Tabs([
            dbc.Tab(label="Dados Brutos", children=[
                html.Div(id='raw-data-container', className="mt-3")
            ]),
            dbc.Tab(label="Métricas Consolidadas", children=[
                html.Div(id='metrics-container', className="mt-3")
            ]),
            dbc.Tab(label="Visualização Temporal", children=[
                html.Div([
                    html.Label("Selecione o Evento para o eixo X (Gráfico de Dispersão):"),
                    dcc.Dropdown(id='event-x-select', className="mb-2")
                ], className="mt-3"),
                dcc.Graph(id='time-series-plot', className="mt-3"),
                dcc.Graph(id='cycles-events-plot', className="mt-3")
            ]),
            dbc.Tab(label="Correlação", children=[
                dcc.Graph(id='correlation-heatmap', className="mt-3")
            ]),
            dbc.Tab(label="Glossário de Eventos", children=[
                html.Div([
                    html.H4("Referência de Eventos PMU (ARM Cortex-A53)", className="mb-3"),
                    dash_table.DataTable(
                        data=glossary_data,
                        columns=[{"name": i, "id": i} for i in ['Código', 'Mnemônico', 'Atividade/Descrição']],
                        filter_action="native",
                        sort_action="native",
                        page_size=20,
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'whiteSpace': 'normal',
                            'height': 'auto',
                        },
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        }
                    )
                ], className="mt-3")
            ]),
        ])
    )
], fluid=True)

@app.callback(
    Output('file-select', 'options'),
    Output('file-select', 'value'),
    Input('benchmark-select', 'value'),
    Input('interval-select', 'value')
)
def update_file_list(benchmark, interval):
    path = os.path.join(benchmark, interval, "*.csv")
    files = sorted(glob.glob(path))
    options = [{'label': os.path.basename(f), 'value': f} for f in files]
    value = files[0] if files else None
    return options, value

@app.callback(
    Output('event-x-select', 'options'),
    Output('event-x-select', 'value'),
    Input('file-select', 'value')
)
def update_event_options(file_path):
    if not file_path or not os.path.exists(file_path):
        return [], None
    try:
        df = pd.read_csv(file_path, sep=';', nrows=0)
        cols = [c.strip() for c in df.columns if c.strip() != 'CYCLES']
        options = [{'label': c, 'value': c} for c in cols]
        value = cols[0] if cols else None
        return options, value
    except:
        return [], None

@app.callback(
    Output('raw-data-container', 'children'),
    Output('metrics-container', 'children'),
    Output('time-series-plot', 'figure'),
    Output('cycles-events-plot', 'figure'),
    Output('correlation-heatmap', 'figure'),
    Input('file-select', 'value'),
    Input('event-x-select', 'value')
)
def update_content(file_path, selected_event):
    if not file_path or not os.path.exists(file_path):
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Sem dados")
        return "Selecione um arquivo", "Selecione um arquivo", empty_fig, empty_fig, empty_fig
    
    try:
        df = pd.read_csv(file_path, sep=';')
        df.columns = df.columns.str.strip()
    except Exception as e:
        return f"Erro ao ler arquivo: {e}", "", go.Figure(), go.Figure(), go.Figure()
    
    # Table Raw
    raw_table = dash_table.DataTable(
        data=df.head(100).to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'}
    )
    
    # Metrics
    df_metrics = calculate_metrics(df)
    if not df_metrics.empty:
        metrics_table = dash_table.DataTable(
            data=df_metrics.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_metrics.columns],
            sort_action="native",
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'}
        )
    else:
        metrics_table = "Erro ao calcular métricas ou coluna CYCLES ausente."
    
    # Time Series
    fig_ts = go.Figure()
    if 'CYCLES' in df.columns:
        fig_ts = px.line(df.reset_index(), x='index', y='CYCLES', title='Evolução de CYCLES')
        fig_ts.update_layout(xaxis_title="Amostra", yaxis_title="Cycles")
    else:
        fig_ts.update_layout(title="Coluna CYCLES não encontrada para visualização temporal")

    # Cycles vs Selected Event
    fig_ev = go.Figure()
    if 'CYCLES' in df.columns:
        df_num = df.apply(pd.to_numeric, errors='coerce').dropna()
        if not df_num.empty:
            if selected_event and selected_event in df_num.columns:
                fig_ev = px.scatter(df_num, x=selected_event, y='CYCLES', title=f'CYCLES vs {selected_event}')
                fig_ev.update_layout(xaxis_title=f"Número de Eventos ({selected_event})", yaxis_title="Cycles")
            else:
                fig_ev.update_layout(title="Selecione um evento válido para o eixo X")
        else:
            fig_ev.update_layout(title="Dados numéricos insuficientes")
    else:
        fig_ev.update_layout(title="Coluna CYCLES não encontrada")
    
    # Correlation
    try:
        df_num_corr = df.apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all').dropna()
        if not df_num_corr.empty and len(df_num_corr.columns) > 1:
            corr = df_num_corr.corr()
            fig_corr = px.imshow(corr, text_auto=".2f", aspect="auto", title="Matriz de Correlação")
        else:
            fig_corr = go.Figure()
            fig_corr.update_layout(title="Dados insuficientes para correlação")
    except:
        fig_corr = go.Figure()
        fig_corr.update_layout(title="Erro ao gerar matriz de correlação")
    
    return raw_table, metrics_table, fig_ts, fig_ev, fig_corr

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    print(f"Iniciando Dashboard na porta {port}...")
    app.run_server(debug=False, port=port, host='0.0.0.0')
