import mysql.connector
import pandas as pd

DB_CONFIG = {
    "host": "BD_HOST",
    "user": "BD_USER",
    "password": "BD_PASSWORD",
    "database": "BD_DATABASE"
}

ARQUIVO_SAIDA = "experimento_1_similaridade_perfis_organizado.xlsx"

conn = mysql.connector.connect(**DB_CONFIG)

query = """
SELECT
    cenario,
    tipo_comparacao,
    fonte_termos,
    comunidade,

    llm_a,
    abordagem_a,
    medida_a,
    centralidade_a,
    tempo_a_ms,

    llm_b,
    abordagem_b,
    medida_b,
    centralidade_b,
    tempo_b_ms,

    cosine_similarity,
    dissimilaridade

FROM similaridade_perfis

WHERE abordagem_a != 'CGBA'
  AND abordagem_b != 'CGBA'
  AND centralidade_a IS NOT NULL
  AND centralidade_b IS NOT NULL

ORDER BY
    cenario,
    comunidade,
    cosine_similarity DESC;
"""

df = pd.read_sql(query, conn)
conn.close()

df["perfil_a"] = (
    df["llm_a"].astype(str) + " | " +
    df["abordagem_a"].astype(str) + " | " +
    df["medida_a"].astype(str) + " | " +
    df["centralidade_a"].astype(str)
)

df["perfil_b"] = (
    df["llm_b"].astype(str) + " | " +
    df["abordagem_b"].astype(str) + " | " +
    df["medida_b"].astype(str) + " | " +
    df["centralidade_b"].astype(str)
)

# =========================
# DESCRIÇÃO DAS ABAS
# =========================

descricao_abas = pd.DataFrame([
    {
        "Aba": "Dados_Brutos",
        "Descrição": "Contém todas as comparações de similaridade e dissimilaridade entre perfis gerados."
    },
    {
        "Aba": "Resumo_Comparacoes",
        "Descrição": "Mostra a similaridade média entre pares de perfis considerando todos os cenários."
    },
    {
        "Aba": "Mais_Similares",
        "Descrição": "Mostra, para cada comunidade e cenário, o par de perfis mais semelhante."
    },
    {
        "Aba": "Mais_Dissimilares",
        "Descrição": "Mostra, para cada comunidade e cenário, o par de perfis mais diferente."
    },
    {
        "Aba": "Perfil_Representativo",
        "Descrição": "Indica o perfil mais representativo de cada comunidade, considerando a maior similaridade média com os demais."
    },
    {
        "Aba": "Mesmo_Metodo_Varia_Central",
        "Descrição": "Compara perfis com mesma abordagem e mesma medida, variando apenas a centralidade."
    },
    {
        "Aba": "Resumo_Varia_Central",
        "Descrição": "Resume a similaridade média entre pares de centralidades para cada cenário, abordagem e medida."
    },
    {
        "Aba": "Resumo_Modelos",
        "Descrição": "Resume a similaridade média entre pares de modelos."
    }
])

# =========================
# DADOS BRUTOS
# =========================

dados_brutos = df[[
    "cenario",
    "tipo_comparacao",
    "fonte_termos",
    "comunidade",

    "llm_a",
    "llm_b",

    "perfil_a",
    "perfil_b",

    "tempo_a_ms",
    "tempo_b_ms",

    "cosine_similarity",
    "dissimilaridade"
]].copy()

dados_brutos = dados_brutos.rename(columns={
    "comunidade": "comunidade_comparada",
    "perfil_a": "perfil_1",
    "perfil_b": "perfil_2",
    "cosine_similarity": "similaridade"
})

# =========================
# RESUMO COMPARAÇÕES
# =========================

resumo_comparacoes = (
    df.groupby(
        [
            "cenario",
            "llm_a",
            "llm_b",
            "perfil_a",
            "perfil_b"
        ],
        as_index=False
    )
    .agg(
        similaridade_media=("cosine_similarity", "mean"),
        dissimilaridade_media=("dissimilaridade", "mean"),
        qtd_comunidades=("comunidade", "nunique")
    )
)

# =========================
# RESUMO POR MODELOS
# =========================

resumo_modelos = (
    df.groupby(
        [
            "cenario",
            "llm_a",
            "llm_b",
            "tipo_comparacao"
        ],
        as_index=False
    )
    .agg(
        similaridade_media=("cosine_similarity", "mean"),
        dissimilaridade_media=("dissimilaridade", "mean"),
        qtd_comparacoes=("cosine_similarity", "count"),
        qtd_comunidades=("comunidade", "nunique")
    )
)

# =========================
# MAIS SIMILARES
# =========================

mais_similares = (
    df.sort_values(
        ["cenario", "comunidade", "cosine_similarity"],
        ascending=[True, True, False]
    )
    .groupby(["cenario", "comunidade"])
    .head(1)
)

