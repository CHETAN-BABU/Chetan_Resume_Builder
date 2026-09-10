> Historical source material. Read `../evidence.yml` and `../../config/profile.yml` first. Older recommendations, missing-detail prompts and disclosure restrictions below are not current policy. Original supplied content is preserved.

# Chetan Babu M — Detailed Career Evidence

This is the detailed supplied narrative for resume tailoring. Read it with `config/profile.yml`, `context/evidence.yml`, and `context/PROFILE-NOTES.md`; preserve all role and claim guardrails. The structured registry controls approved external wording, claim status, client anonymity, and project IDs.

Do not copy every fact into every resume. Select only evidence mapped to the target JD, and include exactly one resume-ready project from `context/evidence.yml`.

## Positioning

- Professional identity: Data Analyst / BI Analyst / BI Developer
- Current academic identity: MSc Data Science candidate
- Suitable emerging tracks: Junior/Graduate Data Scientist and entry-level GenAI application roles when candidate projects satisfy the actual requirements
- Not suitable: experienced/senior AI Engineer, ML Engineer, Software Engineer, dedicated MLOps Engineer, or production-platform roles

The dated Infocepts experience runs from February 2023 through January 2025—approximately two years. Do not describe it as three years.

## Career timeline

### B.Tech in Computer Science — AI and ML specialization

- SRM Institute of Science and Technology, India
- Jun 2019–May 2023
- CGPA reported by Chetan: 9.4/10
- The degree specialization is academic context, not professional AI-engineering experience.

#### KPMG Data Analytics Virtual Experience — Forage

- Four-week virtual project during the bachelor's degree
- Cleaned and prepared source data
- Built a Tableau dashboard to communicate findings
- Treat this as a virtual experience/project, not employment at KPMG

### Infocepts Technologies Pvt. Ltd. — Assistant Associate Analyst

**Data Analyst / BI Developer training role | India | Feb 2023–Aug 2023**

- Completed a structured BI bootcamp covering:
  - SQL and reporting queries
  - Power BI, dashboard design, and data modeling
  - MicroStrategy administration and development
  - Python for data work
  - AWS and S3 fundamentals
  - Cloud data-warehouse concepts, including Redshift and Snowflake
  - ETL, testing, deployment, and the end-to-end BI lifecycle
- Progressed to an Associate Analyst role after the training period.

### Infocepts Technologies Pvt. Ltd. — Associate Analyst

**Data Analyst / BI Developer | India | Sep 2023–Jan 2025**

#### Hindustan Unilever — Power BI Developer

**Sector:** FMCG

- Implemented requested enhancements to existing Power BI dashboards.
- Performed testing and validation.
- Supported promotion of the updated dashboards to production.
- The source narrative uses “BAT”; another draft uses “UAT.” Use “testing and validation” until the exact term is confirmed.

#### NielsenIQ — BI Report Developer

**Sector:** FMCG  
**Engagement length:** About six months

- Worked directly with client stakeholders to gather BRDs and clarify report requirements.
- Learned the client's proprietary in-house BI platform within two weeks.
- Developed 300+ reports over six months, according to Chetan's supplied narrative.
- Created a reusable finance dashboard POC from an initial wireframe.
- Chetan reports that the template reduced dashboard-development effort by 50% and saved roughly three days per person for each new dashboard.
- Chetan reports that client stakeholders recognized the POC for innovation. Confirm the exact award wording before publishing it.

Do not convert the six-month total into “100+ reports in one month.” The source does not support that monthly number.

#### AstraZeneca — Power BI Developer

**Sector:** Pharmaceutical  
**Engagement length:** About one year

##### Executive/CEO dashboard

- Collaborated within a three-person development team.
- Contributed to data modeling, dashboard development, publication, demonstration, and handover.
- The dashboard was delivered within one month, according to the supplied narrative.
- Chetan reports personally participating in the CEO demonstration/handover.

Chetan also reports that the work contributed to a three-year, USD 5 million client contract. This causal/commercial claim requires confirmation and must not be used in external material by default.

##### Redshift-to-Snowflake migration

- Contributed to a team migration of 160 Power BI reports within a three-month delivery window.
- Updated Power Query/M logic, queries, and data connections from Redshift to Snowflake.
- Do not say Chetan led the migration unless he confirms that responsibility.
- Do not describe the work as migrating production data pipelines; the supplied evidence is about Power BI reports and their data connections.

##### Finance reconciliation dashboard

- Co-developed a Power BI dashboard that consolidated five access-tracking sources, including Excel and SharePoint.
- Added drill-through pages so users could trace access requests and discrepancies to their source.
- The previous process reportedly required six team members to spend one hour per day on manual reconciliation.
- The dashboard was tested and promoted through Power BI Service for the finance vertical.
- Chetan reports that the template was later reused in additional verticals.
- This was a group project; never claim independent ownership.

##### Other supplied Power BI work

