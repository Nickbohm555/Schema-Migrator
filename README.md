# Java SQL to MongoDB Migration Analyzer

A comprehensive tool that scans Java codebases for SQL queries and provides AI-powered analysis to support database modernization from relational databases to MongoDB.

---

## 🎯 What This Tool Does

This tool addresses the **Discovery and Analysis** phase of database modernization by:

- Automatically scanning Java projects (local or GitHub repositories) for SQL queries
- Extracting SQL commands from various sources (JPA annotations, native queries, prepared statements)
- Analyzing SQL intent using Claude AI to understand business context and data relationships
- Providing MongoDB migration insights including suggested schema designs and indexing strategies
- Generating comprehensive reports in YAML format for migration planning

---

## 🧱 Modernization Process Coverage

| Phase              | Coverage | Description                                              |
|-------------------|----------|----------------------------------------------------------|
| 🔍 Discovery       | ✅ Full  | Identifies all SQL usage across codebase                |
| 📊 Analysis        | ✅ Full  | AI-powered intent analysis and complexity assessment     |
| 🎯 Planning        | ✅ Full  | Provides MongoDB schema suggestions and migration insights |
| 🔧 Implementation | ✅ Full  | Does not perform actual code transformation              |

---

## 👥 Who It's For

- Database Architects planning MongoDB migrations  
- Development Teams modernizing legacy Java applications  
- Technical Leaders assessing migration complexity and effort  
- DevOps Engineers preparing for database infrastructure changes  

---

## 🚀 How to Run

### Prerequisites

```bash
# Required tools
python 3.8+
git

# Install dependencies
pip install -r requirements.txt
