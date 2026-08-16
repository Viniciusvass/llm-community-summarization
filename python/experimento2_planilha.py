import mysql.connector
import pandas as pd
from scipy.stats import friedmanchisquare

DB_CONFIG = {
    "host": "BD_HOST",
    "user": "BD_USER",
    "password": "BD_PASSWORD",
    "database": "BD_DATABASE"
}

ARQUIVO_SAIDA = "experimento_2_avaliacao_qualidade.xlsx"

conn = mysql.connector.connect(**DB_CONFIG)

query = """
SELECT
    cenario,
    llm_base,
    llm_comparado,
    comunidade,
    metodo,
    medida,
    centralidade,
    fonte_termos,
    cosine_similarity,
    dissimilaridade,
    bert_precision,
    bert_recall,
    bert_f1,
    tempo_ms,
    tempo_gabarito_ms,
    tempo_economizado_ms
FROM avaliacoes3
ORDER BY
    llm_comparado,
    comunidade,
    medida,
    centralidade;
"""

df = pd.read_sql(query, conn)
conn.close()

melhor_por_comunidade = (
    df.sort_values(
        ["llm_comparado", "comunidade", "bert_f1"],
        ascending=[True, True, False]
    )
    .groupby(["llm_comparado", "comunidade"])
    .head(1)
)

media_modelo = df.groupby(
    ["llm_comparado"],
    as_index=False
).agg(
    similaridade_media=("cosine_similarity", "mean"),
    dissimilaridade_media=("dissimilaridade", "mean"),
    bert_precision_medio=("bert_precision", "mean"),
    bert_recall_medio=("bert_recall", "mean"),
    bert_f1_medio=("bert_f1", "mean"),
    tempo_medio_ms=("tempo_ms", "mean"),
    tempo_gabarito_medio_ms=("tempo_gabarito_ms", "mean"),
    tempo_economizado_medio_ms=("tempo_economizado_ms", "mean")
)

media_modelo["ranking_qualidade"] = media_modelo["bert_f1_medio"] \
    .rank(ascending=False, method="dense")

media_centralidade = df.groupby(
    ["llm_comparado", "centralidade"],
    as_index=False
).agg(
    similaridade_media=("cosine_similarity", "mean"),
    dissimilaridade_media=("dissimilaridade", "mean"),
    bert_f1_medio=("bert_f1", "mean"),
    tempo_medio_ms=("tempo_ms", "mean"),
    tempo_economizado_medio_ms=("tempo_economizado_ms", "mean")
)

media_centralidade["ranking_qualidade"] = media_centralidade.groupby(
    "llm_comparado"
)["bert_f1_medio"].rank(ascending=False, method="dense")

media_medida = df.groupby(
    ["llm_comparado", "medida"],
    as_index=False
).agg(
    similaridade_media=("cosine_similarity", "mean"),
    dissimilaridade_media=("dissimilaridade", "mean"),
    bert_f1_medio=("bert_f1", "mean"),
    tempo_medio_ms=("tempo_ms", "mean"),
    tempo_economizado_medio_ms=("tempo_economizado_ms", "mean")
)

media_medida["ranking_qualidade"] = media_medida.groupby(
    "llm_comparado"
)["bert_f1_medio"].rank(ascending=False, method="dense")

media_medida_centralidade = df.groupby(
    ["llm_comparado", "medida", "centralidade"],
    as_index=False
).agg(
    similaridade_media=("cosine_similarity", "mean"),
    dissimilaridade_media=("dissimilaridade", "mean"),
    bert_f1_medio=("bert_f1", "mean"),
    tempo_medio_ms=("tempo_ms", "mean"),
    tempo_economizado_medio_ms=("tempo_economizado_ms", "mean")
)

media_medida_centralidade["ranking_qualidade"] = media_medida_centralidade.groupby(
    "llm_comparado"
)["bert_f1_medio"].rank(ascending=False, method="dense")

