# Dossiê técnico e metodológico — Projeto Integrador IV

> Investigação refeita em 17/09/2026 sobre o estado
> `1c5fb405334557af62ef86553706aef5dd6825ea` da branch `main`.
> Este documento descreve o estado técnico final atual, distingue evidência
> versionada de artefato local e registra resultados reproduzidos sem alterar
> código, dados, hiperparâmetros ou artefatos. As marcações usadas são:
> **Confirmado**, **Execução reproduzida**, **Histórico**, **Inferência técnica** e
> **Contexto externo**.

## 1. Contexto técnico do projeto

**Confirmado.** O projeto investiga o uso de dados públicos e aprendizado de
máquina para estimar o **Valor de Transação (declarado pelo contribuinte)** de
apartamentos na cidade de São Paulo. O produto técnico atual reúne ingestão e
tratamento de dados, auditoria de qualidade, seleção e avaliação de modelos de
regressão, artefato de produção, aplicação Streamlit, testes automatizados e
documentação.

O alvo não deve ser denominado preço de mercado, preço de anúncio, valor venal ou
avaliação profissional. A aplicação fornece uma estimativa estatística do valor
declarado e não substitui um laudo imobiliário.

O tema norteador acadêmico, Design Thinking, entrevistas, participante externo,
orientações da professora, discussões do grupo e validação qualitativa não estão
documentados no repositório. Esses elementos permanecem como **contexto externo**.

## 2. Fonte de dados e ingestão

**Confirmado.** A fonte declarada é a Prefeitura de São Paulo — Secretaria
Municipal da Fazenda, conjunto **Guias de ITBI pagas em 2025**. O README identifica
o arquivo baixado como `GUIAS DE ITBI PAGAS (28012026) XLS.xlsx`, armazenado
localmente como `data/raw/itbi_2025.xlsx` e ignorado pelo Git.

O workbook contém 12 abas mensais, de `JAN-2025` a `DEZ-2025`, além de abas de
legenda, explicações, usos e padrões. As abas mensais somam **230.525 registros**.
O pipeline de ingestão lê as abas definidas, valida as 28 colunas oficiais, remove
somente extras vazias `__UNNAMED__`, acrescenta `source_sheet` e `source_month`,
concatena com `vertical_relaxed` e grava Parquet Zstandard.

**Execução reproduzida.** `scripts/validate_interim.py` confirmou 230.525 linhas,
30 colunas, meses 1–12, ausência de nulos nas colunas de rastreabilidade e as 28
colunas oficiais.

### 2.1 Data de Transação e mês da fonte

`source_month` representa a aba/mês de pagamento da guia. `Data de Transação`
representa a data do instrumento de transmissão. Elas não são intercambiáveis.
Após o filtro anual, 8.648 dos 64.227 registros processados e 8.052 dos 63.140
economicamente válidos possuem mês da `Data de Transação` diferente de
`source_month`.

A modelagem usa **Data de Transação**, não `source_month`, para definir o escopo e
as partições temporais. Essa escolha está implementada em `cleaning.py`,
`dataset.py` e `split.py`.

## 3. Exploração e história técnica inicial

O histórico mostra a evolução inicial em 10/08/2026:

- `610a0c9` — inspeção do workbook e do dicionário;
- `140ad79` — perfis de apartamentos, qualidade, cardinalidade e auditoria;
- `d30ccfd` — pipeline de ingestão e Parquet intermediário;
- `b7bcef9` — recorte, features derivadas e flags econômicas;
- `d081e14` — baselines, modelos, tuning, backtest e avaliação;
- `6b8fe51` — persistência e inferência de produção;
- `c89999a` — permutation importance;
- `f129028` — aplicação Streamlit;
- `6cb1a67` — ampliação dos testes e primeira documentação.

Não há notebooks analíticos versionados; as análises exploratórias estão em
scripts.

## 4. Funil final do recorte

**Execução reproduzida** sobre os Parquets locais:

| Etapa | Regra | Registros |
|---|---|---:|
| Base original | 12 abas de guias pagas em 2025 | 230.525 |
| Compra e venda | natureza igual a `1.Compra e venda` | 205.844 |
| Compra e venda + apartamentos | Uso IPTU 20 | 68.486 |
| Transmissão integral | proporção de 100% | 64.951 |
| Escopo temporal | Data de Transação em 2025 | 64.227 |
| Dataset econômico válido | exclusão da união das flags | **63.140** |

