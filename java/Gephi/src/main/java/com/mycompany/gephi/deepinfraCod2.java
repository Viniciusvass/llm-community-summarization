// Criação das sumarizações com o GPT no deepinfra

package com.mycompany.gephi;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class deepinfraCod2 {

    static final String DB_URL = "BD_URL";
    static final String DB_USER = "BD_USER";
    static final String DB_PASS = "BD_PASS";

    // DeepInfra
    static final String DEEPINFRA_URL = "https://api.deepinfra.com/v1/openai/chat/completions";

    // Coloque sua chave aqui ou use variável de ambiente
    static final String DEEPINFRA_API_KEY = "DEEPINFRA_API_KEY";

    // Confirme o nome exato no botão copiar do modelo no DeepInfra
    static final String MODELO_DEEPINFRA = "openai/gpt-oss-120b-turbo";

    // Nome que será salvo no banco
    static final String LLM = "gpt-oss-120b-turbo";

    static final String METODO_GERAL = "CGBD";
    static final String FONTE_TERMOS = "TESE";

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
                System.out.println("Processando: " + arquivo);
                System.out.println("====================================");

                processarArquivo(arquivo);
            }

            System.out.println("\nTodos os arquivos foram processados!");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    static void processarArquivo(String caminhoArquivo) throws Exception {

        var inputStream = deepinfraCod2.class
                .getClassLoader()
                .getResourceAsStream(caminhoArquivo);

        if (inputStream == null) {
            throw new RuntimeException("Arquivo não encontrado em resources: " + caminhoArquivo);
        }

        BufferedReader br = new BufferedReader(
                new InputStreamReader(inputStream, StandardCharsets.UTF_8));

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

            if (jaExiste(comunidade, medida, metodoOriginal)) {

                System.out.println(
                        "Ignorado | Comunidade " + comunidade +
                                " | Método: " + metodoOriginal +
                                " | Medida: " + medida +
                                " (já existe)");

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
                  "messages": [
                    {
                      "role": "user",
                      "content": "%s"
                    }
                  ],
                  "stream": false
                }
                """.formatted(
                MODELO_DEEPINFRA,
                escaparJson(prompt));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(DEEPINFRA_URL))
                .header("Content-Type", "application/json; charset=UTF-8")
                .header("Authorization", "Bearer " + DEEPINFRA_API_KEY)
                .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                .build();

        HttpClient client = HttpClient.newHttpClient();

        HttpResponse<String> response = client.send(
                request,
                HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

        if (response.statusCode() != 200) {
            throw new RuntimeException("Erro no DeepInfra: " + response.statusCode() + " | " + response.body());
        }
        return extrairRespostaDeepInfra(response.body());
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

    static boolean jaExiste(
            int comunidade,
            String medida,
            String centralidade) {

        try {

            Connection conn = DriverManager.getConnection(
                    DB_URL,
                    DB_USER,
                    DB_PASS);

            String sql = """
                    SELECT COUNT(*)
                    FROM sumarizacoes4
                    WHERE llm = ?
                    AND comunidade = ?
                    AND medida = ?
                    AND centralidade = ?
                    AND fonte_termos = ?
                    """;

            PreparedStatement ps = conn.prepareStatement(sql);

            ps.setString(1, LLM);
            ps.setInt(2, comunidade);
            ps.setString(3, medida);
            ps.setString(4, centralidade);
            ps.setString(5, FONTE_TERMOS);

            var rs = ps.executeQuery();

            rs.next();

            boolean existe = rs.getInt(1) > 0;

            rs.close();
            ps.close();
            conn.close();

            return existe;

        } catch (Exception e) {

            e.printStackTrace();
            return false;
        }
    }

    static String escaparJson(String texto) {

        return texto
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "");
    }

    static String extrairRespostaDeepInfra(String json) {

        try {

            ObjectMapper mapper = new ObjectMapper();

            JsonNode root = mapper.readTree(json);

            JsonNode message = root
                    .path("choices")
                    .get(0)
                    .path("message");

            String content = message.path("content")
                    .asText("")
                    .trim();

            if (!content.isEmpty()) {
                return content;
            }

            return message
                    .path("reasoning_content")
                    .asText("")
                    .trim();

        } catch (Exception e) {

            e.printStackTrace();
            return "";
        }
    }
}