tempo_modelo = df.groupby(
    ["llm_comparado"],
    as_index=False
).agg(
    tempo_medio_ms=("tempo_ms", "mean"),
    tempo_minimo_ms=("tempo_ms", "min"),
    tempo_maximo_ms=("tempo_ms", "max"),
    tempo_gabarito_medio_ms=("tempo_gabarito_ms", "mean"),
    tempo_economizado_medio_ms=("tempo_economizado_ms", "mean")
)

tempo_modelo["tempo_medio_s"] = tempo_modelo["tempo_medio_ms"] / 1000
tempo_modelo["tempo_economizado_medio_s"] = tempo_modelo["tempo_economizado_medio_ms"] / 1000

df_friedman = df[df["llm_comparado"] != "gpt-oss-120b-turbo"]

pivot_friedman = df_friedman.pivot_table(
    index=["comunidade", "medida", "centralidade"],
    columns="llm_comparado",
    values="bert_f1",
    aggfunc="mean"
).dropna()

friedman_resultado = []

if pivot_friedman.shape[0] >= 2 and pivot_friedman.shape[1] >= 3:
    estatistica, p_valor = friedmanchisquare(
        *[pivot_friedman[col] for col in pivot_friedman.columns]
    )

    rankings = pivot_friedman.rank(axis=1, ascending=False, method="average")
    ranking_medio = rankings.mean().sort_values()

    linha = {
        "metrica": "BERT-F1",
        "comparacao": "Modelos open-source",
        "observacao": "GPT excluído por ser usado como baseline/gabarito",
        "blocos_utilizados": pivot_friedman.shape[0],
        "modelos_comparados": ", ".join(pivot_friedman.columns),
        "estatistica_friedman": estatistica,
        "p_value": p_valor,
        "significativo_0_05": "SIM" if p_valor < 0.05 else "NÃO"
    }

    for modelo, rank in ranking_medio.items():
        linha[f"ranking_medio_{modelo}"] = rank

    friedman_resultado.append(linha)

friedman_df = pd.DataFrame(friedman_resultado)

descricao_abas = pd.DataFrame([
    {"Aba": "Dados_Brutos", "Descrição": "Todas as avaliações individuais entre gabarito GPT e sumarizações."},
    {"Aba": "Melhor_por_Comunidade", "Descrição": "Melhor sumarização de cada comunidade para cada modelo, usando BERT-F1."},
    {"Aba": "Media_Modelo", "Descrição": "Desempenho médio de cada modelo: similaridade, BERT-F1 e tempo."},
    {"Aba": "Media_Centralidade", "Descrição": "Desempenho médio de cada centralidade dentro de cada modelo."},
    {"Aba": "Media_Medida", "Descrição": "Desempenho médio de cada medida de seleção de termos dentro de cada modelo."},
    {"Aba": "Media_Medida_Central", "Descrição": "Desempenho médio da combinação medida + centralidade para cada modelo."},
    {"Aba": "Tempo_Modelo", "Descrição": "Tempo médio, mínimo, máximo e tempo economizado por modelo."},
    {"Aba": "Friedman_BERT", "Descrição": "Teste de Friedman sobre BERT-F1 entre modelos open-source, excluindo GPT."}
])

with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl") as writer:
    descricao_abas.to_excel(writer, sheet_name="Descricao_Abas", index=False)
    df.to_excel(writer, sheet_name="Dados_Brutos", index=False)
    melhor_por_comunidade.to_excel(writer, sheet_name="Melhor_por_Comunidade", index=False)
    media_modelo.to_excel(writer, sheet_name="Media_Modelo", index=False)
    media_centralidade.to_excel(writer, sheet_name="Media_Centralidade", index=False)
    media_medida.to_excel(writer, sheet_name="Media_Medida", index=False)
    media_medida_centralidade.to_excel(writer, sheet_name="Media_Medida_Central", index=False)
    tempo_modelo.to_excel(writer, sheet_name="Tempo_Modelo", index=False)
    friedman_df.to_excel(writer, sheet_name="Friedman_BERT", index=False)

print(f"Planilha gerada com sucesso: {ARQUIVO_SAIDA}")