O período observado após o filtro anual vai de **02/01/2025 a 31/12/2025**. A
janela metodológica começa em 01/01/2025, mas não há transação observada nesse dia.

## 5. Qualidade dos dados e anomalias econômicas

As flags implementadas em `cleaning.py::add_quality_flags` são `valor_m2 < 100` e
`razao_transacao_vvr < 0,10`.

| Condição | Registros reproduzidos |
|---|---:|
| `valor_m2 < 100` | 1.018 |
| `razao_transacao_vvr < 0,10` | 301 |
| Interseção das flags | 232 |
| União das flags | 1.087 |
| Registros economicamente válidos | 63.140 |

A base processada preserva as 64.227 linhas e as flags. A exclusão ocorre ao
construir o dataset com `exclude_severe_anomalies=True`. VVR proporcional igual a
zero **não** é uma terceira regra de exclusão.

### 5.1 Achado de VVR proporcional zero

**Execução reproduzida.** Há 1.236 VVRs proporcionais zero no dataset processado e
**450** entre os válidos. Como o target é positivo, a divisão produz
`razao_transacao_vvr = inf`; a condição `< 0,10` não é ativada.

Esse grupo permanece no dataset final. VVR e razão não são features. O achado é
uma limitação de qualidade; este documento não decide se deveria ser excluído.

## 6. Variável alvo

`TARGET_COLUMN` é `Valor de Transação (declarado pelo contribuinte)`. O alvo não
equivale necessariamente a preço de mercado, preço de anúncio, valor venal,
avaliação bancária ou laudo profissional.

## 7. Engenharia e seleção de atributos

O contrato final, na ordem de entrada, é:

1. `Área Construída (m2)`;
2. `cep4`;
3. `Padrão (IPTU)`;
4. `idade_imovel`;
5. `Fração Ideal`.

| Variável | Tipo | Origem/transformação |
|---|---|---|
| Área Construída | Numérica | coluna cadastral |
| `cep4` | Categórica | quatro primeiros dígitos do CEP normalizado |
| Padrão IPTU | Categórica | código cadastral |
| `idade_imovel` | Numérica | `2025 - ACC (IPTU)` |
| Fração Ideal | Numérica | coluna cadastral |

`mes_transacao` deriva de `Data de Transação`, foi somente experimental e fica fora
de `FEATURE_COLUMNS_WITHOUT_MONTH`. Os testes protegem sua exclusão.

CEP4 é aproximação espacial. Sua criação e cardinalidade de 397 categorias são
confirmadas, mas a justificativa humana para preferi-la a outras granularidades
não está explicitamente versionada.

## 8. Prevenção de data leakage

`LEAKAGE_COLUMNS` lista VVR, VVR proporcional, Base de Cálculo, Valor Financiado,
`valor_m2` e `razao_transacao_vvr`. Os dois últimos usam o target em sua fórmula e
a Base de Cálculo é relacionada ao valor declarado e ao VVR. Nenhum integra as
features finais.

O teste `test_final_features_do_not_contain_leakage` protege esse contrato
conhecido, mas não é um detector geral de qualquer vazamento possível.

## 9. Dataset final e preprocessing

O dataset de ML possui **63.140 observações**. O código rejeita datas nulas ou fora
de 2025, ausência de colunas e nulos nas features/target.

No XGBoost e Random Forest, CEP4 e Padrão passam por `OneHotEncoder` com
`handle_unknown="infrequent_if_exist"` e `min_frequency=10`; área, idade e fração
passam sem escala. A Regressão Linear aplica `StandardScaler` às numéricas.

## 10. Estratégia temporal e isolamento do teste

| Partição | Janela definida | Datas observadas | Registros |
|---|---|---|---:|
| Treino da seleção | 01/01–31/10/2025 | 02/01–31/10/2025 | 52.807 |
| Validação | 01/11–30/11/2025 | 01/11–30/11/2025 | 4.902 |
| Teste reservado | 01/12–31/12/2025 | 01/12–31/12/2025 | 5.431 |

`build_temporal_partitions()` valida datas, exclusividade, cobertura, ausência de
sobreposição e ordem cronológica.

### 10.1 Isolamento arquitetural