- Implemented Power BI member access for app/workspace management.
- Automated incremental refresh using Power Automate.
- Conducted dashboard and query testing.

Use these points only when relevant and avoid implying sole ownership.

## MSc in Data Science

**Munster Technological University, Ireland | Sep 2025–Sep 2026 | In progress**

### Semester 1

- Reported overall result: 2:1
- Statistics for Data Science
- Python and R used in module projects
- DBMS using SQL and MongoDB/JSON
- Data Science Principles
- Time-series analysis in R, including traditional models and ARIMA

### Semester 2

- Applied Machine Learning
- Data Mining
- Data Analytics
- A newly supplied draft describes the SECOM and FAANG analyses below, but does not identify their course, term, dates, collaboration status, repository, or reproducible outputs.

### Thesis / capstone — MSc award in progress

**Machine Learning-Based Medical Insurance Claim Fraud Detection**

The project reports supplied on 12 August 2026 supersede the earlier narrow
thesis summary for methods and results. Submission month/year and final grade
remain unresolved.

- Built an end-to-end workflow over 10,000 public synthetic claims, including a
  2,000-record independent test set.
- Compared Logistic Regression, Random Forest, Gradient Boosting, XGBoost, and
  LightGBM using a stratified 60:20:20 split, training-only SMOTE, leakage-safe
  cross-validation, and GridSearchCV.
- Engineered Claim Discrepancy and Delay Rate, rejected a weak Composite Risk
  Score, and retained the original interpretable feature space after PCA did not
  improve classification.
- Selected a 0.25 LightGBM threshold on validation data. Independent-test fraud
  recall was 60.3%, precision 16.3%, F1 25.6%, ROC-AUC 0.535, and PR-AUC 0.173.
- Applied permutation importance and SHAP. The report explicitly concludes that
  discrimination is limited and that the model is not production-ready.

## Additional projects supplied through 12 August 2026

These descriptions are candidate-supplied draft evidence. They may be used as
personal/academic project work with careful attribution, but not as
professional AI, MLOps, manufacturing, or financial-industry experience.
Unless the audited 12 August portfolio notes establish otherwise, dates,
collaboration status, repository/demo links, data-source URLs, and reproducible
outputs remain to be confirmed.

### Retrieval-Augmented Document Q&A Prototype

- Built a Python document-ingestion and chunking workflow for PDF, TXT, and Markdown inputs, retaining source metadata for retrieved passages.
- Combined embedding-based retrieval using FAISS with TF-IDF keyword retrieval, then supplied retrieved context to an OpenAI chat model through structured prompts.
- Added a Streamlit interface with displayed source references.
- The draft also reports Docker containerization, Kubernetes manifests, GitHub Actions workflows, and evaluation of relevance, context, faithfulness, and latency. Treat these as conditional until a repository or artifact is reviewed.
- The reported 90%+ answer-relevance result is on hold until the evaluator, formula, dataset/domain, sample size, run date, and baseline are supplied.
- Do not call FAISS a standalone scalable vector database, expose chain-of-thought, claim hallucination resistance, or imply production deployment.

### SECOM Semiconductor Fault-Detection Analysis

- Prepared the SECOM dataset using median imputation, removal of high-missing and zero-variance features, standardization, and exploratory outlier analysis.
- The draft reports reducing 590 input features to 446, then retaining 162 principal components at a 95% variance threshold.
- Applied K-Means for exploratory clustering and evaluated k-NN, decision-tree, and SVM classifiers; used SMOTE to investigate class imbalance.
- The draft identifies a SMOTE-trained decision tree as the preferred precision/recall trade-off, but the validation design, leakage controls, baselines, and metrics remain to be confirmed.
- Do not claim production fault detection, reliable failure prediction, business impact, or 95% model accuracy.

### PCA of FAANG Market Indicators

- Prepared a draft dataset described as 14,964 stock-level observations and 16 technical indicators using missing-value checks, standardization, correlation analysis, and factorability diagnostics.
- Applied PCA to reduce the indicators to four components explaining a reported 90.6% of sample variance.
- Produced loading, score, scree, biplot, and reconstruction-error views; compared PCA with factor analysis and varied retained-variance thresholds.
- Component themes such as price, momentum, volatility, and returns are interpretations of loadings, not causal or predictive findings.
- Do not present the analysis as price prediction, investment advice, trading performance, or 90.6% accuracy.

### Prototype Adjustment and DBSCAN Clustering

- Implemented prototype-adjustment clustering, DBSCAN, and silhouette scoring
  from first principles on two reproducible 120-point synthetic datasets.
- Compared learning rates 0.01, 0.05, and 0.20 across 200 epochs; 0.05 provided
  the best observed speed/stability balance.
- DBSCAN achieved silhouette 0.814 on Gaussian data with three clusters and two
  noise points at epsilon 1.25; the selected epsilon did not recover the
  non-convex ring, and that limitation must remain visible.

