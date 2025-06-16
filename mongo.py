import os
import git
import tempfile
from pathlib import Path
import anthropic
import shutil
import yaml
import re
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()
import json
from datetime import datetime
import re
from collections import defaultdict
import os
from pathlib import Path
import pprint
import subprocess
import streamlit as st
import tempfile
import shutil



# FUNCTION: Parse the Table: Given a format of table: primary key, foreign key
# Parse this into a dictionary to access easily
# no LLM use, only parsing 


def parse_claude_output_to_dict(claude_text: str):
    result = {}
    current_table = None

    for line in claude_text.strip().splitlines():
        line = line.strip()

        if line.startswith("TABLE "):
            current_table = line.replace("TABLE ", "").replace(":", "").strip().upper()
            result[current_table] = {
                "primary_key": [],
                "foreign_keys": []
            }
        elif line.startswith("- Primary Key"):
            pk_match = re.search(r"- Primary Key\(s\): (.+)", line)
            if pk_match and current_table:
                pks = [key.strip() for key in pk_match.group(1).split(",")]
                result[current_table]["primary_key"] = pks
        elif line.startswith("- Foreign Key"):
            # foreign key list starts next lines
            continue
        elif "→" in line and current_table:
            result[current_table]["foreign_keys"].append(line.strip("- ").strip())

    return result


# FUNCTION: Ask LLM to create the code for the mongoDB Schema 
# Had to prompt engineer correctly (no comments, add multiple documents if needed)
# LLM Use Case: Code generation !!


def get_mongo_schema_code_with_claude(schema_block: str, table_name: str) -> str:
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    """
    Uses Claude to generate a complete Python script that inserts multiple MongoDB documents
    using a real Atlas connection.
    """
    mongo_code_creation_prompt = f"""
            You are a senior Python developer and MongoDB expert.

            Output **only** valid Python code — no explanations, comments, markdown fences, or extra text.

            Requirements:
            - Import necessary modules: `pymongo`, `urllib.parse.quote_plus`
            - Escape the username and password using `quote_plus`
            - Connect to MongoDB Atlas using this connection string format:

                mongodb+srv://{{username}}:{{password}}@cluster0.ze0xint.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

            - Use a database name appropriate for the context (derive from schema or justification if possible)
            - Use the collection name: `{table_name}`
            - From the provided schema block, generate multiple realistic example documents as Python dictionaries
            - Use the justification to determine how many example documents to create and what fields to emphasize
            - Name the documents `item_1`, `item_2`, etc.
            - Insert all documents in a single call to `collection.insert_many()`
            - Place all connection and insertion code inside an `if __name__ == "__main__":` block

            Use these credentials exactly:

            - Username: `{username}`
            - Password: `{password}`

            Here is the schema block and justification(in JSON):

            ```json
            {schema_block}
            """
    return call_claude_api(
        prompt=mongo_code_creation_prompt,
        system_prompt="You generate production-ready Python scripts that insert MongoDB documents using Atlas connection."
    )



# Writes my schema created from a previous LLM to a file

def save_generated_schema_files(code: str, filename: str = "insert_generated_doc.py"):
    with open(filename, "w") as f:
        f.write(code)
    print(f"✅ Schema code saved to {filename}")




# This parses the LLM final output of queries and gets a dictionary of {TABLE: Queries}

def parse_claude_response(text):
    tables = defaultdict(list)
    current_table = None
    buffer = []

    lines = text.strip().splitlines()

    for line in lines:
        line = line.strip()

       
        m = re.match(r'^TABLE\s+([A-Z_]+):$', line)
        if m:
            
            if current_table and buffer:
                query = " ".join(buffer).strip()
                if query:
                    tables[current_table].append(query)
                buffer = []

            current_table = m.group(1)
            continue

        
        if line.startswith("- "):
            
            if buffer:
                query = " ".join(buffer).strip()
                if query:
                    tables[current_table].append(query)
                buffer = []

            
            buffer.append(line[2:].strip())
        else:
            
            if buffer:
                buffer.append(line)
            

   
    if current_table and buffer:
        query = " ".join(buffer).strip()
        if query:
            tables[current_table].append(query)

    
    return dict(tables)