O commit `ee8a5cf` criou `build_selection_split()`. A função consulta o dataset com
limites de 01/01 a 01/12/2025; dezembro não é selecionado do Parquet nos fluxos de
comparação e tuning. Ela retorna somente `x_train`, `y_train`, `x_validation` e
`y_validation` — nunca `x_test`, `y_test`, targets ou linhas de dezembro.

Baseline, Linear, Random Forest, comparação com/sem mês e tuning usam essa API. O
split completo permanece para validação estrutural e avaliação final.

### 10.2 Correção metodológica

**Histórico.** Antes de `a3132f6`, o código agrupava pelo número do mês e permitia
datas de outros anos. A correção filtrou Data de Transação para 2025, reduziu o
dataset válido histórico de 63.807 para 63.140 e tornou o holdout literalmente
dezembro de 2025. Os números antigos aparecem apenas como estado superado.

## 11. Comparação de modelos — novembro

**Execução reproduzida.** Todos treinaram em Jan–Out e avaliaram 4.902 registros de
novembro.

| Modelo | MAE | RMSE | R² |
|---|---:|---:|---:|
| Dummy mediana | R$ 445.690,03 | R$ 1.359.439,91 | -0,0464 |
| Regressão Linear | R$ 312.417,38 | R$ 859.369,42 | 0,5818 |
| Random Forest | R$ 185.435,77 | R$ 658.238,14 | 0,7547 |
| XGBoost inicial com mês | R$ 184.440,95 | R$ 481.673,15 | 0,8686 |
| XGBoost inicial sem mês | R$ 181.962,60 | R$ 463.993,37 | 0,8781 |
| XGBoost ajustado | **R$ 170.133,00** | **R$ 462.107,92** | **0,8791** |

São métricas de seleção em novembro, não do teste final.

## 12. Experimento com mês

| Configuração inicial | MAE | RMSE | R² |
|---|---:|---:|---:|
| Com `mes_transacao` | R$ 184.440,95 | R$ 481.673,15 | 0,8686 |
| Sem `mes_transacao` | R$ 181.962,60 | R$ 463.993,37 | 0,8781 |

Sem mês menos com mês: MAE **-R$ 2.478,35**, RMSE **-R$ 17.679,78** e R²
**+0,0095**. A versão sem mês foi melhor nas três métricas dessa validação.

## 13. Tuning do XGBoost

O grid combina depths 4/6/8, taxas 0,03/0,05 e 500/800 árvores. O critério é o
menor MAE em novembro.

| depth | lr | árvores | MAE | RMSE | R² |
|---:|---:|---:|---:|---:|---:|
| 4 | 0,03 | 500 | R$ 208.366,50 | R$ 530.975,81 | 0,8404 |
| 4 | 0,03 | 800 | R$ 197.970,42 | R$ 506.035,50 | 0,8550 |
| 4 | 0,05 | 500 | R$ 197.033,08 | R$ 511.322,21 | 0,8520 |
| 4 | 0,05 | 800 | R$ 188.402,75 | R$ 490.752,91 | 0,8636 |
| 6 | 0,03 | 500 | R$ 192.704,74 | R$ 487.146,40 | 0,8656 |
| 6 | 0,03 | 800 | R$ 183.249,70 | R$ 470.117,98 | 0,8749 |
| 6 | 0,05 | 500 | R$ 181.962,60 | R$ 463.993,37 | 0,8781 |
| 6 | 0,05 | 800 | R$ 175.511,62 | R$ 458.157,15 | 0,8811 |
| 8 | 0,03 | 500 | R$ 183.503,87 | R$ 479.429,53 | 0,8698 |
| 8 | 0,03 | 800 | R$ 176.450,16 | R$ 472.930,47 | 0,8734 |
| 8 | 0,05 | 500 | R$ 174.777,78 | R$ 464.321,51 | 0,8779 |
| 8 | 0,05 | 800 | **R$ 170.133,00** | R$ 462.107,92 | 0,8791 |

## 14. Backtest dos três finalistas

A = depth 8/800; B = depth 8/500; C = depth 6/800. Todos usam taxa 0,05.