### EU Compliance RAG Assistant

- Built a Streamlit assistant over GDPR, the EU AI Act, and DORA using official
  sources, persistent Chroma storage, MMR retrieval, and configurable local
  Ollama or Gemini models.
- Added page/source citations, query decomposition, article extraction,
  heuristic confidence, self-evaluation, and compliance-checklist export.
- Do not claim legal correctness, calibrated confidence, benchmarked factual
  accuracy, production deployment, or usage metrics.

### Power BI Business and Sports Analytics Portfolio

- Built an e-commerce dashboard over 51,290 orders and 1,173 returns with KPI,
  category, market, fulfilment, and geographic views.
- Built a second dashboard over 516 Virat Kohli innings/match records from
  2008-2022 with opponent and year trends.
- Do not infer undocumented DAX, Power Query transformations, star-schema work,
  deployment, stakeholder adoption, or business impact.

### BlogBoard Multi-Agent Article Generator

- Built a typed LangGraph state workflow routing tutorial/news generators
  through validation and revision with in-memory checkpointing.
- Integrated Groq, Tavily, Guardian search, Cloudflare R2/S3-compatible storage,
  Pydantic, Opik fallback, and optional Sentry monitoring.
- Do not claim production autonomy, successful GitHub Actions deployment,
  article quality, traffic, or reliability metrics.

## Skills evidence

### Professional

- Power BI, Tableau, MicroStrategy
- SQL; draft materials list MySQL, SQL Server, and PostgreSQL
- Power Query/M, data modeling, reporting, and dashboard development
- Requirements/BRD gathering, stakeholder communication, testing, deployment, and handover
- Redshift, Snowflake, AWS/S3 fundamentals
- Power Automate, Nexla, Dataiku

### Academic

- Python, R, statistics, data mining
- SQL, MongoDB, JSON
- Time series and ARIMA
- Classification, Random Forest, XGBoost

### Candidate-project evidence

- pandas, NumPy, scikit-learn, matplotlib, seaborn
- PCA, feature preprocessing, K-Means, k-NN, decision trees, SVM, SMOTE
- Python document ingestion, FAISS retrieval, TF-IDF, structured prompting, OpenAI API, Streamlit
- Docker, Kubernetes manifests, and GitHub Actions are newly reported project details and remain conditional until an artifact is reviewed
- LightGBM, GridSearchCV, SHAP, threshold optimisation, DBSCAN, Factor Analysis,
  LangChain, LangGraph, ChromaDB, Ollama/Gemini, MMR retrieval, and Power BI
  portfolio work may be used only through their registered project evidence.

## Certifications reported by Chetan

- Microsoft Certified: PL-300 Power BI Data Analyst Associate; renewal through March 2027 newly reported
- Nexla Certified Foundations
- Dataiku Core Designer
- HackerRank SQL (Hard)
- Infocepts Data Analytics Internship Certificate

Certification IDs and public verification links were not supplied.

## Languages supplied

- English (fluent)
- Tamil (fluent)
- Telugu (native)

A newly supplied draft instead lists English (professional), Tamil (native),
and Hindi (conversational). Preserve the established language line until Chetan
confirms which list and proficiency labels are current.

## Quantified claims

| Claim | Status |
|------|--------|
| 300+ NielsenIQ reports over six months | Supported by supplied narrative |
| Learned proprietary BI tool within two weeks | Supported by supplied narrative |
| Finance template reduced effort by 50% | User-reported; retain attribution |
| 160 Power BI reports migrated within three months | Supported as team contribution |
| Five reconciliation sources / six-person daily process | User-reported |
| USD 5 million contract caused by dashboard | Hold for confirmation |
| 100+ reports in one month | Unsupported; do not use |
| Zero migration discrepancies | Unsupported; do not use |
| RAG 90%+ answer relevance | Hold until evaluation evidence is supplied |
| Capstone 10,000 claims / selected-threshold metrics | Audited project-report evidence; use with low-discrimination caveat |
| SECOM 1,567 samples / 162 components / F1 0.1795 | Audited academic-project evidence; one-split limitation required |
| FAANG 14,964 observations / four components / 90.6% variance / MSE 0.069 | Audited academic-project evidence; not accuracy or prediction |
| DBSCAN silhouette 0.814 on Gaussian synthetic data | Audited academic-project evidence; do not generalise beyond the dataset |

## Missing facts

- Preferred current phone: the earlier Irish number or newly supplied `+91 73585 72027` WhatsApp-only number
- Current location: Ireland or newly supplied Chennai, India
- Exact MSc degree title and whether the expected `1:1` statement should be omitted
- Exact Feb–Aug 2023 employment/internship classification
- Associate Analyst end date: January 2025 or newly supplied July 2025
- Permission to name enterprise clients publicly
- Exact award title
- Thesis methods completed and final metrics
- Project dates, course/personal classification, collaboration status, repositories, datasets, validation details, and reproducible outputs
