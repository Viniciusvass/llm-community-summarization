import mysql.connector
from itertools import combinations
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# =========================
# CONFIGURAÇÕES
# =========================

DB_CONFIG = {
    "host": "BD_HOST",
    "user": "BD_USER",
    "password": "BD_PASSWORD",
    "database": "BD_DATABASE"
}

FONTE_TERMOS = "TESE"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LIMPAR_TABELA = True

MODELOS = [
    "gemma3:1b",
    "llama3.2",
    "qwen3.5:2b",
    "gpt-oss-120b-turbo"
]

# =========================
# CONEXÃO
# =========================

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

if LIMPAR_TABELA:
    cursor.execute("TRUNCATE TABLE similaridade_perfis;")
    conn.commit()

# =========================
# MODELO DE EMBEDDINGS
# =========================

print("Carregando modelo de embeddings...")
model = SentenceTransformer(MODEL_NAME)

# =========================
# FUNÇÕES
# =========================

def buscar_sumarios(llm):
    query = """
    SELECT
        llm,
        comunidade,
        metodo AS abordagem,
        medida,
        centralidade,
        sumario,
        tempo_ms
    FROM sumarizacoes4
    WHERE fonte_termos = %s
      AND llm = %s
      AND sumario IS NOT NULL
      AND TRIM(sumario) <> ''
    ORDER BY comunidade, metodo, medida, centralidade;
    """
    cursor.execute(query, (FONTE_TERMOS, llm))
    return cursor.fetchall()


def chave_perfil(p):
    return (
        p["comunidade"],
        p["abordagem"],
        p["medida"],
        p["centralidade"]
    )


def inserir_resultado(cenario, tipo, a, b, cosine):
    sql = """
    INSERT INTO similaridade_perfis (
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
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (
        cenario,
        tipo,
        FONTE_TERMOS,
        a["comunidade"],

        a["llm"],
        a["abordagem"],
        a["medida"],
        a["centralidade"],
        a["tempo_ms"],

        b["llm"],
        b["abordagem"],
        b["medida"],
        b["centralidade"],
        b["tempo_ms"],

        float(cosine),
        1 - float(cosine)
    ))


def comparar_mesmo_modelo(nome_modelo, perfis):
    """
    Compara todos os perfis de um mesmo modelo dentro de cada comunidade.
    Exemplo:
    qwen3.5:2b | Comunidade 80 | TFIDF-GRAU
    x
    qwen3.5:2b | Comunidade 80 | WRS-PAGERANK
    """

    por_comunidade = {}

    for p in perfis:
        por_comunidade.setdefault(p["comunidade"], []).append(p)

    total = 0
    cenario = f"{nome_modelo}x{nome_modelo}"

    for comunidade, lista in por_comunidade.items():
        if len(lista) < 2:
            continue

        print(f"Comparando {cenario} - Comunidade {comunidade}")

        textos = [p["sumario"] for p in lista]

        embeddings = model.encode(
            textos,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        for i, j in combinations(range(len(lista)), 2):
            a = lista[i]
            b = lista[j]

            cosine = cosine_similarity(
                embeddings[i].reshape(1, -1),
                embeddings[j].reshape(1, -1)
            )[0][0]

            inserir_resultado(
                cenario=cenario,
                tipo="PERFILxPERFIL_MESMO_MODELO",
                a=a,
                b=b,
                cosine=cosine
            )

            total += 1

        conn.commit()

    print(f"{cenario}: {total} comparações salvas.")


def comparar_entre_modelos(modelo_a, perfis_a, modelo_b, perfis_b):
    """
    Compara modelos diferentes apenas quando o perfil é o mesmo.
    Exemplo:
    GPT | Comunidade 80 | CGBD | TFIDF | GRAU
    x
    qwen3.5:2b | Comunidade 80 | CGBD | TFIDF | GRAU
    """

    mapa_b = {
        chave_perfil(p): p
        for p in perfis_b
    }

    total = 0
    cenario = f"{modelo_a}x{modelo_b}"

    for a in perfis_a:
        k = chave_perfil(a)

        if k not in mapa_b:
            continue

        b = mapa_b[k]

        embeddings = model.encode(
            [a["sumario"], b["sumario"]],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        cosine = cosine_similarity(
            embeddings[0].reshape(1, -1),
            embeddings[1].reshape(1, -1)
        )[0][0]

        inserir_resultado(
            cenario=cenario,
            tipo="MESMO_PERFIL_ENTRE_MODELOS",
            a=a,
            b=b,
            cosine=cosine
        )

        total += 1

    conn.commit()

    print(f"{cenario}: {total} comparações salvas.")


# =========================
# BUSCAR SUMÁRIOS
# =========================

perfis_por_modelo = {}

for modelo_nome in MODELOS:
    perfis = buscar_sumarios(modelo_nome)
    perfis_por_modelo[modelo_nome] = perfis
    print(f"Perfis encontrados para {modelo_nome}: {len(perfis)}")

# =========================
# COMPARAÇÃO 1:
# MESMO MODELO
# =========================

print("\n==============================")
print("COMPARAÇÕES DENTRO DO MESMO MODELO")
print("==============================")

for modelo_nome in MODELOS:
    comparar_mesmo_modelo(
        modelo_nome,
        perfis_por_modelo[modelo_nome]
    )

# =========================
# COMPARAÇÃO 2:
# ENTRE MODELOS DIFERENTES
# =========================

print("\n==============================")
print("COMPARAÇÕES ENTRE MODELOS")
print("==============================")

for modelo_a, modelo_b in combinations(MODELOS, 2):
    comparar_entre_modelos(
        modelo_a,
        perfis_por_modelo[modelo_a],
        modelo_b,
        perfis_por_modelo[modelo_b]
    )

# =========================
# FINALIZAÇÃO
# =========================

cursor.close()
conn.close()

print("\nExperimento de similaridade/dissimilaridade finalizado.")