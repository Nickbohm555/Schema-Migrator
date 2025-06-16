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

Setup Your Environment
Create a Claude API key

Go to https://console.anthropic.com

Sign up or log in

Navigate to API Keys and create a new key

Create a MongoDB account (if you want to store results)

Go to https://www.mongodb.com/cloud

Sign up and create a free cluster (MongoDB Atlas)

Save your username, password, and connection string

Create a .env file in your project root:

env
Copy
Edit
ANTHROPIC_API_KEY=your_claude_api_key_here
MONGODB_USERNAME=your_mongodb_username
MONGODB_PASSWORD=your_mongodb_password
MONGODB_EMAIL=your_email@example.com


### 🖥️ Launch the Streamlit UI (Optional)

Now you can run the tool through a simple web interface using Streamlit:


streamlit run mongo.py



HERE IS A VIDEO DEMO BELOW:


Uploading Screen Recording 2025-06-15 at 11.52.05 PM.mov…



