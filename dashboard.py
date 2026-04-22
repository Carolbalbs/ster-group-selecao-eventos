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
    '0x00': {'Mnemonic': 'SW_INCR', 'Description': 'Software increment. The register is incremented only on writes to the Software Increment Register.'},
    '0x01': {'Mnemonic': 'L1I_CACHE_REFILL', 'Description': 'L1 Instruction cache refill.'},
    '0x02': {'Mnemonic': 'L1I_TLB_REFILL', 'Description': 'L1 Instruction TLB refill.'},
    '0x03': {'Mnemonic': 'L1D_CACHE_REFILL', 'Description': 'L1 Data cache refill.'},
    '0x04': {'Mnemonic': 'L1D_CACHE', 'Description': 'L1 Data cache access.'},
    '0x05': {'Mnemonic': 'L1D_TLB_REFILL', 'Description': 'L1 Data TLB refill.'},
    '0x06': {'Mnemonic': 'LD_RETIRED', 'Description': 'Instruction architecturally executed, condition check pass - load.'},
    '0x07': {'Mnemonic': 'ST_RETIRED', 'Description': 'Instruction architecturally executed, condition check pass - store.'},
    '0x08': {'Mnemonic': 'INST_RETIRED', 'Description': 'Instruction architecturally executed.'},
    '0x09': {'Mnemonic': 'EXC_TAKEN', 'Description': 'Exception taken.'},
    '0x0A': {'Mnemonic': 'EXC_RETURN', 'Description': 'Exception return.'},
    '0x0B': {'Mnemonic': 'CID_WRITE_RETIRED', 'Description': 'Change to Context ID retired.'},
    '0x0C': {'Mnemonic': 'PC_WRITE_RETIRED', 'Description': 'Instruction architecturally executed, condition check pass, software change of the PC.'},
    '0x0D': {'Mnemonic': 'BR_IMMED_RETIRED', 'Description': 'Instruction architecturally executed, immediate branch.'},
    '0x0E': {'Mnemonic': 'BR_RETURN_RETIRED', 'Description': 'Instruction architecturally executed, condition code check pass, procedure return.'},
    '0x0F': {'Mnemonic': 'UNALIGNED_LDST_RETIRED', 'Description': 'Instruction architecturally executed, condition check pass, unaligned load or store.'},
    '0x10': {'Mnemonic': 'BR_MIS_PRED', 'Description': 'Mispredicted or not predicted branch speculatively executed.'},
    '0x11': {'Mnemonic': 'CPU_CYCLES', 'Description': 'Cycle.'},
    '0x12': {'Mnemonic': 'BR_PRED', 'Description': 'Predictable branch speculatively executed.'},
    '0x13': {'Mnemonic': 'MEM_ACCESS', 'Description': 'Data memory access.'},
    '0x14': {'Mnemonic': 'L1I_CACHE', 'Description': 'L1 Instruction cache access.'},
    '0x15': {'Mnemonic': 'L1D_CACHE_WB', 'Description': 'L1 Data cache Write-Back.'},
    '0x16': {'Mnemonic': 'L2D_CACHE', 'Description': 'L2 Data cache access.'},
    '0x17': {'Mnemonic': 'L2D_CACHE_REFILL', 'Description': 'L2 Data cache refill.'},
    '0x18': {'Mnemonic': 'L2D_CACHE_WB', 'Description': 'L2 Data cache Write-Back.'},
    '0x19': {'Mnemonic': 'BUS_ACCESS', 'Description': 'Bus access.'},
    '0x1A': {'Mnemonic': 'MEMORY_ERROR', 'Description': 'Local memory error.'},
    '0x1D': {'Mnemonic': 'BUS_CYCLES', 'Description': 'Bus cycle.'},
    '0x1E': {'Mnemonic': 'CHAIN', 'Description': 'Odd performance counter chain mode.'},
    '0x60': {'Mnemonic': 'BUS_ACCESS_LD', 'Description': 'Bus access - Read.'},
    '0x61': {'Mnemonic': 'BUS_ACCESS_ST', 'Description': 'Bus access - Write.'},
    '0x7A': {'Mnemonic': 'BR_INDIRECT_SPEC', 'Description': 'Branch speculatively executed - Indirect branch.'},
    '0x86': {'Mnemonic': 'EXC_IRQ', 'Description': 'Exception taken, IRQ.'},
    '0x87': {'Mnemonic': 'EXC_FIQ', 'Description': 'Exception taken, FIQ.'},
    '0xC0': {'Mnemonic': '-', 'Description': 'External memory request.'},
    '0xC1': {'Mnemonic': '-', 'Description': 'Non-cacheable external memory request.'},
    '0xC2': {'Mnemonic': '-', 'Description': 'Linefill because of prefetch.'},
    '0xC3': {'Mnemonic': '-', 'Description': 'Instruction Cache Throttle occurred.'},
    '0xC4': {'Mnemonic': '-', 'Description': 'Entering read allocate mode.'},
    '0xC5': {'Mnemonic': '-', 'Description': 'Read allocate mode.'},
    '0xC6': {'Mnemonic': '-', 'Description': 'Pre-decode error.'},
    '0xC7': {'Mnemonic': '-', 'Description': 'Data Write operation that stalls the pipeline because the store buffer is full.'},
    '0xC8': {'Mnemonic': '-', 'Description': 'SCU Snooped data from another CPU for this CPU.'},
    '0xC9': {'Mnemonic': '-', 'Description': 'Conditional branch executed.'},
    '0xCA': {'Mnemonic': '-', 'Description': 'Indirect branch mispredicted.'},
    '0xCB': {'Mnemonic': '-', 'Description': 'Indirect branch mispredicted because of address miscompare.'},
    '0xCC': {'Mnemonic': '-', 'Description': 'Conditional branch mispredicted.'},
    '0xD0': {'Mnemonic': '-', 'Description': 'L1 Instruction Cache (data or tag) memory error.'},
    '0xD1': {'Mnemonic': '-', 'Description': 'L1 Data Cache (data, tag or dirty) memory error.'},
    '0xD2': {'Mnemonic': '-', 'Description': 'TLB memory error.'},
}

