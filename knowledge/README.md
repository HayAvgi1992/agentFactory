# GTM Knowledge Base (vision §9)

Internal business knowledge for agent retrieval — **no internet crawling**.

## Folder structure

```text
knowledge/
├── crm_accounts/       → Salesforce / HubSpot account records
├── product_catalog/    → Product documentation
├── pricing/            → Internal pricing sheets
├── sales_playbooks/    → Qualification & sales playbooks
└── case_studies/       → Customer success stories
```

## Usage

Agents retrieve markdown documents via `app/tools/knowledge.py` (keyword search today; embeddings/RAG in a later phase).

Inspect inventory: `GET /api/knowledge`