mais_similares = mais_similares[[
    "cenario",
    "comunidade",
    "llm_a",
    "llm_b",
    "perfil_a",
    "perfil_b",
    "cosine_similarity",
    "dissimilaridade"
]].rename(columns={
    "comunidade": "comunidade_comparada",
    "perfil_a": "perfil_1",
    "perfil_b": "perfil_2",
    "cosine_similarity": "maior_similaridade"
})

# =========================
# MAIS DISSIMILARES
# =========================

mais_dissimilares = (
    df.sort_values(
        ["cenario", "comunidade", "dissimilaridade"],
        ascending=[True, True, False]
    )
    .groupby(["cenario", "comunidade"])
    .head(1)
)

mais_dissimilares = mais_dissimilares[[
    "cenario",
    "comunidade",
    "llm_a",
    "llm_b",
    "perfil_a",
    "perfil_b",
    "cosine_similarity",
    "dissimilaridade"
]].rename(columns={
    "comunidade": "comunidade_comparada",
    "perfil_a": "perfil_1",
    "perfil_b": "perfil_2",
    "dissimilaridade": "maior_dissimilaridade"
})

# =========================
# PERFIL REPRESENTATIVO
# =========================

df_a = df[[
    "cenario",
    "comunidade",
    "llm_a",
    "perfil_a",
    "cosine_similarity"
]].rename(columns={
    "llm_a": "llm",
    "perfil_a": "perfil"
})

df_b = df[[
    "cenario",
    "comunidade",
    "llm_b",
    "perfil_b",
    "cosine_similarity"
]].rename(columns={
    "llm_b": "llm",
    "perfil_b": "perfil"
})

df_perfis = pd.concat([df_a, df_b], ignore_index=True)

perfil_representativo = (
    df_perfis.groupby(
        [
            "cenario",
            "comunidade",
            "llm",
            "perfil"
        ],
        as_index=False
    )
    .agg(
        similaridade_media_com_outros=("cosine_similarity", "mean")
    )
)

perfil_representativo = (
    perfil_representativo
    .sort_values(
        ["cenario", "comunidade", "similaridade_media_com_outros"],
        ascending=[True, True, False]
    )
    .groupby(["cenario", "comunidade"])
    .head(1)
)

perfil_representativo = perfil_representativo.rename(columns={
    "comunidade": "comunidade_comparada"
})

# =========================
# MESMO MÉTODO VARIANDO CENTRALIDADE
# =========================

mesmo_metodo_variando_centralidade = df[
    (df["abordagem_a"] == df["abordagem_b"]) &
    (df["medida_a"] == df["medida_b"]) &
    (df["centralidade_a"] != df["centralidade_b"])
].copy()

mesmo_metodo_variando_centralidade = mesmo_metodo_variando_centralidade[[
    "cenario",
    "comunidade",

    "llm_a",
    "llm_b",

    "abordagem_a",
    "medida_a",

    "centralidade_a",
    "centralidade_b",

    "cosine_similarity",
    "dissimilaridade"
]].rename(columns={
    "comunidade": "comunidade_comparada",
    "abordagem_a": "abordagem",
    "medida_a": "medida",
    "centralidade_a": "centralidade_1",
    "centralidade_b": "centralidade_2",
    "cosine_similarity": "similaridade"
})

# =========================
# RESUMO VARIANDO CENTRALIDADE
# =========================

resumo_variando_centralidade = (
    mesmo_metodo_variando_centralidade.groupby(
        [
            "cenario",
            "llm_a",
            "llm_b",
            "abordagem",
            "medida",
            "centralidade_1",
            "centralidade_2"
        ],
        as_index=False
    )
    .agg(
        similaridade_media=("similaridade", "mean"),
        dissimilaridade_media=("dissimilaridade", "mean"),
        qtd_comunidades=("comunidade_comparada", "nunique")
    )
)

# =========================
# GERAR EXCEL
# =========================

with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl") as writer:

    descricao_abas.to_excel(writer, sheet_name="Descricao_Abas", index=False)
    dados_brutos.to_excel(writer, sheet_name="Dados_Brutos", index=False)
    resumo_comparacoes.to_excel(writer, sheet_name="Resumo_Comparacoes", index=False)
    resumo_modelos.to_excel(writer, sheet_name="Resumo_Modelos", index=False)
    mais_similares.to_excel(writer, sheet_name="Mais_Similares", index=False)
    mais_dissimilares.to_excel(writer, sheet_name="Mais_Dissimilares", index=False)
    perfil_representativo.to_excel(writer, sheet_name="Perfil_Representativo", index=False)
    mesmo_metodo_variando_centralidade.to_excel(writer, sheet_name="Mesmo_Metodo_Varia_Central", index=False)
    resumo_variando_centralidade.to_excel(writer, sheet_name="Resumo_Varia_Central", index=False)

print(f"Planilha gerada com sucesso: {ARQUIVO_SAIDA}")