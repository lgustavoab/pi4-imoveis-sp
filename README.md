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

O arquivo contém registros mensais de janeiro a dezembro de 2025.

Por questões de tamanho e organização do repositório, o arquivo bruto não é versionado no Git.

Após o download, ele deve ser salvo como:

```text
data/raw/itbi_2025.xlsx
```

---

## 📊 Base original

A base completa de 2025 contém:

**230.525 registros**

distribuídos entre os doze meses do ano.

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

O projeto foi direcionado principalmente para transações com as seguintes características:

- **Natureza da transação:** Compra e venda;
- **Uso IPTU:** 20 — Apartamento em condomínio;
- **Proporção transmitida:** 100%.

Esse recorte resultou inicialmente em:

**64.951 registros**

Durante a análise de qualidade foram identificadas transações com fortes indícios de inconsistência econômica.

Foram utilizados dois critérios principais para sinalizar anomalias severas:

- valor por m² inferior a **R$ 100**;
- valor de transação inferior a **10% do Valor Venal de Referência proporcional**.

Após a exclusão desses registros do conjunto destinado à modelagem, a base principal ficou com:

**63.807 registros**

A base completa do recorte foi preservada para fins de análise.

---

## 🎯 Variável alvo

O modelo busca estimar:

**Valor de Transação (declarado pelo contribuinte)**

Portanto, a previsão representa uma estimativa do **valor declarado na transação imobiliária**.

Ela não representa necessariamente:

- valor venal;
- preço de anúncio;
- avaliação bancária;
- laudo imobiliário profissional.

---

## 🧩 Variáveis utilizadas pelo modelo

O modelo final utiliza cinco variáveis:

| Variável | Descrição |
|---|---|
| Área construída | Área construída do imóvel em metros quadrados |
| CEP4 | Quatro primeiros dígitos do CEP, utilizados como aproximação da localização |
| Padrão IPTU | Código do padrão construtivo cadastrado no IPTU |
| Idade do imóvel | Calculada a partir do ano de conclusão da construção |
| Fração ideal | Participação da unidade no terreno e nas áreas comuns do condomínio |

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

---

## 🔒 Prevenção de vazamento de dados

Algumas variáveis presentes na base oficial foram deliberadamente excluídas da modelagem por apresentarem risco de **data leakage** ou por estarem diretamente relacionadas ao cálculo tributário da própria transação.

Entre elas:

- Valor Venal de Referência;
- Valor Venal de Referência proporcional;
- Base de Cálculo adotada;
- Valor Financiado;
- Valor por m²;
- Razão entre valor de transação e VVR.

O objetivo é evitar que o modelo utilize informações que revelem direta ou indiretamente o valor que deveria prever.

---

## ⏱️ Estratégia de validação temporal

Como os registros possuem uma dimensão temporal, foi utilizada uma estratégia de validação baseada no tempo, evitando uma divisão aleatória simples.

Durante a etapa inicial de desenvolvimento:

```text
Treinamento: janeiro a outubro de 2025
Validação: novembro de 2025
Teste final: dezembro de 2025
```

Após a escolha da configuração final, a avaliação oficial foi realizada com:

```text
Treinamento: janeiro a novembro de 2025
Teste independente: dezembro de 2025
```

O conjunto de dezembro permaneceu separado durante a seleção do modelo e não foi utilizado para ajuste de hiperparâmetros.

---

## 🤖 Modelos avaliados

Foram comparados diferentes modelos de regressão:

- Dummy Regressor;
- Regressão Linear;
- Random Forest;
- XGBoost.

O XGBoost apresentou o melhor desempenho geral durante a etapa de seleção.

Durante os experimentos também foi avaliado o uso do **mês da transação** como variável preditora.

O desempenho foi melhor sem essa variável, portanto ela foi retirada da configuração final.

### Configuração selecionada

Principais hiperparâmetros:

```text
max_depth = 8
learning_rate = 0.05
n_estimators = 800
subsample = 0.8
colsample_bytree = 0.8
```

A configuração final também utiliza:

```text
objective = reg:squarederror
min_child_weight = 1
reg_lambda = 1
tree_method = hist
random_state = 42
```

---