# Extract table names from parsed Claude response
def extract_table_names_from_parsed_dict(parsed_dict):
    return list(parsed_dict.keys())





# Ask the developer to choose a table name based on the 
def get_table_question_from_user(available_tables):
    print("\n--- MongoDB Schema Assistant ---")
    print("Choose which table you'd like help modeling in MongoDB.\n")
    print("Available tables:")

    for i, table in enumerate(available_tables):
        print(f"{i + 1}. {table}")
    
    global schemas_dictionary
    schemas_dictionary = {}

    while True:
        try:
            choice = int(input("\nEnter the number of the table you'd like to model: "))
            if 1 <= choice <= len(available_tables):
                table_name = available_tables[choice - 1]
                break
            else:
                print("❌ Please enter a valid number.")
        except ValueError:
            print("❌ Please enter a number.")

    
    return table_name





# readnin the mongoDB summarized rules I listed - not REALLY needed ...
def load_mongodb_guidelines():
    with open("mongodb_modeling_guidelines.txt", "r") as f:
        return f.read()



# given a string, return all cases where we use CREATE TABLE ...
def extract_create_table_blocks(sql_text):

    create_blocks = re.findall(
        r'CREATE\s+TABLE\s+.*?\(.*?\);', sql_text,
        re.IGNORECASE | re.DOTALL
    )
    return [block.strip() for block in create_blocks]



# Return a list of strings likely to be queries ...
def extract_sql_queries_from_java(java_code):

    def remove_comments(code):
        
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        code = re.sub(r'//.*', '', code)
        return code

    code_no_comments = remove_comments(java_code)

    
    string_literals = re.findall(r'"((?:[^"\\]|\\.)*?)"', code_no_comments, re.DOTALL)

    
    sql_keywords = ['select', 'insert', 'update', 'delete', 'create', 'alter', 'drop', 'join', 'where', 'from', 'into']
    
    potential_sql = []
    for string in string_literals:
        lowered = string.lower()
        if any(keyword in lowered for keyword in sql_keywords):
            potential_sql.append(string.strip())
    
    return potential_sql