# Transform glossary for DataTable
glossary_data = [{'Código': k, 'Mnemônico': v['Mnemonic'], 'Atividade/Descrição': v['Description']} for k, v in EVENT_GLOSSARY.items()]

# --- Dashboard Setup ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

BENCHMARKS = ['bs', 'cnt', 'fibcall_perf_ite', 'matmult', 'msort']
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
                dcc.Graph(id='time-series-plot', className="mt-3")
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
    Output('raw-data-container', 'children'),
    Output('metrics-container', 'children'),
    Output('time-series-plot', 'figure'),
    Output('correlation-heatmap', 'figure'),
    Input('file-select', 'value')
)
def update_content(file_path):
    if not file_path or not os.path.exists(file_path):
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Sem dados")
        return "Selecione um arquivo", "Selecione um arquivo", empty_fig, empty_fig
    
    try:
        df = pd.read_csv(file_path, sep=';')
        df.columns = df.columns.str.strip()
    except Exception as e:
        return f"Erro ao ler arquivo: {e}", "", go.Figure(), go.Figure()
    
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
    
    # Correlation
    try:
        df_num = df.apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all').dropna()
        if not df_num.empty and len(df_num.columns) > 1:
            corr = df_num.corr()
            fig_corr = px.imshow(corr, text_auto=".2f", aspect="auto", title="Matriz de Correlação")
        else:
            fig_corr = go.Figure()
            fig_corr.update_layout(title="Dados insuficientes para correlação")
    except:
        fig_corr = go.Figure()
        fig_corr.update_layout(title="Erro ao gerar matriz de correlação")
    
    return raw_table, metrics_table, fig_ts, fig_corr

if __name__ == '__main__':
    print("Iniciando Dashboard na porta 8050...")
    app.run(debug=False, port=8050, host='0.0.0.0')
