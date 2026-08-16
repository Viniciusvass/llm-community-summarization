import mysql.connector
from html import escape

# ==========================
# Configuração do banco
# ==========================
DB_CONFIG = {
    "host": "BD_HOST",
    "user": "BD_USER",
    "password": "BD_PASSWORD",
    "database": "BD_DATABASE"
}

# ==========================
# Conexão
# ==========================
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT
        id,
        llm,
        comunidade,
        medida,
        centralidade,
        sumario,
        tempo_ms
    FROM sumarizacoes4
    ORDER BY id
""")

resumos = cursor.fetchall()

cursor.close()
conn.close()

# ==========================
# Nomes amigáveis
# ==========================
nomes_metodos = {
    "TFIDF": "TF-IDF",
    "BNS": "BNS",
    "WRS": "WRS",
    "X2": "χ²",
    "CHI2": "χ²",
    "X²": "χ²"
}

# ==========================
# Início do HTML
# ==========================
html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Resultados das Sumarizações</title>

<style>

body {{
    font-family: Arial, sans-serif;
    max-width: 1200px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.6;
}}

h1 {{
    margin-bottom: 5px;
}}

h2 {{
    margin-top: 45px;
    border-bottom: 1px solid #ccc;
    padding-bottom: 5px;
}}

h3 {{
    margin-top: 30px;
}}

h4 {{
    margin-top: 20px;
    color: #555;
}}

.metodo {{
    margin-left: 30px;
}}

.comunidade {{
    margin-left: 30px;
}}

.experimento {{
    margin-left: 30px;
    margin-bottom: 10px;
}}

details {{
    margin-top: 5px;
}}

summary {{
    cursor: pointer;
}}

.resumo {{
    margin-top: 10px;
    white-space: pre-wrap;
    text-align: justify;
}}

</style>

</head>

<body>

<h1>Resultados das Sumarizações</h1>

<p>
    Total de resumos:
    <strong>{len(resumos)}</strong>
</p>
"""

# ==========================
# Estrutura hierárquica
# ==========================
llm_atual = None
comunidade_atual = None
metodo_atual = None

for r in resumos:

    metodo = nomes_metodos.get(
        str(r["medida"]).upper(),
        r["medida"]
    )

    # Novo LLM
    if r["llm"] != llm_atual:

        if metodo_atual is not None:
            html += "</div>"

        if comunidade_atual is not None:
            html += "</div>"

        if llm_atual is not None:
            html += "</div>"

        html += f"""
        <div class="llm">
            <h2>{escape(r['llm'])}</h2>
        """

        llm_atual = r["llm"]
        comunidade_atual = None
        metodo_atual = None

    # Nova Comunidade
    if r["comunidade"] != comunidade_atual:

        if metodo_atual is not None:
            html += "</div>"
            metodo_atual = None

        if comunidade_atual is not None:
            html += "</div>"

        html += f"""
            <div class="comunidade">
                <h3>Comunidade {r['comunidade']}</h3>
        """

        comunidade_atual = r["comunidade"]

    # Novo Método
    if metodo != metodo_atual:

        if metodo_atual is not None:
            html += "</div>"

        html += f"""
                <div class="metodo">
                    <h4>{escape(str(metodo))}</h4>
        """

        metodo_atual = metodo

    centralidade = r["centralidade"] or "-"
    tempo = r["tempo_ms"] or "-"
    resumo = escape(r["sumario"])

    html += f"""
        <div class="experimento">

            <details>
                <summary>
                    Experimento #{r['id']}
                    | Centralidade: {escape(str(centralidade))}
                    | Tempo: {tempo} ms
                    | Ver resumo
                </summary>

                <div class="resumo">
{resumo}
                </div>

            </details>

        </div>
    """

# Fecha as divs abertas
if metodo_atual is not None:
    html += "</div>"

if comunidade_atual is not None:
    html += "</div>"

if llm_atual is not None:
    html += "</div>"

html += """
</body>
</html>
"""

# ==========================
# Salva o arquivo
# ==========================
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ index.html criado com {len(resumos)} resumos.")