| Cand. | Val. | Treino | Validação | MAE | RMSE | R² |
|---|---:|---:|---:|---:|---:|---:|
| A | Jul | 30.718 | 5.331 | R$ 175.835,37 | R$ 601.923,77 | 0,7103 |
| A | Ago | 36.049 | 5.366 | R$ 173.278,25 | R$ 618.306,02 | 0,7758 |
| A | Set | 41.415 | 5.509 | R$ 175.142,47 | R$ 557.604,38 | 0,7624 |
| A | Out | 46.924 | 5.883 | R$ 188.280,98 | R$ 709.856,93 | 0,8144 |
| A | Nov | 52.807 | 4.902 | R$ 170.133,00 | R$ 462.107,92 | 0,8791 |
| B | Jul | 30.718 | 5.331 | R$ 180.254,26 | R$ 601.583,03 | 0,7106 |
| B | Ago | 36.049 | 5.366 | R$ 178.145,38 | R$ 619.572,19 | 0,7749 |
| B | Set | 41.415 | 5.509 | R$ 178.298,53 | R$ 543.878,42 | 0,7739 |
| B | Out | 46.924 | 5.883 | R$ 194.739,10 | R$ 719.275,02 | 0,8094 |
| B | Nov | 52.807 | 4.902 | R$ 174.777,78 | R$ 464.321,51 | 0,8779 |
| C | Jul | 30.718 | 5.331 | R$ 180.374,91 | R$ 600.608,35 | 0,7115 |
| C | Ago | 36.049 | 5.366 | R$ 180.067,90 | R$ 624.059,29 | 0,7716 |
| C | Set | 41.415 | 5.509 | R$ 179.503,44 | R$ 540.504,46 | 0,7767 |
| C | Out | 46.924 | 5.883 | R$ 195.589,63 | R$ 710.508,87 | 0,8141 |
| C | Nov | 52.807 | 4.902 | R$ 175.511,62 | R$ 458.157,15 | 0,8811 |

| Candidato | MAE médio | Desvio | RMSE médio | R² médio | Vitórias MAE |
|---|---:|---:|---:|---:|---:|
| A | **R$ 176.534,01** | R$ 6.196,59 | R$ 589.959,80 | 0,7884 | **5/5** |
| B | R$ 181.243,01 | R$ 6.974,05 | R$ 589.726,03 | 0,7894 | 0/5 |
| C | R$ 182.209,50 | R$ 6.916,13 | **R$ 586.767,62** | **0,7910** | 0/5 |

A venceu pelo critério de MAE e em todas as janelas por MAE. C teve RMSE e R²
médios ligeiramente melhores; A não foi superior em todas as métricas.

## 15. Modelo congelado

```text
XGBRegressor(
    objective="reg:squarederror",
    max_depth=8,
    learning_rate=0.05,
    n_estimators=800,
    min_child_weight=1,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    tree_method="hist",
    random_state=42,
    n_jobs=-1,
)
```

O congelamento ocorreu antes do teste. Dezembro não participou de features,
tuning nem hiperparâmetros.

## 16. Avaliação final oficial

Treino: 57.709 registros de Jan–Nov/2025. Teste: 5.431 de Dez/2025. As partições
são disjuntas e ordenadas.

| Métrica | Valor bruto | Apresentação |
|---|---:|---:|
| MAE | 231947.92292769515 | R$ 231.947,92 |
| RMSE | 1091963.084853122 | R$ 1.091.963,08 |
| R² | 0.5729976346033591 | 0,5730 |

São as métricas oficiais do modelo de avaliação, não do modelo de produção.

## 17. Análise final dos erros

Erro assinado = real − predição; valor negativo indica previsão acima do real.

| Estatística | Resultado |
|---|---:|
| Mediana do erro absoluto | R$ 84.607,78 |
| Acima do real | 2.895 — 53,31% |
| Abaixo do real | 2.536 — 46,69% |
| Exatamente iguais | 0 |
| Erro assinado médio | -R$ 30.398,29 |

| Faixa real | Casos | MAE |
|---|---:|---:|
| < R$ 300 mil | 1.494 | R$ 124.469,13 |
| R$ 300–500 mil | 1.574 | R$ 89.352,55 |
| R$ 500 mil–1 mi | 1.318 | R$ 158.119,75 |
| R$ 1–2 mi | 671 | R$ 342.779,83 |
| R$ 2–5 mi | 298 | R$ 745.698,57 |
| ≥ R$ 5 mi | 76 | R$ 3.585.343,55 |

