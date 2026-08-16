package com.mycompany.gephi;

import java.io.BufferedReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

public class TESTE2 {

    static final String DB_URL = "BD_URL";
    static final String DB_USER = "BD_USER";
    static final String DB_PASS = "BD_PASS";

    static final String OLLAMA_URL = "http://localhost:11434/api/generate";
    static final String MODELO_OLLAMA = "SELECT_MODEL"; // Models used in the experiments: llama3.2 and gemma3:1b

    static final String LLM = "llama3.2";
    static final String METODO_GERAL = "CGBD";
    static final String FONTE_TERMOS = "TESE";

    // Troque apenas esse arquivo
    static final String[] ARQUIVOS = {
            "saida_AUTOVETOR.txt",
            "saida_EXCENTRICIDADE.txt",
            "saida_GRAU.txt",
            "saida_INTERMEDIACAO.txt",
            "saida_PAGERANK.txt",
            "saida_PROXIMIDADE.txt"
    };

    public static void main(String[] args) {

        try {

            for (String arquivo : ARQUIVOS) {

                System.out.println("\n====================================");
                System.out.println("Processando arquivo: " + arquivo);
                System.out.println("====================================");

                processarArquivo(arquivo);

                System.out.println("Arquivo concluído: " + arquivo);
            }

            System.out.println("\nTodos os arquivos foram processados com sucesso!");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    static void processarArquivo(String caminhoArquivo) throws Exception {
        var inputStream = TESTE2.class
                .getClassLoader()
                .getResourceAsStream(caminhoArquivo);

        if (inputStream == null) {

            System.out.println("Arquivo não encontrado: " + caminhoArquivo);
            return;
        }

        BufferedReader br = new BufferedReader(
                new java.io.InputStreamReader(
                        inputStream,
                        StandardCharsets.UTF_8));
        String linha;

        int comunidade = -1;
        String metodo = null;
        String medida = null;
        String termos = null;

        while ((linha = br.readLine()) != null) {

            linha = linha.trim();

            if (linha.startsWith("Comunidade")) {
                comunidade = Integer.parseInt(
                        linha.replace("Comunidade", "").trim());
            }

            else if (linha.startsWith("Método:")) {
                metodo = linha.replace("Método:", "").trim();
            }

            else if (linha.startsWith("Medida:")) {
                medida = linha.replace("Medida:", "").trim();
            }

            else if (linha.startsWith("'") && linha.endsWith("'")) {
                termos = linha.replace("'", "").trim();

                if (!"INSERT".equalsIgnoreCase(metodo)) {
                    executarSumarizacao(
                            comunidade,
                            metodo,
                            medida,
                            termos);
                }

                comunidade = -1;
                metodo = null;
                medida = null;
                termos = null;
            }
        }

        br.close();
    }

    static void executarSumarizacao(
            int comunidade,
            String metodoOriginal,
            String medida,
            String termos) {

        try {
            if (comunidade == -1 || metodoOriginal == null || medida == null || termos == null) {
                return;
            }

            long inicio = System.currentTimeMillis();

            String sumario = gerarResumoIA(termos);

            long tempo = System.currentTimeMillis() - inicio;

            salvarSumario(
                    LLM,
                    comunidade,
                    METODO_GERAL,
                    metodoOriginal,
                    medida,
                    sumario,
                    tempo,
                    FONTE_TERMOS);

            System.out.println(
                    "Salvo | Comunidade " + comunidade +
                            " | Método: " + metodoOriginal +
                            " | Medida: " + medida +
                            " | Tempo: " + tempo + " ms");

        } catch (Exception e) {
            System.out.println(
                    "Erro | Comunidade " + comunidade +
                            " | Método: " + metodoOriginal +
                            " | Medida: " + medida);
            e.printStackTrace();
        }
    }

    static String gerarResumoIA(String termos) throws Exception {

        String prompt = """
                You are an academic researcher.

                Generate an academic description in English about a research community using exclusively the provided keywords.

                RULES:

                * The text must be written entirely in ENGLISH.
                * Use only information that can be directly inferred from the keywords.
                * Do not invent contexts, applications, domains, or research areas that are not represented by the terms.
                * Be objective, coherent, and descriptive.
                * Do not use bullet points or lists.
                * Do not use titles.
                * Do not use subtitles.
                * Do not use expressions such as "Academic Summary", "Conclusions", "Preliminary Conclusions", "Final Considerations", "In summary", "To conclude", "Finally", or equivalent phrases.
                * Do not make recommendations or judgments about the quality of the research.
                * Do not present final conclusions.
                * Return only the community description as continuous text, organized into two or three paragraphs.

                Keywords:
                """
                + termos;

        String body = """
                {
                  "model": "%s",
                  "prompt": "%s",
                  "stream": false
                }
                """.formatted(MODELO_OLLAMA, escaparJson(prompt));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(OLLAMA_URL))
                .header("Content-Type", "application/json; charset=UTF-8")
                .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                .build();

        HttpClient client = HttpClient.newHttpClient();

        HttpResponse<String> response = client.send(
                request,
                HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

        if (response.statusCode() != 200) {
            throw new RuntimeException("Erro no Ollama: " + response.body());
        }

        return extrairResposta(response.body());
    }

    static void salvarSumario(
            String llm,
            int comunidade,
            String metodo,
            String medida,
            String centralidade,
            String sumario,
            long tempo,
            String fonteTermos) throws Exception {

        Connection conn = DriverManager.getConnection(
                DB_URL,
                DB_USER,
                DB_PASS);

        String sql = """
                INSERT INTO sumarizacoes4
                (llm, comunidade, metodo, medida, centralidade, sumario, tempo_ms, fonte_termos)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """;

        PreparedStatement ps = conn.prepareStatement(sql);

        ps.setString(1, llm);
        ps.setInt(2, comunidade);
        ps.setString(3, metodo);
        ps.setString(4, medida);
        ps.setString(5, centralidade);
        ps.setString(6, sumario);
        ps.setLong(7, tempo);
        ps.setString(8, fonteTermos);

        ps.executeUpdate();

        ps.close();
        conn.close();
    }

    static String escaparJson(String texto) {

        return texto
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "");
    }

    static String extrairResposta(String json) {

        String chave = "\"response\":\"";
        int inicio = json.indexOf(chave);

        if (inicio == -1) {
            return json;
        }

        inicio += chave.length();

        StringBuilder resposta = new StringBuilder();

        boolean escape = false;

        for (int i = inicio; i < json.length(); i++) {

            char c = json.charAt(i);

            if (escape) {

                switch (c) {
                    case 'n' -> resposta.append('\n');
                    case 't' -> resposta.append('\t');
                    case 'r' -> resposta.append('\r');
                    case '"' -> resposta.append('"');
                    case '\\' -> resposta.append('\\');
                    default -> resposta.append(c);
                }

                escape = false;

            } else {

                if (c == '\\') {
                    escape = true;
                } else if (c == '"') {
                    break;
                } else {
                    resposta.append(c);
                }
            }
        }

        return resposta.toString().trim();
    }
}