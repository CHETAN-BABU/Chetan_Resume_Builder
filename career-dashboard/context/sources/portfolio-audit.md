> Historical source material. Read `../evidence.yml` and `../../config/profile.yml` first. Older recommendations, missing-detail prompts and disclosure restrictions below are not current policy. Original supplied content is preserved.

# Irish Data Science CV and Job-Search Research Pack

Prepared for **Chetan Babu Mahendiran**  
Portfolio audited: `/Users/chetan/Desktop/Project`  
Research date: **12 August 2026**  
Target market: **Ireland — graduate, junior and early-career data roles**

> This is a source document for a CV-writing AI, not the final CV. Use only facts confirmed below. Replace every `[ADD ...]` placeholder before applying. Do not claim production deployment, commercial impact, teamwork, a grade, employment status, or ownership beyond what Chetan can personally verify.

## 1. Portfolio audit and positioning

The folder contains **five named code/project directories**, a **main thesis/capstone**, and three additional standalone academic analyses. It therefore contains more than six usable portfolio artefacts. For a two-page Irish graduate CV, present the **six strongest projects** below and use the others as optional variants.

Recommended positioning:

> MSc Data Science and Analytics candidate at Munster Technological University with hands-on experience in end-to-end machine-learning workflows, imbalanced classification, explainable AI, statistical modelling, Power BI, and retrieval-augmented generation. Applied Python and scikit-learn to healthcare fraud, manufacturing fault detection, financial-market and medical datasets, with additional experience building LangGraph and local-LLM applications. Seeking graduate/junior Data Scientist, Data Analyst, BI Analyst, Fraud/Risk Analytics or Applied AI roles in Ireland.

Do not describe the thesis model as “highly accurate”. Its value is the **rigour of the workflow, honest evaluation and operational threshold trade-off**, not predictive strength.

## 2. Recommended CV technical-skills section

Use only the subgroup relevant to each vacancy.

- **Programming and data:** Python, pandas, NumPy, Jupyter Notebook, Excel; SQL `[ADD only after completing a demonstrable SQL project]`
- **Machine learning:** scikit-learn, LightGBM, XGBoost, Logistic Regression, Random Forest, Gradient Boosting, SVM, k-NN, Decision Trees, K-Means, DBSCAN, SMOTE, PCA, Factor Analysis
- **Evaluation and explainability:** stratified train/validation/test splitting, GridSearchCV, threshold optimisation, confusion matrices, precision, recall, F1, ROC-AUC, PR-AUC, permutation importance, SHAP
- **Statistics and analysis:** EDA, feature engineering, standardisation, correlation analysis, outlier analysis, Bartlett's test, KMO, silhouette score, sensitivity analysis, imbalanced-data analysis
- **Visualisation and BI:** Power BI, interactive dashboards, KPI cards, filters/slicers, data storytelling, Matplotlib, Seaborn
- **Generative AI and NLP:** LangGraph, LangChain, RAG, sentence-transformers, ChromaDB, Ollama, Groq, Gemini, Hugging Face embeddings, prompt orchestration, semantic search, MMR retrieval
- **Application/cloud tooling:** Streamlit, FastAPI (declared dependency), Pydantic, Cloudflare R2/S3 API, boto3, Git/GitHub, GitHub Actions (documented), Sentry, Opik, uv, REST APIs
- **Domain exposure:** healthcare fraud, insurance analytics, semiconductor quality/fault detection, financial-market analytics, e-commerce analytics, EU regulatory compliance

Important accuracy notes:

- SQL, Docker, Azure/AWS, Spark, Databricks, MLflow, formal CI/CD testing and model deployment are **not demonstrated strongly enough in the current local artefacts**.
- The BlogBoard repository declares FastAPI, but the audited execution path is a CLI/LangGraph workflow; do not claim a production FastAPI service without showing it.
- Cloudflare R2, Sentry and Opik integrations are present in code. Claim “integrated” or “implemented”, not business-scale operation.
- The diabetes notebook scales the complete feature matrix before splitting, which leaks test-set distribution information. Treat it as an early learning project and improve it before featuring prominently.

## 3. Six projects to feature on the primary CV

