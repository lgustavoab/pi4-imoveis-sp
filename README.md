# 🏠 Sistema Inteligente para Análise e Estimativa de Valores de Apartamentos em São Paulo

Projeto desenvolvido no contexto do **Projeto Integrador IV do curso de Ciência de Dados da UNIVESP**.

O projeto utiliza dados públicos de transações imobiliárias da cidade de São Paulo para desenvolver um modelo de Machine Learning capaz de **estimar o valor de transação de apartamentos residenciais a partir de características cadastrais do imóvel**.

Além da etapa de Ciência de Dados, foi desenvolvida uma aplicação interativa em **Streamlit**, permitindo explorar os dados, visualizar o desempenho do modelo e realizar novas estimativas.

---

## 📌 Objetivo

O projeto busca responder à seguinte questão:

> É possível utilizar dados públicos de transações imobiliárias e técnicas de Machine Learning para estimar o valor de transação de apartamentos na cidade de São Paulo?

Para responder a essa questão, o projeto contempla:

- coleta e tratamento de dados públicos;
- análise exploratória;
- avaliação da qualidade dos dados;
- engenharia de atributos;
- comparação de modelos de regressão;
- ajuste de hiperparâmetros;
- validação temporal;
- análise dos erros;
- interpretação do modelo;
- construção de um modelo de produção;
- desenvolvimento de dashboard interativo;
- desenvolvimento de estimador de valores;
- testes automatizados.

---

## 🗂️ Fonte dos dados

Os dados utilizados são provenientes da **Prefeitura de São Paulo** e correspondem às **Guias de ITBI pagas em 2025**.

**Fonte:** Prefeitura de São Paulo — Secretaria Municipal da Fazenda