Os 76 casos ≥ R$ 5 milhões são 1,40% do teste, com mediana absoluta de
R$ 1.656.100,00 e RMSE de R$ 7.957.496,16.

### 17.1 Dez maiores erros

| # | CEP4 | Área | Padrão | Idade | Fração | Real | Predição | Erro assinado | Erro absoluto |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0453 | 1.231 | 25 | 6 | 0,0600 | R$ 70.000.000,00 | R$ 19.467.184,00 | R$ 50.532.816,00 | R$ 50.532.816,00 |
| 2 | 0454 | 699 | 24 | 4 | 0,0779 | R$ 7.164.000,00 | R$ 37.240.316,00 | -R$ 30.076.316,00 | R$ 30.076.316,00 |
| 3 | 0451 | 1.134 | 25 | 22 | 0,0532 | R$ 3.295.818,32 | R$ 30.323.060,00 | -R$ 27.027.241,68 | R$ 27.027.241,68 |
| 4 | 0454 | 749 | 24 | 16 | 0,0515 | R$ 17.500.000,00 | R$ 34.269.312,00 | -R$ 16.769.312,00 | R$ 16.769.312,00 |
| 5 | 0400 | 900 | 25 | 11 | 0,0307 | R$ 24.000.000,00 | R$ 7.931.103,50 | R$ 16.068.896,50 | R$ 16.068.896,50 |
| 6 | 0451 | 689 | 25 | 18 | 0,0467 | R$ 12.200.000,00 | R$ 25.859.534,00 | -R$ 13.659.534,00 | R$ 13.659.534,00 |
| 7 | 0453 | 759 | 25 | 1 | 0,0503 | R$ 30.000.000,00 | R$ 18.754.852,00 | R$ 11.245.148,00 | R$ 11.245.148,00 |
| 8 | 0403 | 794 | 25 | 24 | 0,1429 | R$ 783.000,00 | R$ 11.683.360,00 | -R$ 10.900.360,00 | R$ 10.900.360,00 |
| 9 | 0414 | 659 | 24 | 11 | 0,0400 | R$ 1.837.813,07 | R$ 11.461.631,00 | -R$ 9.623.817,93 | R$ 9.623.817,93 |
| 10 | 0450 | 555 | 24 | 36 | 0,0614 | R$ 14.750.000,00 | R$ 5.775.809,00 | R$ 8.974.191,00 | R$ 8.974.191,00 |

A mediana da área é 100 m² no teste e 754 m² nos dez maiores erros. Essa é uma
associação descritiva, não causal.

## 18. Permutation importance final

Metodologia: `scoring="neg_mean_absolute_error"`, `n_repeats=10`,
`random_state=42`, `n_jobs=-1`.

| Variável | Aumento médio do MAE | Desvio |
|---|---:|---:|
| Área Construída | R$ 460.785,14 | ± R$ 6.331,58 |
| CEP4 | R$ 124.343,02 | ± R$ 3.620,19 |
| `idade_imovel` | R$ 82.576,24 | ± R$ 5.289,14 |
| Padrão IPTU | R$ 23.649,95 | ± R$ 1.499,60 |
| Fração Ideal | R$ 15.721,82 | ± R$ 2.524,52 |

**Importância preditiva não representa causalidade.**

## 19. Modelo de produção

Usa a mesma configuração congelada e foi treinado depois da avaliação nos 63.140
registros válidos. Não possui holdout interno nem novas métricas oficiais.

- `artifacts/apartment_price_model.joblib`: **1.988.404 bytes**;
- `artifacts/model_metadata.json`: 2.367 bytes.

| Campo do metadata | Valor |
|---|---|
| Projeto | `pi4-imoveis-sp` 0.1.0 |
| Modelo | 1.0.0 |
| Treino de produção | 63.140; sem holdout |
| Python | 3.14.6 |
| Scikit-learn | 1.9.0 |
| XGBoost | 3.4.0 |
| Joblib | 1.5.3 |
| Pandas | 3.0.5 |
| Polars | 1.43.2 |

**Histórico.** O bug antigo `environment.python = 0.1.0` foi corrigido por
`92ca761`, que separou versão do projeto e runtime, completou parâmetros e contexto
da avaliação. O validador atual carregou ambos os artefatos e confirmou o contrato.

## 20. Aplicação Streamlit

