import pandas as pd
import numpy as np
from sklearn.feature_selection import mutual_info_regression
from scipy.stats import entropy, skew, kurtosis
import os
import glob

# =====================================================================
# CONFIGURAÇÕES
# =====================================================================

PASTA_DADOS = './msort/msort_perf/n_eventos/repeticao3/' # Coloque aqui os seus 10 ficheiros CSV originais do msort
PASTA_RESULTADOS = './msort/msort_perf/n_eventos/repeticao3/estudo_metricas'

if not os.path.exists(PASTA_RESULTADOS):
    os.makedirs(PASTA_RESULTADOS)

arquivos_csv = glob.glob(os.path.join(PASTA_DADOS, '*.csv'))

if not arquivos_csv:
    print(f"Nenhum ficheiro CSV encontrado na pasta '{PASTA_DADOS}'.")
    exit()

print(f"Iniciando Explorador de Métricas (Consolidado na Base 2 com Impacto Bilateral): {len(arquivos_csv)} ficheiro(s) encontrados.\n")

resultados = []

# =====================================================================
# FUNÇÕES MATEMÁTICAS AVANÇADAS
# =====================================================================
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

# =====================================================================
# PROCESSAMENTO DE DADOS (CÁLCULO BRUTO)
# =====================================================================
for file_path in arquivos_csv:
    nome_arquivo = os.path.basename(file_path)
    print(f"A processar: {nome_arquivo}...")
    
    df = pd.read_csv(file_path, sep=';')
    df.columns = df.columns.str.strip()
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    
    if 'CYCLES' not in df.columns:
        continue
        
    y_target = df['CYCLES']
    X_raw = df.drop(columns=['CYCLES'])
    
    limiar_crise = y_target.quantile(0.95)
    mask_crise = y_target >= limiar_crise
    y_crise = y_target[mask_crise]
    X_crise = X_raw[mask_crise]
    
    # MI Global
    mi_global_scores = mutual_info_regression(X_raw, y_target, random_state=42)
    
    for idx, evento in enumerate(X_raw.columns):
        serie = X_raw[evento]
        
        media = serie.mean()
        cv = (serie.std() / media) if media != 0 else 0
        curtose_fisher = serie.kurtosis()
        shannon = calc_entropia_shannon(serie)
        
        # =============================================================
        # ALTERNATIVA A: IMPACTO BILATERAL SIMÉTRICO (max(D, E))
        # =============================================================
        p50 = serie.median()
        p99_9 = serie.quantile(0.999)
        p0_1 = serie.quantile(0.001)
        
        # Impacto Direito (Picos por Excesso de Erros / Gargalos)
        impacto_direito = (p99_9 - p50) / max(1, p50)
        
        # Impacto Esquerdo (Quedas Abruptas por Subnutrição / Starvation)
        impacto_esquerdo = (p50 - p0_1) / max(1, p0_1)
        
        # O Impacto Absoluto é a maior disrupção registada (seja falta ou excesso)
        impacto_abs = max(impacto_direito, impacto_esquerdo)
        # =============================================================
        
        # Alternativa B e C
        bc_sarle = calc_bimodalidade_sarle(serie)
        serie_crise = X_crise[evento]
        if serie_crise.nunique() > 1:
            mi_condicionada = mutual_info_regression(serie_crise.values.reshape(-1, 1), y_crise, random_state=42)[0]
        else:
            mi_condicionada = 0.0
            
        resultados.append({
            'Evento': evento,
            'Ficheiro': nome_arquivo[:20] + '...',
            'MI Global': mi_global_scores[idx],
            'Alt A (Impacto Bilateral)': impacto_abs,
            'Alt B (Bimodal)': bc_sarle,
            'Alt C (MI P95)': mi_condicionada,
            'Curtose': curtose_fisher,
            'Entropia': shannon
        })

# =====================================================================
# FUSÃO: O ÍNDICE DEFINITIVO (BASE 2)
# =====================================================================
df_res = pd.DataFrame(resultados)

# 1. Normalização Min-Max da MI Global (Escala 0 a 1)
mi_min, mi_max = df_res['MI Global'].min(), df_res['MI Global'].max()
df_res['Norm_MI'] = (df_res['MI Global'] - mi_min) / (mi_max - mi_min) if mi_max > mi_min else 0

# 2. Normalização Min-Max do Impacto Bilateral Absoluto (Escala 0 a 1)
imp_min, imp_max = df_res['Alt A (Impacto Bilateral)'].min(), df_res['Alt A (Impacto Bilateral)'].max()
df_res['Norm_Impacto'] = (df_res['Alt A (Impacto Bilateral)'] - imp_min) / (imp_max - imp_min) if imp_max > imp_min else 0

# 3. O Índice Base 2 (A Escolha Metodológica)
# Confere o dobro da importância à correlação temporal, mas permite ultrapassagens 
# em caso de eventos com Impacto Bilateral excecional (Picos Absurdos ou Quedas Abruptas).
df_res['Índice Global (Base 2)'] = (df_res['Norm_MI'] * 2) + df_res['Norm_Impacto']

# =====================================================================
# LIMPEZA, ORDENAÇÃO E EXPORTAÇÃO
# =====================================================================
colunas_arredondar = ['MI Global', 'Alt A (Impacto Bilateral)', 'Norm_MI', 'Norm_Impacto', 'Índice Global (Base 2)']
df_res[colunas_arredondar] = df_res[colunas_arredondar].round(4)

# Ordenação pelo Índice Base 2 (A decisão arquitetural final)
df_res = df_res.sort_values(by='Índice Global (Base 2)', ascending=False)

caminho_excel = os.path.join(PASTA_RESULTADOS, 'tabela_metricas_base.xlsx')
try:
    with pd.ExcelWriter(caminho_excel, engine='openpyxl') as writer:
        df_res.to_excel(writer, sheet_name='Análise Consolidada', index=False)
    print(f"\n[SUCESSO] Tabela gerada! Abra o ficheiro: {caminho_excel}")
except ModuleNotFoundError:
    caminho_csv = os.path.join(PASTA_RESULTADOS, 'tabela_metricas_base.csv')
    df_res.to_csv(caminho_csv, index=False, sep=';', decimal=',')
    print(f"\n[SUCESSO] Pacote excel não encontrado. CSV gerado: {caminho_csv}")

print("-> A tabela foi ordenada utilizando o Índice Global (Base 2) sugerido.")
print("-> Este índice inclui agora a fórmula de Impacto Bilateral, cobrindo Picos de Erro e Quedas de Produtividade.")