**Página oficial para download dos dados:** [Prefeitura de São Paulo](https://prefeitura.sp.gov.br/web/fazenda/w/acesso_a_informacao/31501)

Arquivo original utilizado:

```text
GUIAS DE ITBI PAGAS (28012026) XLS.xlsx
```

O arquivo reúne guias de ITBI pagas em 2025. O ano de pagamento da guia não
implica, por si só, que a respectiva **Data de Transação** também pertença a
2025. Para manter o escopo temporal do estudo, o pipeline final restringe essa
coluna ao ano de 2025 antes da modelagem.

Por questões de tamanho e organização do repositório, o arquivo bruto não é versionado no Git.

Após o download, ele deve ser salvo como:

```text
data/raw/itbi_2025.xlsx
```

---

## 📊 Base original

O arquivo original de guias pagas em 2025 contém:

**230.525 registros**

distribuídos entre as planilhas mensais da fonte.

Entre as informações disponibilizadas estão:

- valor de transação;
- data da transação;
- área construída;
- CEP;
- uso cadastral do imóvel;
- padrão construtivo;
- fração ideal;
- ano de conclusão da construção;
- Valor Venal de Referência;
- Base de Cálculo do ITBI;
- informações de financiamento;
- informações cadastrais do imóvel.

---

## 🎯 Recorte utilizado

O funil final aplica sequencialmente os seguintes critérios:

| Etapa | Registros |
|---|---:|
| Base original — guias pagas em 2025 | 230.525 |
| Natureza da transação: compra e venda | 205.844 |
| Compra e venda + Uso IPTU 20 — apartamento em condomínio | 68.486 |
| Transmissão integral — proporção transmitida de 100% | 64.951 |
| Data de Transação pertencente a 2025 | 64.227 |
| Após exclusão da união das anomalias econômicas severas | **63.140** |

Durante a análise de qualidade foram utilizados dois critérios para sinalizar
anomalias econômicas severas:

- valor por m² inferior a **R$ 100**;
- razão entre valor de transação e VVR proporcional inferior a **0,10**.

No recorte com Data de Transação em 2025, foram encontrados:

| Flag de qualidade | Registros |
|---|---:|
| `valor_m2 < 100` | 1.018 |
| `razao_transacao_vvr < 0,10` | 301 |
| Interseção das duas flags | 232 |
| União das duas flags | 1.087 |

A exclusão utiliza a união dessas duas flags. VVR proporcional igual a zero não
constitui uma regra adicional de exclusão. A base processada com 64.227 registros
é preservada; o conjunto de Machine Learning utiliza os 63.140 registros
economicamente válidos.

---

## 🎯 Variável alvo

O modelo busca estimar:

**Valor de Transação (declarado pelo contribuinte)**

Portanto, a previsão representa uma estimativa do **valor declarado na transação imobiliária**.

Ela não representa necessariamente:

- valor venal;
- preço de mercado;
- preço de anúncio;
- avaliação bancária;
- laudo imobiliário profissional.

---

## 🧩 Variáveis utilizadas pelo modelo

O dataset final de Machine Learning possui **63.140 registros**. O modelo utiliza
cinco variáveis, nesta ordem:

| Variável | Descrição |
|---|---|
| `Área Construída (m2)` | Área construída do imóvel em metros quadrados |
| `cep4` | Quatro primeiros dígitos do CEP, utilizados como aproximação da localização |
| `Padrão (IPTU)` | Código do padrão construtivo cadastrado no IPTU |
| `idade_imovel` | Idade calculada a partir do ano de conclusão da construção |
| `Fração Ideal` | Participação da unidade no terreno e nas áreas comuns do condomínio |

Variáveis categóricas:

- `cep4`;
- `Padrão (IPTU)`.

Variáveis numéricas:

- `Área Construída (m2)`;
- `idade_imovel`;
- `Fração Ideal`.

A idade do imóvel é calculada como:

```text
2025 - Ano de Conclusão da Construção
```

O **CEP4** é derivado automaticamente a partir dos quatro primeiros dígitos do CEP.

Exemplo:

```text
CEP: 04303-000
CEP4: 0430
```

A variável `mes_transacao` foi avaliada experimentalmente, mas não integra o
contrato final do modelo.

---

## 🔒 Prevenção de vazamento de dados

Algumas variáveis presentes na base oficial foram deliberadamente excluídas da
modelagem por apresentarem risco de **data leakage**, por derivarem do próprio
alvo ou por estarem relacionadas ao cálculo tributário da transação.

Entre elas:

- VVR;
- VVR proporcional;
- Base de Cálculo;
- `valor_m2`;
- `razao_transacao_vvr`;
- Valor Financiado.

Esses campos não fazem parte das features finais. A exclusão protege a validade
da avaliação preditiva; ela não sustenta afirmações causais sobre as variáveis.

---

## ⏱️ Estratégia de validação temporal

Como os registros possuem uma dimensão temporal, foi utilizada uma estratégia de validação baseada no tempo, evitando uma divisão aleatória simples.

### Seleção do modelo

| Partição | Janela definida | Registros |
|---|---|---:|
| Treino | 01/01/2025 a 31/10/2025 | 52.807 |
| Validação | 01/11/2025 a 30/11/2025 | 4.902 |
| Teste final reservado | 01/12/2025 a 31/12/2025 | 5.431 |

A arquitetura utiliza `build_selection_split()`, que consulta e materializa
somente treino e validação nos fluxos de comparação e tuning. Os registros e os
targets de dezembro não são materializados nesses fluxos.

Dezembro não participou:

- do tuning;
- da seleção de features;
- da escolha dos hiperparâmetros.

### Avaliação final

Depois do congelamento do modelo, a avaliação oficial utilizou:

| Partição | Período | Registros |
|---|---|---:|
| Treino final | Janeiro a novembro de 2025 | 57.709 |
| Teste independente | Dezembro de 2025 | 5.431 |

O modelo foi congelado antes da abertura do teste independente. A avaliação de
dezembro foi realizada somente após o encerramento da seleção.

---

## 🤖 Modelos avaliados

Foram comparados diferentes modelos de regressão:

- Dummy Regressor;
- Regressão Linear;
- Random Forest;
- XGBoost.

### Comparação na validação de novembro de 2025

| Modelo | MAE | RMSE | R² |
|---|---:|---:|---:|
| Dummy Regressor | R$ 445.690,03 | R$ 1.359.439,91 | -0,0464 |
| Regressão Linear | R$ 312.417,38 | R$ 859.369,42 | 0,5818 |
| Random Forest | R$ 185.435,77 | R$ 658.238,14 | 0,7547 |
| XGBoost inicial com mês | R$ 184.440,95 | R$ 481.673,15 | 0,8686 |
| XGBoost inicial sem mês | R$ 181.962,60 | R$ 463.993,37 | 0,8781 |
| XGBoost ajustado | **R$ 170.133,00** | **R$ 462.107,92** | **0,8791** |

Esses resultados pertencem exclusivamente à **validação de novembro de 2025**.
Eles não são as métricas do teste final de dezembro.

### Experimento com e sem mês da transação

Durante os experimentos também foi avaliado o uso do **mês da transação** como variável preditora.

| Configuração inicial | MAE | RMSE | R² |
|---|---:|---:|---:|
| Com `mes_transacao` | R$ 184.440,95 | R$ 481.673,15 | 0,8686 |
| Sem `mes_transacao` | R$ 181.962,60 | R$ 463.993,37 | 0,8781 |

Diferença da versão sem mês menos a versão com mês:

- MAE: **-R$ 2.478,35**;
- RMSE: **-R$ 17.679,78**;
- R²: **+0,0095**.

A versão sem mês apresentou melhor desempenho nas três métricas dessa validação.
Por esse motivo, `mes_transacao` foi removida do contrato final.

### Configuração selecionada

O modelo selecionado é um `XGBRegressor`. O critério principal de seleção foi o
**MAE**.

```text
objective = reg:squarederror
max_depth = 8
learning_rate = 0.05
n_estimators = 800
min_child_weight = 1
subsample = 0.8
colsample_bytree = 0.8
reg_lambda = 1.0
tree_method = hist
random_state = 42
n_jobs = -1
```

### Backtest temporal dos finalistas

Três candidatos foram comparados em cinco janelas expansivas, com validações
mensais de julho a novembro de 2025:

- **A:** profundidade 8 e 800 árvores;
- **B:** profundidade 8 e 500 árvores;
- **C:** profundidade 6 e 800 árvores.

Todos utilizaram `learning_rate = 0.05` e as mesmas demais definições do pipeline.

| Candidato | MAE médio | Desvio do MAE | RMSE médio | R² médio | Vitórias por MAE |
|---|---:|---:|---:|---:|---:|
| A — depth 8 / 800 | **R$ 176.534,01** | R$ 6.196,59 | R$ 589.959,80 | 0,7884 | **5/5** |
| B — depth 8 / 500 | R$ 181.243,01 | R$ 6.974,05 | R$ 589.726,03 | 0,7894 | 0/5 |
| C — depth 6 / 800 | R$ 182.209,50 | R$ 6.916,13 | **R$ 586.767,62** | **0,7910** | 0/5 |

O candidato A foi escolhido pelo menor MAE médio e venceu por MAE nas cinco
janelas. O candidato C obteve RMSE e R² médios ligeiramente melhores; portanto,
A não foi superior em todas as métricas. A decisão seguiu o critério de MAE
definido previamente.

---

## 📈 Avaliação final

A avaliação temporal independente foi realizada depois do congelamento do
modelo, com 57.709 registros de janeiro a novembro no treino e 5.431 registros
de dezembro de 2025 no teste.

| Métrica | Resultado |
|---|---:|
| MAE | R$ 231.947,92 |
| RMSE | R$ 1.091.963,08 |
| R² | 0,5730 |
| Mediana do erro absoluto | R$ 84.607,78 |

Esses são os resultados oficiais do teste independente de dezembro. Eles
pertencem ao modelo de avaliação e não foram substituídos por métricas do modelo
de produção treinado posteriormente.

### MAE

O **MAE — Mean Absolute Error** representa o erro absoluto médio entre o valor real e o valor previsto pelo modelo.

Valores menores indicam menor erro médio.

### RMSE

O **RMSE — Root Mean Squared Error** atribui maior peso a erros elevados e, por isso, é mais sensível a observações extremas.

### R²

O **R² — Coeficiente de Determinação** indica quanto da variação observada nos valores dos imóveis é explicada pelas previsões do modelo.

Valores mais próximos de 1 representam maior capacidade explicativa.

---

## 🔎 Análise dos erros

A análise do conjunto temporal independente mostrou que o comportamento do modelo varia de acordo com a faixa de valor dos imóveis.

- a mediana do erro absoluto foi de **R$ 84.607,78**;
- **53,31%** das previsões ficaram acima do valor real;
- na faixa de R$ 300 mil a R$ 500 mil, o MAE foi de **R$ 89.352,55**;
- os 76 imóveis com valor declarado a partir de R$ 5 milhões, equivalentes a
  1,40% do teste, apresentaram MAE de **R$ 3.585.343,55**;
- os maiores erros observados concentraram-se em imóveis com áreas
  excepcionalmente grandes.

Essas associações descrevem o teste de dezembro e não demonstram causalidade.
O MAE é uma média do conjunto avaliado, não uma margem de erro individual.

---

## 🧠 Importância das variáveis

Foi utilizada `sklearn.inspection.permutation_importance` no teste independente,
com `scoring="neg_mean_absolute_error"`, `n_repeats=10` e `random_state=42`.

| Variável | Aumento médio do MAE | Desvio |
|---|---:|---:|
| Área Construída | R$ 460.785,14 | ± R$ 6.331,58 |
| CEP4 | R$ 124.343,02 | ± R$ 3.620,19 |
| `idade_imovel` | R$ 82.576,24 | ± R$ 5.289,14 |
| Padrão IPTU | R$ 23.649,95 | ± R$ 1.499,60 |
| Fração Ideal | R$ 15.721,82 | ± R$ 2.524,52 |

A técnica mede quanto o MAE piora quando os valores de uma variável são
embaralhados. **Importância preditiva não representa causalidade.**

---

## 🏭 Modelo de avaliação e modelo de produção

Os dois modelos possuem a mesma arquitetura, preprocessing, features e
hiperparâmetros, mas cumprem papéis diferentes:

| Modelo | Treinamento | Avaliação | Finalidade |
|---|---:|---:|---|
| Modelo de avaliação | 57.709 registros de jan–nov/2025 | 5.431 registros de dez/2025 | Produzir as métricas oficiais do teste independente |
| Modelo de produção | 63.140 registros válidos de 2025 | Sem holdout interno para novas métricas oficiais | Realizar inferências na aplicação |

O modelo de produção foi treinado somente depois do encerramento da avaliação.
Seus artefatos são:

```text
artifacts/apartment_price_model.joblib
artifacts/model_metadata.json
```

O metadata registra separadamente os resultados oficiais da avaliação e o
contexto de treinamento do artefato de produção.

---

## 🖥️ Aplicação interativa

O projeto possui uma aplicação desenvolvida com **Streamlit**.

Ela é dividida em três páginas principais:

1. Visão Geral;
2. Modelo;
3. Estimador.

---

### 📊 Visão Geral

A página permite explorar as transações por meio de filtros dinâmicos.

Filtros disponíveis:

- faixa de preço;
- mês da transação;
- padrão IPTU;
- área mínima;
- área máxima;
- CEP4.

São apresentados indicadores como:

- quantidade de apartamentos no recorte;
- valor mediano;
- área mediana;
- valor mediano por m².

Também são apresentados gráficos de:

- transações por mês;
- valor mediano por mês;
- distribuição por faixa de preço.

Os indicadores e gráficos são atualizados conforme os filtros selecionados.

---

### 🤖 Modelo

A página dedicada ao modelo apresenta:

- métricas finais do teste independente;
- comparação dos modelos na validação de novembro;
- análise dos erros;
- permutation importance;
- configuração final do XGBoost;
- limitações observadas.

As métricas principais correspondem à avaliação temporal independente realizada com dezembro de 2025.

---

### 🏠 Estimador

O Estimador produz uma estimativa do **valor de transação declarado pelo
contribuinte** a partir das seguintes entradas:

- Área Construída;
- CEP;
- Padrão IPTU;
- ano de conclusão da construção — ACC;
- Fração Ideal.

O sistema deriva automaticamente:

```text
CEP → CEP4
ACC → idade_imovel
```

O modelo então gera:

- valor de transação estimado;
- valor estimado por m².

Também são apresentados os dados utilizados na previsão e avisos relacionados às limitações do modelo.

A estimativa é estatística, refere-se ao valor declarado e não substitui uma
avaliação imobiliária profissional.

---

## 📁 Estrutura do projeto

```text
pi4-imoveis-sp/
│
├── app/
│   ├── app.py
│   ├── components/
│   └── pages/
│       ├── overview.py
│       ├── model.py
│       └── estimator.py
│
├── artifacts/
│   ├── apartment_price_model.joblib
│   └── model_metadata.json
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── notebooks/
│
├── scripts/
│
├── src/
│   └── pi4_imoveis_sp/
│       ├── analysis/
│       │   ├── estimator.py
│       │   └── overview.py
│       ├── data/
│       ├── features/
│       ├── ml/
│       ├── presentation.py
│       └── visualization.py
│
├── tests/
│
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 🛠️ Tecnologias utilizadas

As principais tecnologias utilizadas são:

### Ciência de Dados e Machine Learning

- Python;
- Polars;
- Pandas;
- Scikit-learn;
- XGBoost;
- PyArrow;
- Joblib.

### Aplicação e visualização

- Streamlit;
- Plotly.

### Qualidade e desenvolvimento

- Pytest;
- Ruff;
- uv;
- Git;
- GitHub.

---

## ⚙️ Preparação do ambiente

O projeto utiliza o gerenciador de dependências **uv**.

Após clonar o repositório, execute:

```powershell
uv sync
```

Esse comando prepara o ambiente virtual e instala as dependências declaradas no projeto.

---

## 📥 Reprodução do pipeline

O arquivo original de dados deve ser obtido na página oficial da Prefeitura de São Paulo e salvo como:

```text
data/raw/itbi_2025.xlsx
```

A partir dele, o pipeline pode ser executado pelas etapas abaixo.

---

### 1. Construção da base intermediária

Consolida as planilhas mensais do arquivo original e gera uma base intermediária em formato Parquet.

```powershell
uv run python scripts/build_interim.py
```

Validação:

```powershell
uv run python scripts/validate_interim.py
```

Arquivo gerado:

```text
data/interim/itbi_2025.parquet
```

---

### 2. Construção da base processada

Aplica o recorte utilizado no projeto, cria variáveis derivadas e identifica registros com anomalias econômicas.

```powershell
uv run python scripts/build_processed.py
```

Validação:

```powershell
uv run python scripts/validate_processed.py
```

Arquivo gerado:

```text
data/processed/apartments_2025.parquet
```

---

### 3. Preparação e validação do conjunto de Machine Learning

O conjunto destinado à modelagem pode ser inspecionado com:

```powershell
uv run python scripts/profile_ml_dataset.py
```

A separação temporal utilizada durante o desenvolvimento pode ser validada com:

```powershell
uv run python scripts/validate_ml_split.py
```

O validador verifica tanto o split estrutural completo quanto o contrato de
`build_selection_split()`. Nos fluxos de seleção, essa API materializa somente
treino de janeiro a outubro e validação de novembro; dezembro permanece fora
desses objetos.

---

### 4. Comparação dos modelos

Os modelos iniciais podem ser executados separadamente.

#### Baseline

```powershell
uv run python scripts/train_baseline.py
```

#### Random Forest

```powershell
uv run python scripts/train_random_forest.py
```

#### XGBoost

```powershell
uv run python scripts/train_xgboost.py
```

Também foi analisado o efeito da variável referente ao mês da transação:

```powershell
uv run python scripts/compare_xgboost_month.py
```

---

### 5. Ajuste e seleção do XGBoost

A busca de hiperparâmetros é executada por:

```powershell
uv run python scripts/tune_xgboost.py
```

Os modelos finalistas são posteriormente comparados em diferentes períodos temporais:

```powershell
uv run python scripts/backtest_xgboost_finalists.py
```

Esse procedimento foi utilizado para escolher a configuração final antes da avaliação temporal independente.

---

### 6. Avaliação final

Após a definição da configuração do modelo, a avaliação temporal final é executada por:

```powershell
uv run python scripts/evaluate_final_model.py
```

O conjunto de dezembro de 2025 foi mantido separado durante a etapa de seleção e utilizado como teste independente.

#### Análise dos erros

```powershell
uv run python scripts/analyze_final_errors.py
```

#### Importância das variáveis

```powershell
uv run python scripts/analyze_feature_importance.py
```

---

### 7. Construção do modelo de produção

Após o encerramento da avaliação, o modelo utilizado pela aplicação é treinado com todos os registros economicamente válidos de 2025:

```powershell
uv run python scripts/build_production_model.py
```

Esse processo gera:

```text
artifacts/apartment_price_model.joblib
artifacts/model_metadata.json
```

Validação:

```powershell
uv run python scripts/validate_production_model.py
```

---

### 8. Executando a aplicação

Com os dados processados e o modelo de produção disponíveis:

```powershell
uv run streamlit run app/app.py
```

O Streamlit disponibilizará um endereço local para acesso pelo navegador.

---

## 🔬 Scripts de exploração e auditoria

Além do pipeline principal, o projeto possui scripts utilizados durante a exploração, investigação da qualidade dos dados e desenvolvimento metodológico.

Entre eles:

```text
inspect_itbi.py
profile_apartments.py
profile_model_dataset.py
profile_quality.py
```

Esses scripts não são necessários para executar a aplicação, mas registram etapas de investigação realizadas durante o desenvolvimento.

---

## ✅ Testes automatizados

O projeto utiliza **Pytest**.

Atualmente são testados:

- formatação de moeda e números;
- apresentação dos padrões IPTU;
- contrato das variáveis utilizadas pelo modelo;
- exclusão de variáveis com risco de leakage;
- estrutura dos dados enviados ao pipeline de inferência;
- filtros da Visão Geral;
- faixas de preço;
- tratamento das anomalias econômicas;
- restrição da Data de Transação ao ano de 2025;
- isolamento temporal entre seleção, validação e teste;
- metadados e configuração do modelo de produção;
- normalização de CEP;
- formatação de CEP;
- opções de padrão utilizadas pelo Estimador.

Para executar todos os testes:

```powershell
uv run pytest -v
```

Estado atual:

**50 testes aprovados**

---

## 🧹 Qualidade de código

O projeto utiliza **Ruff** para análise estática e formatação dos arquivos Python.

### Formatar todo o projeto

```powershell
uv run ruff format .
```

### Verificar o código

```powershell
uv run ruff check .
```

### Aplicar correções automáticas suportadas

```powershell
uv run ruff check . --fix
```

### Confirmar a formatação

```powershell
uv run ruff format --check .
```

---

## ⚠️ Limitações

Algumas limitações devem ser consideradas:

- a fonte reúne guias de ITBI pagas em 2025;
- a modelagem restringe a Data de Transação ao ano de 2025;
- o alvo é o valor de transação declarado pelo contribuinte e não equivale
  necessariamente ao preço de mercado;
- o CEP4 é uma aproximação da localização e não representa exatamente bairros ou microrregiões imobiliárias;
- algumas informações cadastrais apresentam inconsistências na base original;
- o desempenho foi pior na cauda de imóveis de alto valor do teste;
- alguns padrões menos frequentes apresentaram desempenho inferior;
- o modelo não dispõe de dormitórios, vagas dedicadas, andar, estado de
  conservação, vista ou características internas do imóvel;
- a qualidade da previsão depende das características informadas pelo usuário;
- o MAE e as demais métricas globais não representam uma margem de erro fixa
  para cada imóvel;
- o resultado de dezembro de 2025 não garante o mesmo desempenho em outros
  períodos;
- permutation importance mede associação preditiva no modelo e não causalidade;
- os resultados representam estimativas estatísticas.

---

## ⚖️ Uso responsável

O sistema possui finalidade **acadêmica e experimental**.

As estimativas não devem ser utilizadas isoladamente para decisões:

- financeiras;
- tributárias;
- jurídicas;
- comerciais;
- de compra ou venda de imóveis.

O sistema não substitui um laudo ou avaliação imobiliária profissional.

---

## 🚧 Status do projeto

| Etapa | Status |
|---|---|
| Coleta e exploração dos dados | ✅ Concluída |
| Pipeline de tratamento dos dados | ✅ Concluído |
| Engenharia de atributos | ✅ Concluída |
| Modelagem | ✅ Concluída |
| Avaliação temporal final | ✅ Concluída |
| Modelo de produção | ✅ Gerado e validado |
| Interpretação | ✅ Concluída |
| Aplicação — dashboard e estimador | ✅ Concluída |
| Testes automatizados | ✅ Concluída |
| Documentação técnica | 🔄 Em finalização |

Esse status se refere ao software e ao pipeline técnico. O Relatório Parcial e o
Relatório Final são etapas acadêmicas externas ao repositório e não são tratados
como concluídos por esta tabela.

---

## 🎓 Projeto acadêmico

Projeto desenvolvido no curso de **Ciência de Dados da UNIVESP**, como parte das atividades do **Projeto Integrador IV**.

Os dados utilizados são públicos e disponibilizados pela **Prefeitura de São Paulo**.

---

## 📄 Licença e finalidade

Este repositório foi desenvolvido para fins acadêmicos.

Os dados utilizados pertencem às respectivas fontes públicas responsáveis por sua disponibilização.

As previsões produzidas pela aplicação possuem caráter experimental e não constituem avaliação profissional de imóveis.