### Project 1 — Main MSc capstone: Machine Learning-Based Medical Insurance Claim Fraud Detection

**Programme:** MSc Data Science and Analytics, Munster Technological University  
**Module:** DATA9003 Research Project  
**Supervisor:** Vincent Cregan  
**Status/date:** thesis template still contains an unfinished date field; write `[ADD submission month/year and final grade if awarded]`  
**Data:** public synthetic Kaggle dataset; 10,000 claims, 16 variables including target; 2,000-record independent test set

**Problem and approach**

- Built a reproducible supervised-learning workflow to identify potentially fraudulent medical insurance claims from demographic, hospital, financial, policy and risk indicators.
- Removed non-predictive/high-cardinality identifiers (`Claim ID`, `Diagnosis Code`), encoded three categorical variables and standardised eight continuous variables.
- Engineered `Claim Discrepancy` and `Delay Rate`; evaluated and rejected a weak `Composite Risk Score`, demonstrating evidence-led feature selection.
- Explored PCA: ten components preserved approximately 95% of variance, but retained original features because PCA did not improve classification and reduced interpretability.
- Used a stratified **60:20:20 train/validation/test split** and applied SMOTE only after splitting and only to training data, preventing oversampling leakage.
- Benchmarked Logistic Regression, Random Forest, Gradient Boosting, XGBoost and LightGBM under a common evaluation process.
- Tuned LightGBM with GridSearchCV; documented final parameters of learning rate `0.03`, maximum depth `4`, `200` estimators and `20` leaves.
- Optimised the probability threshold on validation data. Selected `0.25` as an operational recall/false-positive compromise rather than using the default `0.50`.
- Added permutation feature importance and SHAP global/local explanations to support transparent review of flagged claims.

**Verified results**

- Validation threshold `0.10`: recall `0.887`, F1 `0.265`, but excessive legitimate claims flagged.
- Selected threshold `0.25`: validation recall approximately `0.598`.
- Independent test results at threshold `0.25`: accuracy `47.5%`, fraud precision `16.3%`, fraud recall `60.3%`, fraud F1 `25.6%`, ROC-AUC `0.535`, PR-AUC `0.173` versus fraud-prevalence baseline of about `0.150`.
- Threshold optimisation raised recall from approximately `26%` to `60%`, explicitly accepting more false positives.
- The thesis correctly concludes that overall discrimination is limited and the model should support—not replace—expert investigation.

**Tech stack:** Python, pandas, NumPy, scikit-learn, imbalanced-learn/SMOTE, LightGBM, XGBoost, SHAP, Matplotlib, Seaborn, Jupyter.

**Best three CV bullets**

- Developed an end-to-end medical-claim fraud pipeline across 10,000 records, comparing five classifiers with feature engineering, SMOTE, GridSearchCV and leakage-controlled 60:20:20 stratified validation.
- Tuned LightGBM and optimised its decision threshold from 0.50 to 0.25, increasing fraud recall from approximately 26% to 60.3% on an independent 2,000-claim test set while quantifying the false-positive trade-off.
- Applied permutation importance and SHAP to provide global and claim-level explanations; reported precision, recall, F1, ROC-AUC and PR-AUC rather than relying on misleading accuracy for imbalanced data.

**Interview talking points:** Why recall matters in fraud triage; training-only SMOTE; threshold selection as a cost decision; why PCA was rejected; synthetic-data limitations; why an AUC of 0.535 is not production-ready; next steps including stronger data, calibrated probabilities, nested cross-validation and cost-sensitive learning.

### Project 2 — Semiconductor Manufacturing Fault Detection (SECOM)

**Data:** UCI SECOM; 1,567 samples, approximately 590 sensor measurements plus label; 1,463 pass and 104 fail (about 14:1).

**Work completed**

- Built a data-mining workflow spanning missing-data assessment, removal of highly missing and zero-variance features, scaling, EDA, correlation analysis, Z-score/IQR outlier analysis, PCA, K-Means and supervised classification.
- Retained extreme sensor observations because they could represent real fault signals.
- Used PCA to preserve 95% variance before modelling and tested whether two-cluster K-Means aligned with pass/fail labels.
- Compared k-NN, Decision Tree and SVM before and after SMOTE using minority-class precision, recall and F1.
- Found K-Means did not recover the pass/fail structure; Decision Tree with SMOTE gave the best minority-class balance with F1 `0.1795`; SVM with SMOTE produced F1 `0.0183`.

