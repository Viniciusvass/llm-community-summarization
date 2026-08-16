// Criação dos gabaritos com o GPT no deepinfra

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

public class deepinfraCod3 {

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
                        "relatorio_comunidades.txt"
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

                var inputStream = deepinfraCod3.class
                                .getClassLoader()
                                .getResourceAsStream(caminhoArquivo);

                if (inputStream == null) {
                        throw new RuntimeException(
                                        "Arquivo não encontrado: " + caminhoArquivo);
                }

                BufferedReader br = new BufferedReader(
                                new InputStreamReader(
                                                inputStream,
                                                StandardCharsets.UTF_8));

                String linha;

                int comunidadeAtual = -1;

                StringBuilder conteudo = new StringBuilder();

                while ((linha = br.readLine()) != null) {

                        linha = linha.trim();

                        if (linha.startsWith("Comunidade ")) {

                                if (comunidadeAtual != -1
                                                && conteudo.length() > 0) {

                                        gerarGabarito(
                                                        comunidadeAtual,
                                                        conteudo.toString());

                                        conteudo.setLength(0);
                                }

                                comunidadeAtual = Integer.parseInt(
                                                linha.replace(
                                                                "Comunidade",
                                                                "").trim());

                                continue;
                        }

                        if (linha.startsWith("===")
                                        || linha.startsWith("Parte ")
                                        || linha.startsWith("GABARITO:")
                                        || linha.isBlank()) {

                                continue;
                        }

                        conteudo
                                        .append(linha)
                                        .append("\n");
                }

                if (comunidadeAtual != -1
                                && conteudo.length() > 0) {

                        gerarGabarito(
                                        comunidadeAtual,
                                        conteudo.toString());
                }

                br.close();
        }

        static void gerarGabarito(
                        int comunidade,
                        String termos) {

                try {

                        if (jaExiste(comunidade)) {

                                System.out.println(
                                                "Ignorado | Comunidade "
                                                                + comunidade
                                                                + " (já existe)");

                                return;
                        }

                        long inicio = System.currentTimeMillis();

                        String gabarito;

                        if (comunidade == 104) {

                                gabarito = gerarGabaritoGrande(termos);

                        } else {

                                gabarito = gerarResumoIA(termos);
                        }

                        long tempo = System.currentTimeMillis()
                                        - inicio;

                        salvarGabarito(
                                        LLM,
                                        comunidade,
                                        gabarito,
                                        tempo);

                        System.out.println(
                                        "Gabarito salvo | Comunidade "
                                                        + comunidade
                                                        + " | Tempo: "
                                                        + tempo
                                                        + " ms");

                } catch (Exception e) {

                        System.out.println(
                                        "Erro na comunidade "
                                                        + comunidade);

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
                        throw new RuntimeException(
                                        "Erro no DeepInfra: " + response.statusCode() + " | " + response.body());
                }
                return extrairRespostaDeepInfra(response.body());
        }

        static String gerarGabaritoGrande(
                        String termos) throws Exception {

                int tamanhoParte = termos.length() / 3;

                String parte1 = termos.substring(
                                0,
                                tamanhoParte);

                String parte2 = termos.substring(
                                tamanhoParte,
                                tamanhoParte * 2);

                String parte3 = termos.substring(
                                tamanhoParte * 2);

                System.out.println(
                                "Comunidade 104 dividida em 3 partes");

                String resumo1 = gerarResumoIA(parte1);

                String resumo2 = gerarResumoIA(parte2);

                String resumo3 = gerarResumoIA(parte3);

                String termosFinais = resumo1 + "\n\n"
                                + resumo2 + "\n\n"
                                + resumo3;

                return gerarResumoIA(termosFinais);
        }

        static void salvarGabarito(
                        String llm,
                        int comunidade,
                        String gabarito,
                        long tempo) throws Exception {

                Connection conn = DriverManager.getConnection(
                                DB_URL,
                                DB_USER,
                                DB_PASS);

                String sql = """
                                INSERT INTO gabaritos2
                                (llm, comunidade, gabarito, tempo_ms)
                                VALUES (?, ?, ?, ?)
                                """;

                PreparedStatement ps = conn.prepareStatement(sql);

                ps.setString(1, llm);
                ps.setInt(2, comunidade);
                ps.setString(3, gabarito);
                ps.setLong(4, tempo);

                ps.executeUpdate();

                ps.close();
                conn.close();
        }

        static boolean jaExiste(int comunidade) {

                try {

                        Connection conn = DriverManager.getConnection(
                                        DB_URL,
                                        DB_USER,
                                        DB_PASS);

                        String sql = """
                                        SELECT COUNT(*)
                                        FROM gabaritos2
                                        WHERE llm = ?
                                        AND comunidade = ?
                                        """;

                        PreparedStatement ps = conn.prepareStatement(sql);

                        ps.setString(1, LLM);
                        ps.setInt(2, comunidade);

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