`app/app.py` registra Visão Geral, Modelo e Estimador.

- **Visão Geral:** 63.140 válidos de 2025, filtros, indicadores e gráficos.
- **Modelo:** métricas oficiais, comparação, erros, permutation importance,
  configuração, limitações e distinção avaliação/produção.
- **Estimador:** carrega o modelo de produção; recebe Área, CEP, Padrão, ACC e
  Fração; deriva CEP4 e idade; estima o valor declarado e exibe alertas.

O estimador não substitui avaliação profissional.

## 21. Testes automatizados

`uv run pytest -v -p no:cacheprovider`: **50 testes aprovados em 5,45 s**.

| Arquivo | Testes |
|---|---:|
| `test_dataset.py` | 7 |
| `test_estimator.py` | 8 |
| `test_inference.py` | 4 |
| `test_overview.py` | 7 |
| `test_presentation.py` | 9 |
| `test_production.py` | 5 |
| `test_temporal_scope.py` | 10 |
| **Total** | **50** |

## 22. Ferramentas e ambiente

| Ferramenta | Versão |
|---|---|
| Python | 3.14.6 |
| Polars | 1.43.2 |
| Pandas | 3.0.5 |
| Scikit-learn | 1.9.0 |
| XGBoost | 3.4.0 |
| Joblib | 1.5.3 |
| Streamlit | 1.59.1 |
| Plotly | 6.9.0 |
| PyArrow | 25.0.1 |
| fastexcel | 0.20.2 |
| Pytest | 9.1.1 |
| Ruff | 0.16.2 |

O projeto usa uv, Git e GitHub. O remoto é
`https://github.com/lgustavoab/pi4-imoveis-sp.git`; não há evidência de uso de
Issues, Actions ou Pull Requests.

## 23. Decisões metodológicas

| Decisão | Alternativas | Escolha | Evidência | Justificativa |
|---|---|---|---|---|
| Recorte | todos os imóveis/usos | compra/venda, Uso 20, 100% | código/funil | delimitação do produto |
| Escopo | todas as datas | Data de Transação em 2025 | `a3132f6` | coerência temporal |
| Tempo | `source_month` ou Data de Transação | Data de Transação | código/auditoria | significado transacional; razão humana adicional não versionada |
| Anomalias | manter/winsorizar/excluir | união das duas flags | código/validador | limiares implementados; motivação substantiva não versionada |
| VVR zero | excluir/manter | manter | dados/código | não virou regra; decisão humana não versionada |
| Localização | Bairro/CEP3/4/5/completo | CEP4 | contrato/perfis | aproximação; comparação quantitativa não versionada |
| Mês | incluir/excluir | excluir | comparação/testes | melhor nas três métricas de novembro |
| API de seleção | split completo/restrito | `build_selection_split` | `ee8a5cf` | não materializar dezembro |
| Teste | aleatório/temporal | Dez/2025 | `split.py` | período posterior |
| Tuning | outros grids/grid atual | 12 combinações | script | origem humana do grid não versionada |
| Critério | MAE/RMSE/R² | menor MAE | código | critério explícito |
| Backtest | 2/3 finalistas | A, B e C | `0459244` | robustez em cinco janelas |
| Escolha final | melhor em qualquer métrica | menor MAE médio | script | critério previamente definido |
| Congelamento | antes/depois do teste | antes | arquitetura | preservar teste independente |
| Avaliação/produção | um modelo/dois papéis | avaliação 57.709/5.431; produção 63.140 | metadata | separar métrica oficial de inferência |

## 24. Limitações e riscos

- A fonte reúne guias pagas em 2025; a modelagem filtra Data de Transação em 2025.
- Um ano e um mês de teste limitam generalização temporal.
- O alvo declarado não é preço de mercado.
- Faltam dormitórios, vagas dedicadas, andar, conservação, vista e interior.
- CEP4 é aproximação espacial.
- Há 450 VVRs zero válidos, embora VVR não seja feature.
- A cauda alta é rara e apresenta erros elevados.
- Métricas agregadas não são margens individuais.
- Permutation importance não é causal.
- Produção não possui holdout interno.
- Dados e artefatos são ignorados pelo Git.
- Números hardcoded na página Modelo podem divergir futuramente dos scripts.

## 25. Cronologia da correção e finalização