**Tech stack:** Python, pandas, NumPy, scikit-learn, imbalanced-learn, PCA, K-Means, k-NN, Decision Tree, SVM, Matplotlib, Seaborn, Jupyter.

**CV bullets**

- Analysed 1,567 semiconductor-production samples with roughly 590 sensor features, building a preprocessing, outlier, PCA, clustering and classification pipeline for a 14:1 imbalanced fault-detection problem.
- Demonstrated that K-Means failed to separate pass/fail units and improved minority detection with training-time SMOTE; Decision Tree achieved the best tested failure-class F1 of 0.1795.
- Evaluated model limitations transparently and proposed cross-validation, systematic tuning and SHAP-based sensor attribution as production-oriented next steps.

**Caveat:** the study used one 80:20 split and no systematic hyperparameter search. Do not claim robust generalisation.

### Project 3 — FAANG Multivariate Modelling with PCA and Factor Analysis

**Data:** 14,964 daily observations; five stocks (AAPL, AMZN, GOOGL, META, MSFT); 16 numeric price, volume, momentum and volatility features.

**Work completed and results**

- Excluded `Next_Day_Close` to prevent future-information leakage and removed `Date`/`Ticker` before unsupervised modelling.
- Evaluated 1,115 rows (7.45%) containing a `|Z| > 3` value and retained them as potentially meaningful market events.
- Verified suitability using correlation structure, Bartlett's test (`p < 0.001` after removing >0.95 correlated features for that test) and KMO `0.839`.
- Standardised features and selected four components consistently using the Kaiser criterion, scree elbow and 90% cumulative-variance threshold.
- Four components explained `90.6%` of variance with reconstruction MSE `0.069`: price level (`63.6%`), momentum (`14.1%`), volume/volatility (`6.6%`) and residual return (`6.3%`).
- Compared results with four-factor Factor Analysis and ran 80/90/95% sensitivity tests; PC1 loading difference between 80% and 90% solutions was `0.0000`.

**Tech stack:** Python, pandas, NumPy, scikit-learn, FactorAnalyzer/statistical tests, Matplotlib, Seaborn, PCA, Factor Analysis.

**CV bullets**

- Reduced 16 collinear technical indicators across 14,964 FAANG observations to four interpretable components explaining 90.6% of variance with reconstruction MSE 0.069.
- Validated dimensionality-reduction suitability using Bartlett's test and KMO 0.839, then triangulated component selection using Kaiser, scree and cumulative-variance criteria.
- Confirmed robustness through Factor Analysis and multi-threshold sensitivity testing while documenting non-stationarity, temporal-dependence and outlier limitations.

### Project 4 — Applied Clustering: Prototype Adjustment and DBSCAN from Scratch

**Data:** two reproducible synthetic datasets of 120 points each, generated from student-specific random seed `172`: three Gaussian clusters; and ring + blob + uniform noise.

**Work completed and results**

- Implemented an online prototype-adjustment clustering algorithm with deterministic farthest-point centroid initialisation, fixed-step updates, empty-cluster recovery and 200-epoch SSE tracking.
- Implemented DBSCAN and silhouette scoring manually, including fourth-nearest-neighbour epsilon selection and exclusion of noise points from silhouette evaluation.
- Compared learning rates `0.01`, `0.05`, `0.20`; found `0.05` best balanced speed/stability, while `0.20` oscillated and overshot.
- Prototype method on Gaussian data achieved silhouette `0.808`; DBSCAN found three clusters, two noise points and silhouette `0.814` at epsilon `1.25`.
- Prototype method on non-convex data had SSE `1292.76` and silhouette `0.514`; DBSCAN at the selected epsilon fragmented the ring, returned one cluster and 15 noise points, making silhouette undefined/reported as zero.

**Tech stack:** Python, NumPy, Matplotlib, Euclidean-distance algorithms, unsupervised learning, DBSCAN, silhouette analysis.

