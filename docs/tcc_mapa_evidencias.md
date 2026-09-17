# Mapa de evidências — Projeto Integrador IV

> Estado investigado: branch `main`, commit
> `1c5fb405334557af62ef86553706aef5dd6825ea`, em 17/09/2026.
> “Execução reproduzida” indica confirmação no ambiente local sem alterar código,
> dados ou artefatos. Artefatos locais e Parquets são ignorados pelo Git.

| ID | Informação | Valor/resultado | Tipo de evidência | Fonte | Localização | Seção provável do relatório | Observação |
|---|---|---|---|---|---|---|---|
| EV-001 | Estado Git investigado | `main` em `1c5fb40` | Git | repositório local | `git rev-parse HEAD` | Metodologia/Rastreabilidade | HEAD também é `origin/main`. |
| EV-002 | Repositório remoto | `lgustavoab/pi4-imoveis-sp` | Configuração Git | `.git/config` | `git remote -v` | Ferramentas | Não comprova Issues, Actions ou PRs. |
| EV-003 | Fonte pública | Prefeitura de São Paulo — Guias de ITBI pagas em 2025 | Documentação + código | `README.md`; ingestão | seção Fonte; constantes | Fonte dos dados | Ano do pagamento não equivale automaticamente à Data de Transação. |
| EV-004 | Arquivo bruto | `GUIAS DE ITBI PAGAS (28012026) XLS.xlsx` → `data/raw/itbi_2025.xlsx` | Documentação/local | README; arquivo ignorado | Fonte/preparação | Fonte dos dados | Não versionado. |
| EV-005 | Abas mensais | 12, de JAN a DEZ/2025 | Código + execução | `ingestion.py`; validador | `MONTH_SHEETS` | Ingestão | Abas auxiliares não entram no Parquet. |
| EV-006 | Base intermediária | 230.525 × 30 | Execução reproduzida | `validate_interim.py`; Parquet | saída do validador | Dados | 28 oficiais + `source_sheet`/`source_month`. |
| EV-007 | Rastreabilidade | `source_sheet` e `source_month`, sem nulos | Execução reproduzida | `validate_interim.py` | seções 3 e 7 | Dados | Preservam origem da guia. |
| EV-008 | Data vs mês da fonte | 8.648 divergências em 64.227 processados | Execução reproduzida | Parquet processado | comparação `dt.month`/`source_month` | Metodologia | Justifica distinguir pagamento e transação. |
| EV-009 | Data vs mês entre válidos | 8.052 divergências em 63.140 | Execução reproduzida | Parquet processado | filtro econômico + comparação | Metodologia | Split usa Data de Transação. |
| EV-010 | Base original | 230.525 | Execução reproduzida | Parquet intermediário | contagem | Funil | Primeiro nível do funil. |
| EV-011 | Compra e venda | 205.844 | Execução reproduzida | Parquet intermediário | filtro de natureza | Funil | Regra exata do código. |
| EV-012 | Compra/venda + Uso 20 | 68.486 | Execução reproduzida | Parquet intermediário | filtros sequenciais | Funil | Uso 20 = apartamento em condomínio. |
| EV-013 | Transmissão integral | 64.951 | Execução reproduzida | Parquet intermediário | proporção 100% | Funil | Tolerância `< 1e-9`. |
| EV-014 | Data de Transação em 2025 | 64.227 | Código + execução | `cleaning.py`; validador | `filter_transaction_year` | Funil/Metodologia | Correção introduzida em `a3132f6`. |
| EV-015 | Intervalo processado | 02/01/2025–31/12/2025 | Execução reproduzida | `validate_processed.py` | escopo | Dados | Janela definida começa em 01/01. |
| EV-016 | Dataset processado | 64.227 × 37 | Execução reproduzida | `validate_processed.py` | dimensões | Dados | Preserva linhas sinalizadas. |
| EV-017 | Flag valor/m² | 1.018 com `valor_m2 < 100` | Código + execução | `cleaning.py`; validador | `add_quality_flags` | Qualidade | Limiar humano não explicitamente versionado. |
| EV-018 | Flag razão/VVR | 301 com razão `< 0,10` | Código + execução | mesmos | mesma função | Qualidade | Usa VVR proporcional. |
| EV-019 | Interseção das flags | 232 | Execução reproduzida | `validate_processed.py` | seção flags | Qualidade | Casos com ambas. |
| EV-020 | União das flags | 1.087 | Execução reproduzida | `validate_processed.py` | seção flags | Qualidade | Conjunto excluído da modelagem. |
| EV-021 | Dataset válido | 63.140 | Código + execução | `dataset.py`; validador | `build_model_dataset` | Dataset final | 64.227 − 1.087. |
| EV-022 | VVR zero processado | 1.236 | Execução reproduzida | Parquet processado | filtro VVR proporcional zero | Qualidade | Não é regra de exclusão. |
| EV-023 | VVR zero válido | 450 | Execução reproduzida | Parquet processado | filtro válido + VVR zero | Limitações | Achado atual solicitado. |
| EV-024 | Razão infinita | 450 entre válidos | Execução reproduzida | Parquet processado | `is_infinite` | Limitações | Divisão por VVR zero. |
| EV-025 | Tratamento do VVR zero | Mantido; não ativa `< 0,10` | Código + dados | `cleaning.py`; Parquet | expressão da flag | Decisões | Não decidir exclusão agora. |
| EV-026 | Target | Valor de Transação (declarado pelo contribuinte) | Código + metadata | `dataset.py`; JSON | `TARGET_COLUMN`; `target` | Metodologia | Não equivale necessariamente a mercado. |
| EV-027 | Features finais | área, CEP4, padrão, idade, fração | Código/teste/metadata | `dataset.py`; testes; JSON | `FEATURE_COLUMNS_WITHOUT_MONTH` | Metodologia | Ordem fixa. |
| EV-028 | Categóricas | `cep4`, `Padrão (IPTU)` | Código/teste/metadata | mesmos | `CATEGORICAL_FEATURES` | Metodologia | One-hot encoding. |
| EV-029 | Numéricas | área, idade, fração | Código/teste/metadata | mesmos | `NUMERICAL_FEATURES_WITHOUT_MONTH` | Metodologia | Passthrough nas árvores. |
| EV-030 | Idade | `2025 - ACC` | Código | `cleaning.py` | `add_derived_features` | Engenharia | Referência fixa no ano do estudo. |
| EV-031 | CEP4 | quatro primeiros dígitos; 397 categorias | Código + execução | `cleaning.py`; validador | derivação/CEP | Engenharia | Aproximação espacial. |
| EV-032 | Mês experimental | existe em `FEATURE_COLUMNS`, fora do contrato final | Código + testes | `dataset.py`; `test_dataset.py` | contratos | Engenharia | Continua auxiliar em análises. |
| EV-033 | Campos de leakage | VVRs, base, financiado, valor/m², razão | Código/teste | `dataset.py`; teste | `LEAKAGE_COLUMNS` | Leakage | Nenhum nas features finais. |
| EV-034 | OHE | `infrequent_if_exist`, frequência mínima 10 | Código | preprocessors | `build_preprocessor` | Modelagem | CEP4/Padrão. |
| EV-035 | Escopo anual validado | datas nulas/fora de 2025 são rejeitadas | Código/teste | `dataset.py`; testes temporais | `validate_model_temporal_scope` | Qualidade | Contrato novo. |
| EV-036 | Split de seleção | objeto com quatro campos, sem teste | Código/teste | `split.py`; testes | `SelectionSplit` | Metodologia | Isolamento arquitetural. |
| EV-037 | Treino da seleção | 52.807, 02/01–31/10/2025 | Execução reproduzida | `validate_ml_split.py` | tamanhos/intervalos | Metodologia | Janela definida desde 01/01. |
| EV-038 | Validação da seleção | 4.902, 01–30/11/2025 | Execução reproduzida | mesmo | mesmos | Metodologia | Usada para comparação/tuning. |
| EV-039 | Dezembro na seleção | não selecionado nem materializado | Código/teste/execução | `split.py`; testes; validador | `build_selection_split` | Metodologia | Consulta encerra em 01/12. |
| EV-040 | Teste estrutural | 5.431, 01–31/12/2025 | Execução reproduzida | `validate_ml_split.py` | teste | Avaliação | Reservado até congelamento. |
| EV-041 | Partições disjuntas | cobertura 63.140 e ordem cronológica | Código/teste | `split.py`; testes | validação de partições | Metodologia | Sem sobreposição. |
| EV-042 | API migrada | baseline/RF/XGB/tuning usam selection split | Código/Git | módulos ML; `ee8a5cf` | chamadas | Metodologia | Não retornam teste. |
| EV-043 | Dummy | MAE 445.690,03; RMSE 1.359.439,91; R² -0,0464 | Execução reproduzida | `train_baseline.py` | saída | Resultados | Novembro. |
| EV-044 | Regressão Linear | MAE 312.417,38; RMSE 859.369,42; R² 0,5818 | Execução reproduzida | mesmo | saída | Resultados | Novembro. |
| EV-045 | Random Forest | MAE 185.435,77; RMSE 658.238,14; R² 0,7547 | Execução reproduzida | `train_random_forest.py` | saída | Resultados | 200 árvores, folha 2. |
| EV-046 | XGB inicial com mês | 184.440,95; 481.673,15; 0,8686 | Execução reproduzida | `compare_xgboost_month.py` | saída | Resultados | Depth 6, 500. |
| EV-047 | XGB inicial sem mês | 181.962,60; 463.993,37; 0,8781 | Execução reproduzida | mesmo | saída | Resultados | Melhor nas três métricas. |
| EV-048 | Diferença sem−com mês | MAE -2.478,35; RMSE -17.679,78; R² +0,0095 | Execução reproduzida | mesmo | saída | Resultados | Fundamenta remoção do mês. |
| EV-049 | Grid de tuning | depth 4/6/8; lr .03/.05; 500/800 | Código | `tune_xgboost.py` | `parameter_grid` | Metodologia | 12 combinações. |
| EV-050 | Critério do tuning | menor MAE em novembro | Código | mesmo | atualização de `best_result` | Metodologia | RMSE/R² apenas reportados. |
| EV-051 | Tuning 4/.03/500 | 208.366,50; 530.975,81; 0,8404 | Execução reproduzida | `tune_xgboost.py` | combinação 1 | Resultados | MAE/RMSE/R². |
| EV-052 | Tuning 4/.03/800 | 197.970,42; 506.035,50; 0,8550 | Execução reproduzida | mesmo | combinação 2 | Resultados | — |
| EV-053 | Tuning 4/.05/500 | 197.033,08; 511.322,21; 0,8520 | Execução reproduzida | mesmo | combinação 3 | Resultados | — |
| EV-054 | Tuning 4/.05/800 | 188.402,75; 490.752,91; 0,8636 | Execução reproduzida | mesmo | combinação 4 | Resultados | — |
| EV-055 | Tuning 6/.03/500 | 192.704,74; 487.146,40; 0,8656 | Execução reproduzida | mesmo | combinação 5 | Resultados | — |
| EV-056 | Tuning 6/.03/800 | 183.249,70; 470.117,98; 0,8749 | Execução reproduzida | mesmo | combinação 6 | Resultados | — |
| EV-057 | Tuning 6/.05/500 | 181.962,60; 463.993,37; 0,8781 | Execução reproduzida | mesmo | combinação 7 | Resultados | XGB inicial sem mês. |
| EV-058 | Tuning 6/.05/800 | 175.511,62; 458.157,15; 0,8811 | Execução reproduzida | mesmo | combinação 8 | Resultados | Candidato C. |
| EV-059 | Tuning 8/.03/500 | 183.503,87; 479.429,53; 0,8698 | Execução reproduzida | mesmo | combinação 9 | Resultados | — |
| EV-060 | Tuning 8/.03/800 | 176.450,16; 472.930,47; 0,8734 | Execução reproduzida | mesmo | combinação 10 | Resultados | — |
| EV-061 | Tuning 8/.05/500 | 174.777,78; 464.321,51; 0,8779 | Execução reproduzida | mesmo | combinação 11 | Resultados | Candidato B. |
| EV-062 | Melhor tuning | depth 8/.05/800; 170.133,00; 462.107,92; 0,8791 | Execução reproduzida | mesmo | combinação 12/final | Resultados | Candidato A. |
| EV-063 | Configuração congelada | squarederror; 8; .05; 800; child 1; .8/.8; lambda 1; hist; seed 42; jobs -1 | Código/metadata/modelo | `final_model.py`; JSON; Joblib | pipeline | Metodologia | Validada no artefato. |
| EV-064 | Janelas do backtest | Jul–Nov, expansivas | Código + execução | `backtest_xgboost_finalists.py` | `VALIDATION_MONTHS` | Metodologia | 15 treinamentos. |
| EV-065 | Tamanhos das janelas | 30.718/5.331 até 52.807/4.902 | Código + execução | mesmo | `EXPECTED_WINDOW_ROWS` | Metodologia | Cinco pares confirmados. |
| EV-066 | Candidato A | MAE 176.534,01 ± 6.196,59; RMSE 589.959,80; R² 0,7884 | Execução reproduzida | backtest | resumo | Resultados | 5 vitórias MAE. |
| EV-067 | Candidato B | MAE 181.243,01 ± 6.974,05; RMSE 589.726,03; R² 0,7894 | Execução reproduzida | backtest | resumo | Resultados | 0 vitórias. |
| EV-068 | Candidato C | MAE 182.209,50 ± 6.916,13; RMSE 586.767,62; R² 0,7910 | Execução reproduzida | backtest | resumo | Resultados | 0 vitórias. |
| EV-069 | Escolha do backtest | A pelo menor MAE e 5/5 | Código + execução | backtest | ranking/vitórias | Decisão | C foi melhor em RMSE/R² médios. |
| EV-070 | Não dominância | A não foi melhor em todas as métricas | Execução reproduzida | backtest | resumo | Discussão | Evita conclusão incorreta. |
| EV-071 | Treino final | 57.709, Jan–Nov/2025 | Código + execução + metadata | `final_model.py`; script; JSON | avaliação oficial | Avaliação | Modelo congelado. |
| EV-072 | Teste final | 5.431, Dez/2025 | mesmos | mesmos | avaliação oficial | Avaliação | Independente da seleção. |
| EV-073 | Métricas finais brutas | 231947.92292769515; 1091963.084853122; 0.5729976346033591 | Execução + metadata | avaliação; JSON | `metrics` | Resultados finais | MAE/RMSE/R². |
| EV-074 | Métricas formatadas | R$ 231.947,92; R$ 1.091.963,08; 0,5730 | Execução/documentação | script; README/app | saída/interface | Resultados finais | Oficiais. |
| EV-075 | Mediana absoluta | R$ 84.607,78 | Execução reproduzida | `analyze_final_errors.py` | mediana | Erros | NumPy e quantil coincidem. |
| EV-076 | Direção dos erros | 53,31% acima; 46,69% abaixo | Cálculo reproduzido | `run_final_evaluation()` | comparação predição/real | Erros | 0 empates. |
| EV-077 | Erro assinado médio | -R$ 30.398,29 | Cálculo reproduzido | mesmo | real − predição | Erros | Sinal negativo = sobreprevisão média. |
| EV-078 | MAE por faixas | 124.469,13; 89.352,55; 158.119,75; 342.779,83; 745.698,57; 3.585.343,55 | Execução reproduzida | script de erros | agrupamento | Erros | Faixas crescentes de valor real. |
| EV-079 | Grupo ≥ R$ 5 mi | 76; 1,40%; mediana 1.656.100; RMSE 7.957.496,16 | Cálculo reproduzido | avaliação final | filtro de faixa | Erros/Limitações | MAE 3.585.343,55. |
| EV-080 | Dez maiores erros | tabela de 10 casos confirmada | Execução reproduzida | avaliação final | ordenação por erro absoluto | Erros | Maior: R$ 50.532.816. |
| EV-081 | Área e maiores erros | mediana teste 100 m²; top 10 = 754 m² | Cálculo reproduzido | avaliação final | medianas | Discussão | Associação não causal. |
| EV-082 | Metodologia importance | neg-MAE; 10 repetições; seed 42; jobs -1 | Código | `analyze_feature_importance.py` | chamada sklearn | Interpretabilidade | Aplicada ao teste. |
| EV-083 | Importância área | 460.785,14 ± 6.331,58 | Execução reproduzida | mesmo | saída | Interpretabilidade | Maior. |
| EV-084 | Importância CEP4 | 124.343,02 ± 3.620,19 | Execução reproduzida | mesmo | saída | Interpretabilidade | Segunda. |
| EV-085 | Importância idade | 82.576,24 ± 5.289,14 | Execução reproduzida | mesmo | saída | Interpretabilidade | Terceira. |
| EV-086 | Importância padrão | 23.649,95 ± 1.499,60 | Execução reproduzida | mesmo | saída | Interpretabilidade | Quarta. |
| EV-087 | Importância fração | 15.721,82 ± 2.524,52 | Execução reproduzida | mesmo | saída | Interpretabilidade | Quinta. |
| EV-088 | Causalidade | importância preditiva não é causal | Código/documentação | README; app; dossiê | avisos | Discussão | Limite explícito. |
| EV-089 | Produção — treino | 63.140 válidos; sem holdout | Código/metadata/validação | `production.py`; JSON | contexto de produção | Implementação | Posterior à avaliação. |
| EV-090 | Joblib | 1.988.404 bytes | Artefato local | `artifacts/` | arquivo | Implementação | Ignorado pelo Git. |
| EV-091 | Metadata | projeto 0.1.0; modelo 1.0.0; ambiente correto | Artefato + validação | JSON; validador | chaves | Implementação | 2.367 bytes. |
| EV-092 | Bug histórico do Python | `0.1.0` corrigido para `3.14.6` | Git + metadata | `92ca761`; JSON | ambiente | Auditoria | Versão do projeto agora separada. |
| EV-093 | Ambiente ML | sklearn 1.9.0; XGB 3.4.0; Joblib 1.5.3; Pandas 3.0.5; Polars 1.43.2 | Metadata/ambiente | JSON; validador | `environment` | Ferramentas | Contrato validado. |
| EV-094 | Aplicação | Visão Geral, Modelo, Estimador | Código/Git | `app/app.py`; `fd1418c` | navegação | Produto | Três páginas. |
| EV-095 | Visão Geral | 63.140 válidos de 2025, filtros e gráficos | Código | `app/pages/overview.py` | `main` | Produto | Base antes das flags = 64.227. |
| EV-096 | Página Modelo | métricas, comparação, erros, importance, configuração, limitações | Código | `app/pages/model.py` | `main` | Produto | Distingue avaliação/produção. |
| EV-097 | Estimador | cinco entradas; CEP→CEP4; ACC→idade; valor declarado | Código/testes | `app/pages/estimator.py`; análise | `main` | Produto | Carrega modelo de produção. |
| EV-098 | Suíte de testes | 50 aprovados em 5,45 s | Execução reproduzida | Pytest | suíte completa | Qualidade | Python 3.14.6. |
| EV-099 | Testes por arquivo | 7/8/4/7/9/5/10 | Execução reproduzida | `tests/*.py` | coleta Pytest | Qualidade | Dataset/estimator/inference/overview/presentation/production/temporal. |
| EV-100 | Cronologia final | `a3132f6` → `ee8a5cf` → `0459244` → `92ca761` → `fd1418c` → `1c5fb40` | Git | `git log --stat` | commits de 17/09/2026 | Cronologia | Escopo, isolamento, backtest, produção, app e README. |

## Referência rápida dos tipos de evidência

- **Código/teste:** comprova regra implementada ou contrato, não sua execução
  histórica.
- **Execução reproduzida:** confirma resultado no ambiente atual, sem escrita nos
  artefatos.
- **Cálculo reproduzido:** cálculo não destrutivo feito sobre a avaliação atual
  quando o script versionado não imprime a estatística completa.
- **Artefato local:** existe nesta estação, mas é ignorado pelo Git.
- **Documentação:** registra afirmação do projeto e deve ser cruzada com código e
  dados.
- **Git:** comprova entrada da mudança no histórico, não a data da decisão humana.
- **Ausência após inventário:** indica que o repositório não contém a informação;
  não prova que a atividade nunca ocorreu fora dele.

## Contexto externo ainda necessário

Design Thinking, entrevistas, participante externo, orientações docentes,
discussões do grupo, motivação acadêmica/social e validação qualitativa não possuem
evidência no repositório e devem ser fornecidos pelos integrantes.