# Initialize Claude client
def initialize_claude_client():
    """Initialize Claude API client"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    return anthropic.Anthropic(api_key=api_key)

claude_client = None



# get the client ...
def get_claude_client():
    """Get or initialize Claude client"""
    global claude_client
    if claude_client is None:
        claude_client = initialize_claude_client()
    return claude_client


# make an API call to claude ...
def call_claude_api(prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
    """
    Make a call to Claude API
    
    Args:
        prompt (str): The user prompt
        system_prompt (str, optional): System prompt for context
        max_tokens (int): Maximum tokens in response
    
    Returns:
        str: Claude's response
    """
    try:
        client = get_claude_client()
        
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = client.messages.create(**kwargs)
        return response.content[0].text
        
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None





# Temporarily clone the repository ...
def clone_and_analyze_repo(repo_url, local_path=None):


    if local_path is None:
        temp_dir = tempfile.mkdtemp()
        local_path = os.path.join(temp_dir, "repo")
        cleanup_temp = True
    else:
        cleanup_temp = False
    
    try:
        print(f"Cloning repository from {repo_url}...")
        
       
        repo = git.Repo.clone_from(repo_url, local_path)
        
        print(f"Repository cloned to: {local_path}")
        
    
        repo_info = analyze_repository(local_path)
        
        return repo_info, local_path
        
    except git.exc.GitCommandError as e:
        print(f"Error cloning repository: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None






# return a dictionary about information of this repository ...
def analyze_repository(repo_path):

    repo_path = Path(repo_path)
    java_files = list(repo_path.rglob("*.java"))
    sql_files = list(repo_path.rglob("*.sql"))
    sql_extensions = ["*.sql", "*.ddl", "*.dml", "*.psql", "*.mysql"]
    all_sql_files = []
    for ext in sql_extensions:
        all_sql_files.extend(repo_path.rglob(ext))
    
    
    all_sql_files = list(set(all_sql_files))
    
    repo_info = {
        "repo_path": str(repo_path),
        "java_files": [str(f) for f in java_files],
        "sql_files": [str(f) for f in all_sql_files],
        "java_count": len(java_files),
        "sql_count": len(all_sql_files),
        "total_files": len(java_files) + len(all_sql_files)
    }
    
    return repo_info


# return the file content per file ...
def read_file_contents(file_paths):
    
    file_contents = {}
    
    for i, file_path in enumerate(file_paths):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_contents[file_path] = f.read()
            print(f"Read file {i+1}: {file_path}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            file_contents[file_path] = None
    
    
    return file_contents



if __name__ == "__main__":
    
    

    # You’ll need to define these somewhere in your codebase
    # from your_module import clone_and_analyze_repo, read_file_contents, extract_sql_queries_from_java

    st.set_page_config(page_title="Repository Analyzer", layout="wide")
    st.title("🔍 AI Schema Migrator")

    # Style boost (optional)
    st.markdown("""
    <style>
    .big-label { font-size: 1.3rem; font-weight: 600; margin-top: 1rem; }
    .step-box {
        border: 1px solid #ddd; 
        padding: 1rem; 
        border-radius: 1rem; 
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Step 0: Input ---
    with st.container():
        st.markdown("<div class='big-label'>Step 1: Enter GitHub Repo</div>", unsafe_allow_html=True)
        repo_url = st.text_input("Paste a GitHub repo URL containing Java + SQL code", 
                                value="https://github.com/doubleirish/lecture1_jdbc.git")
        if st.button("🚀 Start Analysis"):
            st.session_state.start_clicked = True

    # --- Step 1: Clone and Analyze Repo ---
    if st.session_state.get("start_clicked") and "repo_info" not in st.session_state:
        with st.status("🔄 Cloning and analyzing repository...", expanded=True) as status:
            repo_info, local_path = clone_and_analyze_repo(repo_url)
            if not repo_info:
                st.error("❌ Failed to analyze repository.")
                st.stop()
            st.session_state.repo_info = repo_info
            st.session_state.local_path = local_path
            status.update(label="✅ Repository cloned and analyzed", state="complete")

    # Show Step 1 summary with expandable details (like Step 2)
    if "repo_info" in st.session_state:
        st.markdown("✅ Repository cloned and analyzed")

        with st.expander("📂 View repository info details", expanded=False):
            st.json(st.session_state.repo_info)

        if st.button("➡️ Next: Read Files"):
            st.session_state.step2_ready = True



    # --- Step 2: Read Java and SQL Files ---
    if st.session_state.get("step2_ready") and ("java_contents" not in st.session_state or "sql_contents" not in st.session_state):
        with st.status("📄 Step 2: Reading Java and SQL files...", expanded=True) as status:
            java_contents = read_file_contents(st.session_state.repo_info["java_files"]) if st.session_state.repo_info["java_files"] else {}
            sql_contents = read_file_contents(st.session_state.repo_info["sql_files"]) if st.session_state.repo_info["sql_files"] else {}
            st.session_state.java_contents = java_contents
            st.session_state.sql_contents = sql_contents
            status.update(label="✅ Step 2 complete: Files read", state="complete")

    # --- Step 2 Output ---
    if "java_contents" in st.session_state and "sql_contents" in st.session_state:
        st.markdown("<h3 style='color:black;'>📥 Step 2 Output: Java and SQL File Contents</h3>", unsafe_allow_html=True)

        with st.expander("📂 Java Files"):
            for path, content in st.session_state.java_contents.items():
                st.code(content, language="java")

        with st.expander("🗄️ SQL Files"):
            for path, content in st.session_state.sql_contents.items():
                st.code(content, language="sql")

        if st.button("➡️ Step 3: Extract SQL from Java"):
            st.session_state.step3_ready = True

    # --- Step 3: Extract SQL Snippets ---
    if st.session_state.get("step3_ready") and "sql_snippets_combined" not in st.session_state:
        with st.status("🧠 Step 3: Extracting SQL queries from Java files...", expanded=True) as status:
            all_sql_snippets = []
            for content in st.session_state.java_contents.values():
                if content:
                    snippets = extract_sql_queries_from_java(content)
                    if snippets:
                        all_sql_snippets.extend(snippets)

            if not all_sql_snippets:
                st.warning("⚠️ No SQL queries found.")
                st.stop()

            sql_snippets_combined = "\n\n".join(all_sql_snippets)
            st.session_state.sql_snippets_combined = sql_snippets_combined
            status.update(label="✅ Step 3 complete: SQL queries extracted", state="complete")

    # --- Step 3 Output ---
    if "sql_snippets_combined" in st.session_state:
        with st.expander("🧠 Step 3 Output: Extracted SQL Queries from Java"):
            st.markdown("<h4 style='color:black;'>SQL Queries Found:</h4>", unsafe_allow_html=True)
            st.code(st.session_state.sql_snippets_combined, language="sql")

        if st.button("➡️ Step 4: Group Queries by Table"):
            st.session_state.step4_ready = True






        # --- Step 4: Group SQL Queries via LLM ---
        if st.session_state.get("step4_ready") and "QUERIES_LLM_OUTPUT_FIRST" not in st.session_state:
            
            with st.spinner("🤖 AI Schema Migrator is Grouping SQL queries by Table"):
                example_tables = """
    TABLE ORDERS:
    - SELECT * FROM ORDERS;

    TABLE CUSTOMERS:
    - SELECT ID, NAME FROM CUSTOMERS;

    JOINED QUERIES (appearing under all referenced tables):
    - SELECT C.NAME, O.TOTAL FROM CUSTOMERS C JOIN ORDERS O ON C.ID = O.CUSTOMER_ID;
    """
                prompt_queries_first = f"""
    I have several SQL snippets extracted from Java code across different files. 

    Please do the following:

    1. Extract the table name(s) from each SQL query by looking at the `FROM` and `JOIN` clauses.

    2. Group all queries that reference **only one table** under that table’s section, like this:

        TABLE TABLE_NAME:
        - SQL query 1
        - SQL query 2

    3. For queries that reference **multiple tables** (via JOINs), do NOT put them under individual tables yet. Instead, put all such multi-table queries under a single separate section at the bottom named:

        JOINED QUERIES (appearing under all referenced tables):
        - multi-table query 1
        - multi-table query 2

    4. Use uppercase table names for section headers (e.g., TABLE USERS).

    5. Avoid duplicates: do not list the same query twice under the same table.

    6. Ignore any lines that are not valid SQL (like logs, comments, or unrelated text).

    7. Preserve the exact filenames and inline formatting of the queries.

    IMPORTANT:
    - Do NOT add any backticks (`) or triple backticks (```) around SQL queries.
    - Output queries as plain text only, without any Markdown code formatting.
    - Do not modify, reword, or reformat the SQL queries in any way. Use the exact text as provided.

    ALWAYS follow this output format exactly: 
    {example_tables}

    Here are the SQL snippets:

    {st.session_state.sql_snippets_combined}
                """

                system_prompt = "You are a helpful expert in database design and schema interpretation."
                grouped_queries = call_claude_api(prompt=prompt_queries_first, system_prompt=system_prompt)
                st.session_state.QUERIES_LLM_OUTPUT_FIRST = grouped_queries
                st.success("✅ Step 4 complete: SQL queries grouped.")

        # Show grouped query output
        if "QUERIES_LLM_OUTPUT_FIRST" in st.session_state:
            with st.expander("📂 Step 4 Output: Grouped SQL Queries"):
                st.text_area("Grouped SQL Queries:", value=st.session_state.QUERIES_LLM_OUTPUT_FIRST, height=350)

            if st.button("➡️ Step 5: Organize by Final Tables"):
                st.session_state.step5_ready = True






        # Step 5: Final LLM call to merge JOINED QUERIES under each table
        if (
    st.session_state.get("step5_ready") 
    and "QUERIES_LLM_OUTPUT_FIRST" in st.session_state 
    and "QUERIES_LLM_OUTPUT_FINAL" not in st.session_state
):
            
            with st.spinner("AI Schema Migrator is formatting queries by Table Name"):
                
                user_prompt = f"""
    I have the following SQL queries grouped by tables, plus a separate section listing all multi-table JOIN queries at the bottom, exactly like this:

    {st.session_state.QUERIES_LLM_OUTPUT_FIRST}

    Please do the following:

    1. For each query in the "JOINED QUERIES (appearing under all referenced tables)" section, add that query under **every** table it references in the output.

    2. Remove the entire "JOINED QUERIES" section from the final output.

    3. Keep the exact formatting and filenames as they appear.

    4. Use uppercase table names for all section headers (e.g., TABLE USERS).

    5. Do not list the same query more than once under the same table (avoid duplicates).

    IMPORTANT:
    - Do NOT add any backticks (`) or triple backticks (```) around SQL queries.
    - Output queries as plain text only, without any Markdown code formatting.

    Return the fully merged and cleaned output, with all queries correctly grouped under their respective table sections and no separate "JOINED QUERIES" section.
                """
                system_prompt = "You are a helpful expert in database design and schema interpretation."
                st.session_state.QUERIES_LLM_OUTPUT_FINAL = call_claude_api(prompt=user_prompt, system_prompt=system_prompt)
                st.success("✅ Step 5 complete: Queries finalized and merged.")



        # Step 6: Display final output (after Step 4 & 5 done)
        if "QUERIES_LLM_OUTPUT_FINAL" in st.session_state:
            with st.expander("📂 View Final SQL Grouping by Table", expanded=True):
                st.code(st.session_state.QUERIES_LLM_OUTPUT_FINAL, language="sql")



        # --- Step 6: Extract CREATE TABLE info (only after Step 5 & 6 done) ---
        if "QUERIES_LLM_OUTPUT_FINAL" in st.session_state:
            if ("SQL_TABLES" not in st.session_state or "parsed_dict" not in st.session_state) and "sql_contents" in st.session_state:
                if st.button("▶️ Step 6: Extract Table Definitions (CREATE TABLE)"):
                    with st.spinner("Extracting CREATE TABLE definitions and parsing keys..."):
                        all_ddl_blocks = []
                        for file_path, content in st.session_state.sql_contents.items():
                            if content:
                                ddl_blocks = extract_create_table_blocks(content)
                                all_ddl_blocks.extend(ddl_blocks)

                        if not all_ddl_blocks:
                            st.warning("⚠️ No CREATE TABLE blocks found.")
                            st.stop()

                        combined_create_tables = "\n\n".join(all_ddl_blocks)
                        st.session_state.combined_create_tables = combined_create_tables

                        prompt_table_format = f"""
        I extracted these SQL DDL snippets from a legacy database. Please identify each table’s primary key(s) and foreign key relationships.

        Format your response like this exactly:

        TABLE table_name:
        - Primary Key(s): col1, col2
        - Foreign Key(s):
        - local_col → referenced_table.referenced_col
        - another_col → another_table.another_col

        Here are the DDL blocks:

        {st.session_state.combined_create_tables}
                        """
                        st.session_state.SQL_TABLES = call_claude_api(
                            prompt=prompt_table_format,
                            system_prompt="You are an expert database architect."
                        )
                        st.session_state.parsed_dict = parse_claude_output_to_dict(st.session_state.SQL_TABLES)

                        st.success("✅ Step 6 complete: Table definitions extracted and parsed.")



            if "SQL_TABLES" in st.session_state:
                with st.expander("📐 Step 6 Output: Table Definitions from DDL", expanded=True):
                    st.code(st.session_state.SQL_TABLES)



        # --- Step 7: Parse grouped SQL output (requires Step 5 and Step 6) ---
        if "QUERIES_LLM_OUTPUT_FINAL" in st.session_state and "SQL_TABLES" in st.session_state:
            if st.button("▶️ Step 7: Parse Grouped SQL Output to Dictionary"):
                st.session_state.step7_ready = True

        # Execute Step 7 only after button is pressed
        if st.session_state.get("step7_ready") and "table_query_dictionary" not in st.session_state:
            with st.spinner("🔍 Parsing grouped SQL output..."):
                st.session_state.table_query_dictionary = parse_claude_response(st.session_state.QUERIES_LLM_OUTPUT_FINAL)
                st.success("✅ Step 7 complete: Grouped SQL parsed.")

        # --- Step 7A Output: Parsed Queries by Table ---
        if st.session_state.get("step7_ready") and "table_query_dictionary" in st.session_state:
            with st.expander("📚 Step 7 Output: SQL Application Code", expanded=True):
                st.code(st.session_state.table_query_dictionary)

        # --- Step 7B Output: Parsed Table Keys ---
        if st.session_state.get("step7_ready") and "parsed_dict" in st.session_state:
            with st.expander("📚 Step 7 Output: Table Formatting (Primary and Foreign Keys)", expanded=True):
                st.code(st.session_state.parsed_dict)



        # if st.session_state.get("step7_ready", False):
        #     if st.sidebar.button("⬅️ Back to Table Selection"):
        #         # Reset table-related session state to go back
        #         st.session_state.table_selected = False
        #         for key in ["selected_table", "queries", "fks", "columns"]:
        #             if key in st.session_state:
        #                 del st.session_state[key]
                
        # Load MongoDB migration guidelines once
        if "mongodb_guidelines" not in st.session_state:
            st.session_state.mongodb_guidelines = load_mongodb_guidelines()

        if st.session_state.get("step7_ready", False) and "table_query_dictionary" in st.session_state:

            # Load tables once
            if "available_tables" not in st.session_state:
                st.session_state.available_tables = extract_table_names_from_parsed_dict(st.session_state.parsed_dict)

            available_tables = st.session_state.available_tables

            st.markdown("### Step 8: Please select a table to analyze before proceeding")

            # Radio for selection
            selected_table = st.radio("Select a table:", options=available_tables)

            # Check if selection changed (or no previous)
            if st.session_state.get("selected_table", None) != selected_table:
                # Save new selection
                st.session_state.selected_table = selected_table

                # Clear cached extraction data to force fresh run
                for key in ["queries", "fks", "columns", "model_justification", "final_schema_and_justification", "schema_evaluation"]:
                    if key in st.session_state:
                        del st.session_state[key]

            # Now run extraction logic fresh every time based on current selection:

            # Extract queries and foreign keys fresh (no caching in session)
            queries = st.session_state.table_query_dictionary[selected_table]
            fks = st.session_state.parsed_dict[selected_table]["foreign_keys"]

            # --- Queries Section ---
            st.markdown(f"## 🧾 SQL Queries for `{selected_table}`")

                        # Combine queries without extra whitespace
            all_queries_text = "---\n".join(f"-- Query {i+1} --\n{q.strip()}" for i, q in enumerate(queries))

            with st.expander(f"🧾 SQL Queries for `{selected_table}`", expanded=False):
                st.code(all_queries_text, language="sql")

            # --- Foreign Keys Section ---
            st.markdown(f"## 🔗 Foreign Keys for `{selected_table}`")
            with st.expander("Foreign Keys", expanded=True):  # <-- Also shrinkable!
                if fks:
                    for fk in fks:
                        st.markdown(f"- 🔑 **{fk}**")
                else:
                    st.info("No foreign keys found for this table.")

            # Extract columns fresh each time
            final_prompt = f"""
            You are given a list of SQL queries related to a single table.

            Your job is to find the column names for the table based only on the `INSERT INTO` query (if available). Ignore SELECT, DELETE, or JOIN queries unless the INSERT query is missing.

            Here is the list of SQL queries:

            {queries}

            ---

            Return only the columns and nothing else:
            """
            columns = call_claude_api(
                prompt=final_prompt,
                system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
            )

            st.markdown(f"### 🧱 Columns for `{selected_table}`")
            st.code(columns)




            # --- Step 2: Modeling Strategy (but do not show it) ---
            if "model_justification" not in st.session_state:
                with st.spinner("🧠 Generating MongoDB modeling strategy..."):
                    model_justification_prompt = f"""
                    You are helping design a MongoDB schema for a table from a legacy relational database.

                    Below is the relevant context:

                    📌 **Columns**
                    {columns}

                    🔗 **Foreign Keys**
                    {fks}

                    📝 **Representative SQL Queries**
                    {queries}

                    📚 **Guidelines**
                    {st.session_state.mongodb_guidelines}

                    ---

                    🎯 **Task**
                    Based on the table's structure, foreign key relationships, and query patterns, choose the most appropriate MongoDB modeling strategy for this table.

                    Your options:
                    - **Embedded Document** — for tightly coupled data often queried together.
                    - **Referenced Document** — for loosely coupled or shared data.
                    - **Top-Level Collection** — for independent entities.

                    ---

                    🛑 **Rules**
                    - Do **NOT** generate schema or code.
                    - Keep your response concise and structured.
                    - Limit to **1 modeling decision** and **max 5 bullet points** of justification.

                    📦 **Format**
                    Respond **only** in this format:

                    **Model as**: [embedded / referenced / top-level collection]

                    **Justification**:
                    - [concise bullet point 1]
                    - [concise bullet point 2]
                    - [concise bullet point 3]
                    """
                    st.session_state.model_justification = call_claude_api(
                        prompt=model_justification_prompt,
                        system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
                    )

            st.success("✅ Modeling decision complete.")
            
            

            if "final_schema_and_justification" not in st.session_state:
                with st.spinner("⏳ Generating final MongoDB schema and justification..."):
                    final_schema_and_justification_prompt = f"""
                    You are building a MongoDB document schema based on the following:

                    - Columns: {columns}
                    - Foreign keys: {fks}
                    - Modeling Justification: {st.session_state.model_justification}

                    ---

                    🎯 **Output Format**

                    1. The MongoDB schema (in JSON format only — no inline comments or explanations).
                    2. A justification section with **up to 5 concise bullet points** explaining why this structure was chosen.

                    🛑 **Important**
                    - Keep justifications practical and short (1 line each).
                    - Focus on reasons like query patterns, data ownership, update patterns, reusability, or write optimization.
                    """
                    st.session_state.final_schema_and_justification = call_claude_api(
                        prompt=final_schema_and_justification_prompt,
                        system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
                    )

            st.success("✅ Final schema and justification complete.")

            with st.expander("📦 Final Schema and Justification", expanded=False):
                st.text(st.session_state.final_schema_and_justification)

            
                        # --- Initialize schema storage if not present ---
            if "schemas_dictionary" not in st.session_state:
                st.session_state.schemas_dictionary = {}

            # --- Save the schema from earlier step ---
            st.session_state.schemas_dictionary[st.session_state.selected_table] = st.session_state.final_schema_and_justification

            # --- Build prompt for evaluation ---
            prompt_repeat = f"""
            You are evaluating whether a MongoDB document schema is correctly designed to match the actual SQL query patterns.

            Here is the SQL query workload:

            {queries}

            Here is the current MongoDB document schema:

            {st.session_state.schemas_dictionary[st.session_state.selected_table]}

            Your task is to analyze whether this schema aligns well with the access patterns shown in the queries.

            Respond in this strict format only:

            NEEDS REVISION: [YES or NO]

            IF YES, give a one-line explanation why and suggest what direction to take (e.g., "consider embedding X", "add indexing", "split this field", etc).

            IF NO, confirm that the schema aligns well with query access patterns.

            Only respond in the format below. Do not include explanations outside of this format.

            ---

            NEEDS REVISION: <YES or NO>  
            JUSTIFICATION: <one-line reason>  
            NUDGE: <short suggested direction or 'None'>
            """

            # --- Call LLM for evaluation ---
            if "schema_evaluation" not in st.session_state:
                with st.spinner("⏳ Evaluating schema alignment with queries..."):
                    st.session_state.schema_evaluation = call_claude_api(
                        prompt=prompt_repeat,
                        system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
                    )

            


            # --- Parse schema evaluation output ---
            match = re.search(
                r"NEEDS REVISION:\s*(YES|NO).*?NUDGE:\s*(.*)",
                st.session_state.schema_evaluation,
                re.DOTALL
    )

            if not match:
                st.error("❌ Failed to extract revision information from LLM output.")
                st.stop()

            needs_revision = match.group(1).strip().upper()
            claude_nudge = match.group(2).strip()
            table_name = st.session_state.selected_table

            # Initial session state setup
            if "schemas_dictionary" not in st.session_state:
                st.session_state.schemas_dictionary = {}

            if "retry_clicked" not in st.session_state:
                st.session_state.retry_clicked = False

            # Show nudge input section — even if revision is not needed
            if not st.session_state.retry_clicked:
                st.markdown("### 🤖 AI Schema Migrator Suggests a Nudge")
                st.markdown(f"**NEEDS REVISION:** {needs_revision}")
                st.markdown(f"**NUDGE:** {claude_nudge}")

                user_nudge = st.text_area(
                    "✏️ Enter your own nudge (optional):",
                    value="",
                    placeholder="Type your custom nudge here to override AI Schema Migrator's suggestion..."
                )

                st.session_state.effective_nudge = user_nudge.strip() if user_nudge.strip() else claude_nudge

            # Use persisted nudge
            effective_nudge = st.session_state.get("effective_nudge", claude_nudge)

            # Retry button — always visible if user provides any nudge
            if st.button("🔁 Apply Nudge and Retry Modeling"):
                st.session_state.retry_clicked = True
                st.rerun()

            # --- Retry logic ---
            if st.session_state.retry_clicked:
                st.success(f"🔁 Retrying with nudge: `{effective_nudge}`")

                retry_prompt = f"""
                You are building a MongoDB document schema based on the following:

                - Modeling decision: {st.session_state.schemas_dictionary.get(table_name, '')}
                - Nudge: {effective_nudge}
                - Columns: {columns}
                - Foreign keys: {fks}

                ---

                Output:
                1. MongoDB schema document (in JSON format, no explanations).
                2. Then, briefly justify why this schema structure was chosen.
                """

                new_recommendation = call_claude_api(
                    prompt=retry_prompt,
                    system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
                )

                st.session_state.schemas_dictionary[table_name] = new_recommendation

                st.markdown("### 📦 Updated Schema with Nudge")
                st.code(new_recommendation)

                # Re-run evaluation with new schema
                prompt_repeat = f"""
                You are evaluating whether a MongoDB document schema is correctly designed to match the actual SQL query patterns.

                Here is the SQL query workload:

                {queries}

                Here is the current MongoDB document schema:

                {st.session_state.schemas_dictionary[table_name]}

                Your task is to analyze whether this schema aligns well with the access patterns shown in the queries.

                Respond in this strict format only:

                NEEDS REVISION: <YES or NO>  
                JUSTIFICATION: <one-line reason>  
                NUDGE: <short suggested direction or 'None'>
                """

                new_evaluation = call_claude_api(
                    prompt=prompt_repeat,
                    system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
                )

                st.session_state.schema_evaluation = new_evaluation

                # Parse reevaluation output
                reevaluation_match = re.search(
                    r"NEEDS REVISION:\s*(YES|NO).*?NUDGE:\s*(.*)",
                    new_evaluation,
                    re.DOTALL
                )

                if not reevaluation_match:
                    st.error("❌ Failed to extract reevaluation information.")
                    st.stop()

                needs_revision = reevaluation_match.group(1).strip().upper()
                claude_nudge = reevaluation_match.group(2).strip()


                # --- Show next round of suggestion (same UI as before) ---
                st.markdown("### 🔍 Reevaluation Result – AI Schema Migrator Suggests a Nudge")
                st.markdown(f"**NEEDS REVISION:** {needs_revision}")
                st.markdown(f"**NUDGE:** {claude_nudge}")

                user_nudge = st.text_area(
                    "✏️ Enter your own nudge (optional):",
                    value="",
                    placeholder="Type your custom nudge here to override AI Schema Migrator's suggestion...",
                    key=f"new_nudge_{table_name}"  # Prevent Streamlit reuse issues
                )

                st.session_state.effective_nudge = user_nudge.strip() if user_nudge.strip() else claude_nudge

                if st.button("🔁 Apply Nudge and Retry Modeling Again"):
                    st.session_state.retry_clicked = True
                    st.rerun()


            # Final Step: Save and Insert
            if st.button("💾 Generate Files and Insert Sample Document"):
                generated_code = get_mongo_schema_code_with_claude(
                    st.session_state.schemas_dictionary[table_name], table_name
                )

                save_generated_schema_files(generated_code)

                result = subprocess.run(["python3", "insert_generated_doc.py"], capture_output=True, text=True)

                st.markdown("### ✅ Insert Result")
                st.code(result.stdout)

                # Helpful link or next steps for user

                st.markdown("""
    ### 🔍 View Your Inserted Document

    If you're using **MongoDB Atlas**, you can check the inserted document here:  
    👉 [Go to MongoDB Atlas](https://cloud.mongodb.com)

    Once logged in, navigate to:

    **Cluster → Collections → _[Your Database]_ → _[Your Collection]_**

    to confirm the document was inserted successfully.
    """)

