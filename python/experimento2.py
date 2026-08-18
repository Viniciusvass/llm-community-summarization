import mysql.connector
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from bert_score import score as bert_score
from scipy.stats import friedmanchisquare

DB_CONFIG = {
    "host": "BD_HOST",
    "user": "BD_USER",
    "password": "BD_PASSWORD",
    "database": "BD_DATABASE"
}

FONTE_TERMOS = "TESE"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LIMPAR_TABELA = True

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

if LIMPAR_TABELA:
    cursor.execute("TRUNCATE TABLE avaliacoes3;")
    conn.commit()

print("Carregando modelo de embeddings...")
model = SentenceTransformer(MODEL_NAME)

query_gabaritos = """
SELECT comunidade, gabarito, tempo_ms
FROM gabaritos2
WHERE llm = 'gpt-oss-120b-turbo';
"""

cursor.execute(query_gabaritos)
gabaritos = cursor.fetchall()

mapa_gabaritos = {
    g["comunidade"]: {
        "texto": g["gabarito"],
        "tempo_ms": g["tempo_ms"]
    }
    for g in gabaritos
}

query_sumarios = """
SELECT
    llm,
    comunidade,
    metodo,
    medida,
    centralidade,
    sumario,
    tempo_ms,
    fonte_termos
FROM sumarizacoes4
WHERE fonte_termos = %s
  AND metodo = 'CGBD'
  AND centralidade IS NOT NULL
  AND llm IN ('gpt-oss-120b-turbo', 'llama3.2', 'gemma3:1b', 'qwen3.5:2b')
ORDER BY comunidade, medida, centralidade, llm;
"""

cursor.execute(query_sumarios, (FONTE_TERMOS,))
sumarios = cursor.fetchall()

insert_sql = """
INSERT INTO avaliacoes3 (
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
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""

resultados_friedman = []
total = 0

for s in sumarios:
    comunidade = s["comunidade"]

    if comunidade not in mapa_gabaritos:
        continue

    gabarito = mapa_gabaritos[comunidade]["texto"]
    tempo_gabarito = mapa_gabaritos[comunidade]["tempo_ms"]
    sumario = s["sumario"]

    if sumario is None or str(sumario).strip() == "":
        continue

    llm_comparado = s["llm"]
    cenario = "gpt-oss-120b-turboxgpt-oss-120b-turbo" if llm_comparado == "gpt-oss-120b-turbo" else f"gpt-oss-120b-turbox{llm_comparado}"

    embeddings = model.encode(
        [gabarito, sumario],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    cosine = cosine_similarity(
        embeddings[0].reshape(1, -1),
        embeddings[1].reshape(1, -1)
    )[0][0]

    dissimilaridade = 1 - float(cosine)

    P, R, F1 = bert_score(
        [sumario],
        [gabarito],
        lang="en",
        verbose=False
    )

    bert_precision = P.mean().item()
    bert_recall = R.mean().item()
    bert_f1 = F1.mean().item()

    tempo_sumario = s["tempo_ms"]
    tempo_economizado = tempo_gabarito - tempo_sumario

    resultados_friedman.append({
        "comunidade": comunidade,
        "medida": s["medida"],
        "centralidade": s["centralidade"],
        "llm": llm_comparado,
        "bert_f1": float(bert_f1)
    })

    cursor.execute(
        insert_sql,
        (
            cenario,
            "gpt-oss-120b-turbo",
            llm_comparado,
            comunidade,
            s["metodo"],
            s["medida"],
            s["centralidade"],
            s["fonte_termos"],
            float(cosine),
            float(dissimilaridade),
            float(bert_precision),
            float(bert_recall),
            float(bert_f1),
            int(tempo_sumario),
            int(tempo_gabarito),
            int(tempo_economizado)
        )
    )

    total += 1

    print(
        f"{cenario} | Comunidade {comunidade} | "
        f"{s['medida']} | {s['centralidade']} | "
        f"Cosine={cosine:.4f} | BERT-F1={bert_f1:.4f} | "
        f"Tempo economizado={tempo_economizado} ms"
    )

conn.commit()

df_friedman = pd.DataFrame(resultados_friedman)
df_friedman = df_friedman[df_friedman["llm"] != "gpt-oss-120b-turbo"]

pivot = df_friedman.pivot_table(
    index=["comunidade", "medida", "centralidade"],
    columns="llm",
    values="bert_f1",
    aggfunc="mean"
).dropna()

print("\n=========================")
print("TESTE DE FRIEDMAN - BERT-F1")
print("=========================")

print(f"Blocos usados no Friedman: {pivot.shape[0]}")
print(f"Modelos comparados: {list(pivot.columns)}")

if pivot.shape[0] >= 2 and pivot.shape[1] >= 3:
    estatistica, p_valor = friedmanchisquare(
        *[pivot[col] for col in pivot.columns]
    )

    print(f"Estatística Friedman: {estatistica:.4f}")
    print(f"P-valor: {p_valor:.6f}")

    rankings = pivot.rank(axis=1, ascending=False, method="average")
    ranking_medio = rankings.mean().sort_values()

    print("\nRanking médio dos modelos:")
    print(ranking_medio)

    if p_valor < 0.05:
        print("Resultado: diferença estatisticamente significativa entre os modelos.")
    else:
        print("Resultado: não há diferença estatisticamente significativa entre os modelos.")
else:
    print("Dados insuficientes para aplicar Friedman.")

cursor.close()
conn.close()

print(f"\nExperimento finalizado.")
print(f"Total de avaliações salvas: {total}")
