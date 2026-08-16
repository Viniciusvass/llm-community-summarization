CREATE DATABASE gephi_results_final;
USE gephi_results_final;

CREATE TABLE gabaritos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    llm VARCHAR(20) NOT NULL,
    comunidade INT NOT NULL,
    gabarito LONGTEXT NOT NULL,
    tempo_ms BIGINT
);

SELECT * FROM gabaritos;

CREATE TABLE sumarizacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    llm VARCHAR(20) NOT NULL,
    comunidade INT NOT NULL,
    metodo VARCHAR(30) NOT NULL,
    centralidade VARCHAR(30),
    sumario LONGTEXT NOT NULL,
    tempo_ms BIGINT,
    fonte_termos VARCHAR(30) NOT NULL
);

SELECT * FROM sumarizacoes;

CREATE TABLE sumarizacoes_2 (
    id INT AUTO_INCREMENT PRIMARY KEY,
    llm VARCHAR(20) NOT NULL,
    comunidade INT NOT NULL,
    metodo VARCHAR(30) NOT NULL,
    centralidade VARCHAR(30),
    sumario LONGTEXT NOT NULL,
    tempo_ms BIGINT,
    fonte_termos VARCHAR(30) NOT NULL
);

SELECT * FROM sumarizacoes_2;

CREATE TABLE avaliacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cenario VARCHAR(30) NOT NULL,
    -- GPTxGPT, GPTxOLLAMA, OLLAMAxOLLAMA
    llm_base VARCHAR(20) NOT NULL,
	llm_comparado VARCHAR(20) NOT NULL,
    comunidade INT NOT NULL,
    metodo VARCHAR(30) NOT NULL,
    -- CGBA, CGBD, CGBDE, CENTRALIDADE
    centralidade VARCHAR(30),
    -- NULL para métodos sem centralidade
    fonte_termos VARCHAR(30) NOT NULL,
    -- MEUS_RESULTADOS ou RESULTADOS_TESE
    cosine_similarity DOUBLE,
    bert_precision DOUBLE,
    bert_recall DOUBLE,
    bert_f1 DOUBLE,
    tempo_ms BIGINT
);

SELECT * FROM avaliacoes;

CREATE TABLE sumarizacoes3 (
    id INT AUTO_INCREMENT PRIMARY KEY,
    llm VARCHAR(20) NOT NULL,
    comunidade INT NOT NULL,
    metodo VARCHAR(30) NOT NULL,
    medida VARCHAR(30) NOT NULL,
    centralidade VARCHAR(30),
    sumario LONGTEXT NOT NULL,
    tempo_ms BIGINT,
    fonte_termos VARCHAR(30) NOT NULL
);

SELECT * FROM sumarizacoes3;

SELECT
    id,
    comunidade,
    medida,
    centralidade,
    sumario
FROM sumarizacoes3
WHERE llm = "qwen3.5:2b"
ORDER BY id;

CREATE TABLE similaridade_perfis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cenario VARCHAR(30) NOT NULL,
    tipo_comparacao VARCHAR(50) NOT NULL,
    fonte_termos VARCHAR(30) NOT NULL,
    comunidade INT NOT NULL,
    llm_a VARCHAR(20) NOT NULL,
    abordagem_a VARCHAR(30),
    medida_a VARCHAR(30),
    centralidade_a VARCHAR(30),
    tempo_a_ms BIGINT,
    llm_b VARCHAR(20) NOT NULL,
    abordagem_b VARCHAR(30),
    medida_b VARCHAR(30),
    centralidade_b VARCHAR(30),
    tempo_b_ms BIGINT,
    cosine_similarity DOUBLE,
    dissimilaridade DOUBLE
);

SELECT * FROM similaridade_perfis;

ALTER TABLE similaridade_perfis
MODIFY COLUMN cenario VARCHAR(100);

ALTER TABLE similaridade_perfis
MODIFY COLUMN llm_a VARCHAR(50);

ALTER TABLE similaridade_perfis
MODIFY COLUMN llm_b VARCHAR(50);

CREATE TABLE avaliacoes3 (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cenario VARCHAR(30) NOT NULL,
    -- GPTxGPT ou GPTxOLLAMA
    llm_base VARCHAR(20) NOT NULL,
    llm_comparado VARCHAR(20) NOT NULL,
    comunidade INT NOT NULL,
    metodo VARCHAR(30) NOT NULL,
    medida VARCHAR(30) NOT NULL,
    centralidade VARCHAR(30),
    fonte_termos VARCHAR(30) NOT NULL,
    cosine_similarity DOUBLE,
    dissimilaridade DOUBLE,
    bert_precision DOUBLE,
    bert_recall DOUBLE,
    bert_f1 DOUBLE,
    tempo_ms BIGINT
);

SELECT * FROM avaliacoes3;

TRUNCATE TABLE avaliacoes3;

ALTER TABLE avaliacoes3
ADD COLUMN tempo_gabarito_ms BIGINT,
ADD COLUMN tempo_economizado_ms BIGINT;

ALTER TABLE avaliacoes3
MODIFY COLUMN cenario VARCHAR(100);

ALTER TABLE avaliacoes3
MODIFY COLUMN llm_base VARCHAR(50);

ALTER TABLE avaliacoes3
MODIFY COLUMN llm_comparado VARCHAR(50);

CREATE TABLE gabaritos2 (
    id INT AUTO_INCREMENT PRIMARY KEY,
    llm VARCHAR(20) NOT NULL,
    comunidade INT NOT NULL,
    gabarito LONGTEXT NOT NULL,
    tempo_ms BIGINT
);

SELECT * FROM gabaritos2;

CREATE TABLE sumarizacoes4 (
    id INT AUTO_INCREMENT PRIMARY KEY,
    llm VARCHAR(20) NOT NULL,
    comunidade INT NOT NULL,
    metodo VARCHAR(30) NOT NULL,
    medida VARCHAR(30) NOT NULL,
    centralidade VARCHAR(30),
    sumario LONGTEXT NOT NULL,
    tempo_ms BIGINT,
    fonte_termos VARCHAR(30) NOT NULL
);

SELECT * FROM sumarizacoes4;

SELECT
    id,
    comunidade,
    medida,
    centralidade,
    sumario
FROM sumarizacoes4
WHERE llm = "qwen3.5:2b"
ORDER BY id;