**CV bullets**

- Implemented prototype-adjustment clustering, DBSCAN and silhouette scoring from first principles and tested them on compact and non-convex datasets.
- Achieved silhouette 0.814 with DBSCAN on Gaussian data and used controlled learning-rate experiments to diagnose convergence, overshooting and cluster-geometry limitations.

### Project 5 — EU Compliance RAG Assistant (primary GenAI project)

**Purpose:** question-answering over GDPR, EU AI Act and DORA sources, with local/offline and Gemini-capable variants.

**Implemented capabilities**

- Streamlit chat interface with multi-PDF upload and ingestion of official EUR-Lex sources.
- PDF/web loading, recursive chunking (`1,200` characters, `180` overlap), Chroma persistent vector storage and maximum marginal relevance retrieval (`k=6`, `fetch_k=20`).
- Local Ollama chat/embeddings or Gemini provider selection, plus Hugging Face embedding fallback.
- Source metadata normalisation and page-level citations; conversation-history window; optional live web enrichment restricted in code to official EU domains.
- Additional utilities for regulation/article extraction, query-complexity detection, LLM query decomposition, heuristic confidence scoring, self-evaluation and compliance-checklist generation.
- Demo corpus includes official GDPR, DORA and EU AI Act PDFs.

**Tech stack:** Python, Streamlit, LangChain, ChromaDB, Ollama, Gemini, Hugging Face/sentence-transformers, PyPDF, Beautiful Soup, DuckDuckGo Search, RAG, MMR, prompt engineering.

**CV bullets**

- Built a privacy-conscious compliance RAG assistant over GDPR, DORA and the EU AI Act using Streamlit, LangChain, ChromaDB and configurable Ollama/Gemini models.
- Implemented PDF and official-source ingestion, overlapping chunking, persistent embeddings, MMR retrieval and page/source citations, with optional live regulatory-web enrichment.
- Added query decomposition, article extraction, confidence heuristics, self-evaluation and checklist export to improve answer transparency and usability.

**Caveats:** no retrieval benchmark, factual-accuracy evaluation, automated tests or deployed usage metrics were found. “Confidence” is heuristic, not calibrated probability; do not claim legal correctness.

### Project 6 — Power BI Business and Sports Analytics Portfolio

Treat these as one BI portfolio entry on the main CV; they may be split for analyst-focused applications.

#### E-Commerce Sales Dashboard

- Modelled/visualised an Excel workbook with **51,290 orders**, 1,173 returns and regional people mapping.
- Built Power BI KPI cards and breakdowns by category, market, ship mode, country and state, with interactive category/market/ship-mode slicers.
- Dashboard displays sales `3.79M`, profit `518.47K`, quantity `108.18K` and shipping cost `405.45K`; Standard Class sales `2.23M`; United States top-country sales `719.05K`.

#### Virat Kohli Career Score Analytics

- Analysed **516 innings/match records** from 2008–2022 and built an interactive Power BI career dashboard.
- Dashboard displays approximately `24K` runs, highest score `254`, `129` fifties, `77` hundreds and average `45.95`.
- Added opponent and year trends; leading opponent totals shown include Australia `4.5K` runs and England `3.9K` runs.

**Tech stack:** Power BI Desktop, Power Query/data preparation `[verify before claiming specific transformations]`, Excel/CSV, KPI design, slicers, categorical/time-series visualisation.

**CV bullets**

- Developed Power BI dashboards over 51,290 e-commerce transactions and 516 cricket records, surfacing KPIs and category, geography, fulfilment, opponent and time trends through interactive filters.
- Communicated business performance through sales/profit/shipping KPIs and sports performance through career aggregates, opponent comparisons and 15-year trend analysis.

## 4. Additional/optional project variants

### Diabetes Prediction with Linear SVM

- Used 768 Pima diabetes observations with eight predictors; standardised inputs and trained a linear SVM on a stratified 80:20 split.
- Notebook reports training accuracy `77.36%` and test accuracy `80.52%`, plus a single-record prediction example.
- **Critical correction before showcasing:** the notebook fits `StandardScaler` before the split. Refactor to `Pipeline(StandardScaler(), SVC(...))`, fit only on training data, handle physiologically invalid zero values, add cross-validation and report class precision/recall/F1/ROC-AUC.