Datas são dos commits, não de decisões humanas anteriores.

| Fase | Commit/data | Evidência |
|---|---|---|
| Desenvolvimento original | `032d434`–`6cb1a67`, 10/08/2026 | fundação até documentação inicial |
| Auditoria metodológica | sem commit específico | documentos locais anteriores; contexto humano não versionado |
| Correção anual | `a3132f6`, 17/09/2026 15:46 -03 | filtro, validadores e testes |
| Isolamento do teste | `ee8a5cf`, 17/09/2026 15:57 -03 | API e migração dos fluxos |
| Nova seleção/tuning | execução após `ee8a5cf` | sem commit exclusivo de saída |
| Backtest ampliado | `0459244`, 17/09/2026 16:08 -03 | três candidatos |
| Avaliação corrigida | execução após correções | sem commit exclusivo de saída |
| Produção/metadata | `92ca761`, 17/09/2026 16:41 -03 | ambiente e contexto final |
| Aplicação | `fd1418c`, 17/09/2026 16:50 -03 | sincronização das páginas |
| README | `1c5fb40`, 17/09/2026 16:59 -03 | resultados finais |

## 26. Informações úteis para o relatório acadêmico

### Introdução e objetivo técnico

O repositório sustenta a exploração de dados públicos de ITBI, a construção de
pipeline reprodutível, a comparação de regressões e a entrega de interface. O
objetivo demonstrável é analisar e estimar o valor declarado de transações de
apartamentos com validação temporal.

### Metodologia demonstrável

Fonte → ingestão → recorte → filtro anual → flags → features → seleção Jan–Out/Nov
→ tuning → backtest → congelamento → teste Dez → erros/importance → produção → app.

### Resultado e conclusão técnica possível

O XGBoost ajustado venceu por MAE. No teste, obteve MAE R$ 231.947,92, RMSE
R$ 1.091.963,08 e R² 0,5730. A solução mostra capacidade preditiva no recorte e
período, sem sustentar causalidade, valor de mercado ou desempenho futuro.

## 27. Informações que não estão no repositório

- Design Thinking;
- entrevistas e roteiros;
- participante/comunidade externa;
- orientações docentes;
- discussões e autoria de decisões do grupo;
- motivação acadêmica/social;
- validação qualitativa.

Esses itens exigem fontes dos integrantes e não devem ser inventados.

# Auditoria final de consistência

## Informações consistentes

- README, código, testes, Parquets, metadata e execuções concordam em 64.227
  processados, 63.140 válidos e split 52.807/4.902/5.431.
- Baselines, comparação do mês, grid, backtest, teste final e importance foram
  reproduzidos sem divergência.
- Metadata e modelo carregado concordam com features, parâmetros e ambiente.
- Aplicação e README usam os resultados corrigidos.
- A suíte possui 50 testes aprovados.

## Divergências ainda existentes

- `analyze_final_errors.py` não imprime percentuais direcionais, erro assinado,
  estatísticas completas ≥ R$ 5 milhões nem medianas de área. Esses valores foram
  recalculados de forma não destrutiva sobre `run_final_evaluation()`.
- Saídas detalhadas de tuning, backtest, erros e importance não são artefatos
  versionados; dependem da execução dos scripts.

## Informações desatualizadas encontradas

Os documentos anteriores registravam o estado pré-correção: 63.807 válidos,
52.911/4.930/5.966 no split, 57.841/5.966 na avaliação, MAE R$ 228.857,12, RMSE
R$ 1.044.652,29, R² 0,5890, importâncias anteriores e o bug
`environment.python = 0.1.0`. São valores **históricos e superados**.

## Informações não comprovadas

- justificativas humanas dos limiares e do CEP4;
- origem humana do grid;
- quantidade histórica de consultas ao teste fora do código;
- desempenho em outros anos ou dados futuros.

## Contexto externo ao repositório

Design Thinking, entrevistas, orientação, comunidade externa, motivações,
discussões de grupo e validação qualitativa dependem dos integrantes.

## Riscos metodológicos remanescentes

- generalização temporal restrita;
- target declarado e poucos atributos;
- localização aproximada;
- cauda alta influente;
- 450 VVRs zero mantidos;
- artefatos locais ignorados;
- números documentais hardcoded na interface;
- métricas não individualizam incerteza;
- permutation importance não é causal.