## 📈 Avaliação final

A avaliação temporal independente foi realizada utilizando as transações de **dezembro de 2025**.

| Métrica | Resultado |
|---|---:|
| MAE | R$ 228.857,12 |
| RMSE | R$ 1.044.652,29 |
| R² | 0,5890 |

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

A mediana do erro absoluto em dezembro ficou em aproximadamente:

**R$ 83 mil**

Isso significa que metade das previsões apresentou erro absoluto inferior a aproximadamente esse valor.

Os maiores erros ficaram concentrados principalmente nos imóveis de valor muito elevado.

Imóveis acima de:

**R$ 5 milhões**

apresentaram erros consideravelmente maiores que as faixas de valores mais comuns da base.

Por esse motivo, estimativas nessa faixa devem ser interpretadas com maior cautela.

---

## 🧠 Importância das variáveis

Foi utilizada **Permutation Importance** para analisar a contribuição preditiva das variáveis.

A ordem observada foi:

1. Área construída;
2. CEP4;
3. Idade do imóvel;
4. Padrão IPTU;
5. Fração ideal.

A técnica avalia quanto o desempenho do modelo piora quando os valores de uma variável são embaralhados.

Quanto maior a perda de desempenho, maior sua importância para as previsões do modelo.

Esses resultados representam **importância preditiva** e não devem ser interpretados como relações causais.

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

- MAE;
- RMSE;
- R²;
- explicação das métricas;
- comparação entre os modelos avaliados;
- importância das variáveis;
- configuração final do XGBoost;
- limitações observadas.

As métricas principais correspondem à avaliação temporal independente realizada com dezembro de 2025.

---

### 🏠 Estimador

O Estimador permite realizar uma nova previsão informando:

- área construída;
- CEP;
- ano de conclusão da construção;
- padrão construtivo do IPTU;
- fração ideal.

O sistema deriva automaticamente:

```text
CEP → CEP4
Ano de conclusão → Idade do imóvel
```

O modelo então gera:

- valor de transação estimado;
- valor estimado por m².

Também são apresentados os dados utilizados na previsão e avisos relacionados às limitações do modelo.

A estimativa é estatística e não substitui uma avaliação imobiliária profissional.

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
- normalização de CEP;
- formatação de CEP;
- opções de padrão utilizadas pelo Estimador.

Para executar todos os testes:

```powershell
uv run pytest -v
```

Estado atual:

**35 testes aprovados**

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

- o modelo utiliza apenas transações registradas em 2025;
- o CEP4 é uma aproximação da localização e não representa exatamente bairros ou microrregiões imobiliárias;
- algumas informações cadastrais apresentam inconsistências na base original;
- imóveis de alto valor apresentaram erros maiores;
- alguns padrões menos frequentes apresentaram desempenho inferior;
- o modelo não utiliza características como dormitórios, vagas, andar, estado de conservação ou infraestrutura do condomínio;
- a qualidade da previsão depende das características informadas pelo usuário;
- as métricas globais não representam uma margem de erro fixa para cada imóvel;
- o valor estimado representa o valor de transação declarado e não necessariamente o preço de mercado;
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
| Tratamento dos dados | ✅ Concluída |
| Engenharia de atributos | ✅ Concluída |
| Modelagem | ✅ Concluída |
| Avaliação temporal | ✅ Concluída |
| Modelo de produção | ✅ Concluída |
| Interpretação | ✅ Concluída |
| Dashboard | ✅ Concluída |
| Estimador | ✅ Concluída |
| Testes automatizados | ✅ Concluída |
| README e documentação técnica | ✅ Concluída |

---

## 🎓 Projeto acadêmico

Projeto desenvolvido no curso de **Ciência de Dados da UNIVESP**, como parte das atividades do **Projeto Integrador IV**.

Os dados utilizados são públicos e disponibilizados pela **Prefeitura de São Paulo**.

---

## 📄 Licença e finalidade

Este repositório foi desenvolvido para fins acadêmicos.

Os dados utilizados pertencem às respectivas fontes públicas responsáveis por sua disponibilização.

As previsões produzidas pela aplicação possuem caráter experimental e não constituem avaliação profissional de imóveis.