### BlogBoard Multi-Agent Article Generator

- Built a typed LangGraph state machine routing tutorial/news generator agents through a validator and revision loop, with in-memory checkpointing and CLI dry-run/date/news modes.
- Integrated Groq (`llama-3.3-70b-versatile` default), Tavily and Guardian search tools, Cloudflare R2/S3-compatible storage, Pydantic settings, Opik prompt fallback and optional Sentry monitoring.
- Uses an Excel schedule of 305 entries and supports multiple ML/AI subject domains.
- **Caveat:** do not claim article quality, traffic, autonomous scheduling in production or successful GitHub Actions deployment without evidence/metrics.

## 5. Irish-market role fit

### Best-fit roles now

1. **Graduate Data Scientist / Junior Data Scientist** — strongest match through MSc, model comparison, imbalanced learning, evaluation and explainability.
2. **Graduate Data Analyst / Junior Data Analyst** — strong match through pandas, EDA, Excel, Power BI and business dashboards; SQL is the largest gap.
3. **BI/Data Visualisation Analyst** — credible through two Power BI dashboards; strengthen with DAX, Power Query and star-schema evidence.
4. **Fraud/Risk Analytics Analyst** — particularly strong narrative through insurance fraud capstone, threshold trade-offs, explainability and compliance RAG.
5. **Junior ML/Applied AI Engineer** — plausible stretch through LangGraph and RAG; needs testing, APIs, containerisation, cloud deployment and monitoring evidence.
6. **Junior Data Quality/Manufacturing Analytics Analyst** — supported by SECOM preprocessing, sensor data, missingness, PCA and fault detection.

### Current market evidence and example openings

- A current **Mastercard Data Scientist I** listing in Dublin describes a junior role spanning data aggregation/cleaning, technical analysis, ML, and dashboard/report validation—closely aligned with this portfolio. Confirm that the role is still open immediately before applying: [Mastercard Data Scientist I](https://careers.mastercard.com/us/en/job/R-275583/Data-scientist-I).
- A recent **FINEOS Graduate Data Scientist** listing asked for Python, SQL, AWS, visualisation, statistics, ML, data pipelines, data quality, CI and generative-AI familiarity. This is an excellent benchmark even if the specific advert has closed: [FINEOS graduate role summary](https://www.ziprecruiter.ie/jobs/525029817-graduate-data-scientist-at-fineos-corporation).
- A recent Dublin Data Analyst advert grouped Power BI, SQL, Python, Azure, Snowflake, ETL and Power Automate. Use this as a concrete gap list for analyst applications: [IrishJobs role snapshot](https://www.irishjobs.ie/job/data-analyst/occ-computing-job106061669).
- Current EY Ireland data roles show recurring demand for advanced SQL, data modelling/warehousing, ETL, Python, CI/CD, Agile, cloud/data platforms, MLflow/model registries and stakeholder communication. The advertised role is senior, so use it for skill direction rather than direct targeting: [EY Data Engineer skill benchmark](https://careers.ey.com/ey/job/Dublin-2-FS-Technology-Consulting-AI-and-Data-Data-Engineer-Senior-Consultant-Dublin/1220366901/).

### Skills-gap priority

| Priority | Gap | Why it matters | Portfolio proof to build |
|---|---|---|---|
| 1 | SQL | Appears across analyst/scientist/data-engineering roles | Add PostgreSQL project with joins, CTEs, window functions, aggregation and query optimisation using e-commerce data |
| 2 | Reproducible ML engineering | Notebooks/reports dominate current ML evidence | Package capstone pipeline; add config, tests, fixed seeds, requirements, model artefact and inference script |
| 3 | Cloud + deployment | Irish adverts commonly mention AWS/Azure and scalable analytics | Deploy a small inference or RAG app; document architecture, security and costs |
| 4 | DAX/data modelling | Necessary to make Power BI claims deeper | Publish measures, relationships, star schema, refresh steps and screenshots |
| 5 | Git/CI/testing | Required for team-based delivery | Add pytest, linting and GitHub Actions to one Python project |
| 6 | Experiment tracking/MLOps | Differentiates junior DS candidates | Track capstone runs in MLflow; add model registry and data/model version notes |
| 7 | Communication/business impact | Recruiters need decisions, not algorithms alone | Add a one-page executive summary and recommended action for each project |

## 6. Irish CV format and section order

Irish career guidance favours an easy-to-scan, tailored CV with evidence and action verbs. For a recent graduate, relevant education and projects can appear above unrelated employment. Jobs.ie recommends a skills-based approach for graduates with limited relevant experience and tangible examples beneath skills; TU Dublin advises reverse chronology and says date of birth, marital status and nationality are unnecessary. See [Jobs.ie graduate CV guidance](https://www.jobs.ie/job-talk/graduate-cv-template/), [TU Dublin CV Help Sheet](https://www.tudublin.ie/media/website/for-students/careers/docs/CV-Help-Sheet-%28Final%29.pdf) and [UCD's scannability checklist](https://www.ucd.ie/professionalacademy/resources/career-advice/how-to-craft-the-perfect-cv/).

Recommended two-page order:

1. Name; Irish city/county; Irish-format phone; professional email; LinkedIn; GitHub/portfolio.
2. Three-to-four-line profile tailored to the exact role.
3. Compact technical skills, mirroring truthful vacancy keywords.
4. MSc education, expected completion/classification and four-to-six relevant modules.
5. Capstone with three quantified bullets.
6. Three or four most relevant projects with two bullets each.
7. Relevant experience, then other experience with transferable achievements.
8. Certifications/awards/publications and work authorisation `[ADD exact truthful status]`.

Do not include a photograph, date of birth, marital status, full street address, generic “hard-working/team player” claims, skill bars, or references unless requested. Keep the layout single-column and ATS-readable; use standard headings and export as a text-selectable PDF.

## 7. Tailoring matrix

| Target role | Lead projects | Keywords to foreground | De-emphasise |
|---|---|---|---|
| Graduate Data Scientist | Fraud capstone, SECOM, FAANG PCA | Python, scikit-learn, model evaluation, SMOTE, feature engineering, SHAP, statistics | dashboard decoration, broad GenAI claims |
| Data Analyst | E-commerce BI, Virat BI, FAANG PCA | Power BI, Excel, pandas, KPIs, EDA, visualisation, stakeholder insight | complex agent architecture |
| Fraud/Risk Analyst | Fraud capstone, compliance RAG, SECOM | anomaly/fraud detection, precision–recall trade-off, thresholding, explainability, governance | cricket dashboard |
| Applied AI / GenAI | Compliance RAG, BlogBoard, fraud capstone | LangChain, LangGraph, RAG, vector search, Ollama/Gemini/Groq, citations, evaluation | basic diabetes notebook |
| Manufacturing/Quality Analytics | SECOM, clustering, Power BI | sensor data, missing data, PCA, fault detection, clustering, imbalanced learning | finance-specific PCA interpretation |

## 8. ATS keyword bank

Select only terms supported by the vacancy and by evidence:

`Python`, `pandas`, `NumPy`, `scikit-learn`, `machine learning`, `statistical modelling`, `exploratory data analysis`, `feature engineering`, `data preprocessing`, `classification`, `clustering`, `imbalanced data`, `SMOTE`, `PCA`, `cross-validation`, `hyperparameter tuning`, `GridSearchCV`, `threshold optimisation`, `precision`, `recall`, `F1-score`, `ROC-AUC`, `PR-AUC`, `SHAP`, `explainable AI`, `Power BI`, `Excel`, `data visualisation`, `dashboarding`, `KPI reporting`, `RAG`, `LangChain`, `LangGraph`, `ChromaDB`, `Ollama`, `Streamlit`, `Git`, `problem solving`, `technical communication`, `reproducible research`.

## 9. Job-search execution plan

- Create three CV versions: **Data Scientist**, **Data/BI Analyst**, and **Applied AI/Fraud Analytics**.
- Search titles: `Graduate Data Scientist`, `Junior Data Scientist`, `Data Science Analyst`, `Graduate Data Analyst`, `Junior Data Analyst`, `BI Analyst`, `Insights Analyst`, `Fraud Analytics Analyst`, `Risk Analytics Analyst`, `Decision Scientist`, `Junior ML Engineer`, `AI Engineer Graduate`.
- Search locations: Cork, Dublin, Limerick, Galway, Waterford and Ireland-wide hybrid/remote. Add relocation willingness only if true.
- Use LinkedIn Jobs, IrishJobs, Jobs.ie, gradireland, publicjobs.ie and direct employer career pages. Prioritise financial services/insurance, healthcare technology, consulting, manufacturing/pharma and SaaS because the project domains tell a coherent story there.
- For every application, copy the vacancy into a comparison sheet, mark each essential criterion `demonstrated / learning / absent`, then adjust the profile, skill order and first three projects.
- Apply when most core requirements match even if optional items do not. Never add a keyword without being able to explain and demonstrate it in interview.
- Track company, role URL, location, closing date, visa/sponsorship statement, CV version, contact, application date, response and follow-up.

## 10. Interview evidence bank

Prepare a 60–90 second STAR explanation for each:

- Preventing leakage by applying SMOTE only to training data.
- Choosing fraud recall and PR-AUC over headline accuracy.
- Selecting a 0.25 threshold and explaining the operational cost of false positives.
- Rejecting PCA in the capstone when it did not improve results, despite using it successfully in the FAANG study.
- Explaining why K-Means struggled on SECOM labels and why centroid methods struggle with a ring.
- Explaining MMR retrieval, chunk size/overlap and citation provenance in the RAG system.
- Turning e-commerce transaction data into a small set of decision-useful Power BI KPIs.
- Admitting model limitations and proposing the next experiment rather than overstating results.

## 11. Missing personal facts to supply to a CV-writing AI

- `[ADD mobile, professional email, Irish location, LinkedIn and GitHub URLs]`
- `[ADD MSc start/end dates, expected award date and verified grade/classification]`
- `[ADD Bachelor degree, institution, location, dates and result]`
- `[ADD all employment with dates, locations and measurable achievements]`
- `[ADD exact Irish work-authorisation/visa status and whether sponsorship is required]`
- `[ADD project GitHub URLs and clarify which code is entirely yours versus adapted/forked/team work]`
- `[ADD thesis dataset URL and repository/notebook if publishable]`
- `[ADD certifications, awards, presentations, volunteering and languages]`
- `[ADD quantified deployment/use metrics only if documented]`

## 12. Portfolio-quality issues to fix before sending applications

1. Add substantive READMEs to the diabetes, e-commerce and Virat repositories: problem, data source/licence, method, results, limitations and reproduction steps.
2. Fix scaling leakage and missing evaluation metrics in the diabetes notebook.
3. Publish code supporting the thesis, SECOM, clustering and FAANG reports; currently the reports provide evidence but recruiters cannot reproduce most results from this folder.
4. Add licences/data-attribution notes and confirm permission to redistribute datasets.
5. Add tests and a small evaluation dataset to the RAG project; distinguish heuristic confidence from validated accuracy.
6. Resolve BlogBoard README/code drift: README paths and Python/dependency versions do not fully match the current repository layout/configuration.
7. Add dashboard documentation with DAX measures, data model, transformation steps and business questions.
8. Remove generated `__pycache__` files from version control and ensure `.env`/credentials are excluded.

## 13. Prompt to give a résumé-building AI

> Create a two-page, single-column, ATS-readable Irish CV for a graduate/junior `[INSERT TARGET TITLE]` role. Use only verified facts from this research pack and the personal details I supply. Put my MSc, capstone and relevant projects before unrelated employment if I have limited relevant work experience. Write a 3–4 line profile and achievement bullets using action + method + scale + result. Do not invent metrics, grades, employment, deployment, teamwork, cloud experience or SQL proficiency. Keep the capstone technically honest: emphasise leakage control, imbalanced evaluation, explainability and the recall/false-positive trade-off; do not call the model highly accurate. Select four projects most relevant to the attached vacancy, mirror its truthful keywords naturally, use Irish/UK spelling, and identify any missing essential requirement after the CV.

---
