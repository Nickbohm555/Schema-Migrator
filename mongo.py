import os
import git
import tempfile
from pathlib import Path
import anthropic
import shutil
import yaml

from dotenv import load_dotenv
load_dotenv()

import re

import json
from datetime import datetime


import re
from collections import defaultdict

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



import os

def get_mongo_schema_code_with_claude(schema_block: str, table_name: str) -> str:
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    """
    Uses Claude to generate a complete Python script that inserts multiple MongoDB documents
    using a real Atlas connection.
    """
    prompt = f"""
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
        prompt=prompt,
        system_prompt="You generate production-ready Python scripts that insert MongoDB documents using Atlas connection."
    )



import re
from collections import defaultdict

import re
from collections import defaultdict

import re
from collections import defaultdict

import re
from collections import defaultdict


import re
from collections import defaultdict

def parse_claude_response(text):
    tables = defaultdict(list)
    current_table = None
    buffer = []

    lines = text.strip().splitlines()

    for line in lines:
        line = line.strip()

        # Detect new table section headers like "TABLE USERS:"
        m = re.match(r'^TABLE\s+([A-Z_]+):$', line)
        if m:
            # Save any buffered query before switching to a new table
            if current_table and buffer:
                query = " ".join(buffer).strip()
                if query:
                    tables[current_table].append(query)
                buffer = []

            current_table = m.group(1)
            continue

        # Query lines start with "- "
        if line.startswith("- "):
            # If there is a buffered query, save it before starting a new one
            if buffer:
                query = " ".join(buffer).strip()
                if query:
                    tables[current_table].append(query)
                buffer = []

            # Start buffering this new query line (without the "- ")
            buffer.append(line[2:].strip())
        else:
            # Continuation line (for multiline queries), add to buffer
            if buffer:
                buffer.append(line)
            # else ignore lines outside query or table sections

    # Add last buffered query if any
    if current_table and buffer:
        query = " ".join(buffer).strip()
        if query:
            tables[current_table].append(query)

    # Return as a normal dict
    return dict(tables)






from pathlib import Path

def save_generated_schema_files(code: str, filename: str = "insert_generated_doc.py"):
    with open(filename, "w") as f:
        f.write(code)
    print(f"✅ Schema code saved to {filename}")




def extract_schema_recommendation_blocks(modeling_output: str) -> str:
    start = modeling_output.find("**1. MongoDB Schema Recommendation**")
    end = modeling_output.find("**2. Justification for MongoDB Schema**")
    return modeling_output[start:end].strip() if start != -1 and end != -1 else ""

def extract_justification_block(modeling_output: str) -> str:
    """
    Extracts the justification section for the MongoDB schema from the full modeling output.
    """
    start = modeling_output.find("**2. Justification for MongoDB Schema**")
    end = modeling_output.find("**3. Rewritten Application Code")
    return modeling_output[start:end].strip() if start != -1 and end != -1 else ""


# Extract table names from formatted DDL response
def extract_table_names_from_ddl(ddl_text):
    return re.findall(r"TABLE (\w+):", ddl_text)

# Ask the developer to choose a table name
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

    # Auto-generate the question in required format
    generated_question = f"How should I model the {table_name} table in MongoDB? Please explain the reasoning."
    return table_name, generated_question


def load_mongodb_guidelines():
    with open("mongodb_modeling_guidelines.txt", "r") as f:
        return f.read()

def extract_create_table_blocks(sql_text):
    """
    Extracts CREATE TABLE blocks from SQL text.

    Returns:
        list of str: List of CREATE TABLE statements
    """
    # Greedy until first closing ); for each CREATE TABLE
    create_blocks = re.findall(
        r'CREATE\s+TABLE\s+.*?\(.*?\);', sql_text,
        re.IGNORECASE | re.DOTALL
    )
    return [block.strip() for block in create_blocks]



def extract_sql_queries_from_java(java_code):
    """
    Extract potential SQL queries from Java code.

    Removes comments before searching string literals for SQL keywords.

    Args:
        java_code (str): Raw Java source code

    Returns:
        list[str]: A list of strings likely to be SQL queries
    """
    # Step 1: Remove single-line and multi-line comments
    def remove_comments(code):
        # Remove multiline comments: /* ... */
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove single-line comments: //
        code = re.sub(r'//.*', '', code)
        return code

    code_no_comments = remove_comments(java_code)

    # Step 2: Capture all string literals
    string_literals = re.findall(r'"((?:[^"\\]|\\.)*?)"', code_no_comments, re.DOTALL)

    # Step 3: Filter literals that likely contain SQL
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

# Global Claude client instance
claude_client = None

def get_claude_client():
    """Get or initialize Claude client"""
    global claude_client
    if claude_client is None:
        claude_client = initialize_claude_client()
    return claude_client

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




def clone_and_analyze_repo(repo_url, local_path=None):
    """
    Clone a Git repository and analyze its Java and SQL files
    
    Args:
        repo_url (str): URL of the Git repository
        local_path (str, optional): Local path to clone to. If None, uses temp directory
    
    Returns:
        dict: Information about the repository and its files
    """


    
    # If no local path specified, use a temporary directory
    if local_path is None:
        temp_dir = tempfile.mkdtemp()
        local_path = os.path.join(temp_dir, "repo")
        cleanup_temp = True
    else:
        cleanup_temp = False
    
    try:
        print(f"Cloning repository from {repo_url}...")
        
        # Clone the repository
        repo = git.Repo.clone_from(repo_url, local_path)
        
        print(f"Repository cloned to: {local_path}")
        
        # Analyze the repository
        repo_info = analyze_repository(local_path)
        
        return repo_info, local_path
        
    except git.exc.GitCommandError as e:
        print(f"Error cloning repository: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None

def analyze_repository(repo_path):
    """
    Analyze the repository for Java and SQL files
    
    Args:
        repo_path (str): Path to the cloned repository
    
    Returns:
        dict: Analysis results
    """
    
    repo_path = Path(repo_path)
    
    # Find Java and SQL files
    java_files = list(repo_path.rglob("*.java"))
    sql_files = list(repo_path.rglob("*.sql"))
    
    # Also look for SQL in other common extensions
    sql_extensions = ["*.sql", "*.ddl", "*.dml", "*.psql", "*.mysql"]
    all_sql_files = []
    for ext in sql_extensions:
        all_sql_files.extend(repo_path.rglob(ext))
    
    # Remove duplicates
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

def read_file_contents(file_paths):
    """
    Read contents of specified files
    
    Args:
        file_paths (list): List of file paths to read
        max_files (int): Maximum number of files to read (to avoid memory issues)
    
    Returns:
        dict: File contents mapped by file path
    """
    
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





# Example usage
if __name__ == "__main__":







    # Example: Spring PetClinic (Java + SQL repository)
    repo_url = "https://github.com/doubleirish/lecture1_jdbc.git"
    
    
    print("Starting repository analysis...")
    
    # Clone and analyze the repository
    repo_info, local_path = clone_and_analyze_repo(repo_url)
    
    if repo_info:
        print("\n" + "="*50)
        print("REPOSITORY ANALYSIS SUMMARY")
        print("="*50)
        print(f"Repository path: {repo_info['repo_path']}")
        print(f"Java files found: {repo_info['java_count']}")
        print(f"SQL files found: {repo_info['sql_count']}")
        print(f"Total relevant files: {repo_info['total_files']}")
        
       
        # Read contents of a few files as examples
        print("\n" + "="*50)
        print("READING FILE CONTENTS")
        print("="*50)
        
        # Read a few Java files
        if repo_info['java_files']:
            #print("\nReading Java files...")
            java_contents = read_file_contents(repo_info['java_files'])
            
            
        # Read SQL files
        if repo_info['sql_files']:
            #print("\nReading SQL files...")
            sql_contents = read_file_contents(repo_info['sql_files'])


        print("\n" + "="*50)
        #print("ANALYZING JAVA FILES FOR SQL RELATIONSHIPS")
        print("="*50)

        all_sql_snippets = []


        for file_path, content in java_contents.items():
            if not content:
                continue

            # Extract SQL queries first
            sql_snippets = extract_sql_queries_from_java(content)
            if not sql_snippets:
                
                continue  # Skip files with no SQL
                
            for snippet in sql_snippets:
                all_sql_snippets.append(f"-- From file: {file_path}\n{snippet}")



        sql_snippets_combined = "\n\n".join(all_sql_snippets)
        

        
        example = """TABLE ORDERS:
TABLE ...:
- single-table query 1
- single-table query 2

TABLE ...:
- single-table query 3

JOINED QUERIES:
- query involving .. and ..
- query involving .., .., and ..

"""


        

        user_prompt = f"""

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
    -  multi-table query 2

4. Use uppercase table names for section headers (e.g., TABLE USERS).

5. Avoid duplicates: do not list the same query twice under the same table.

6. Ignore any lines that are not valid SQL (like logs, comments, or unrelated text).

7. Preserve the exact filenames and inline formatting of the queries.

IMPORTANT:
- Do NOT add any backticks (`) or triple backticks (```) around SQL queries.
- Output queries as plain text only, without any Markdown code formatting.

Example Input:
{example}

Here are the SQL snippets:

{sql_snippets_combined}

"""








        system_prompt = "You are a helpful expert in database design and schema interpretation."

        
        SQL_APPLICATION_CODE = call_claude_api(prompt=user_prompt, system_prompt=system_prompt)
        #print(f"\nClaude's response:\n{SQL_APPLICATION_CODE}")



        user_prompt = f"""

I have the following SQL queries grouped by tables, plus a separate section listing all multi-table JOIN queries at the bottom, exactly like this:

{SQL_APPLICATION_CODE}

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
        
        SQL_APPLICATION_CODE = call_claude_api(prompt=user_prompt, system_prompt=system_prompt)
        print(f"\nClaude's response:\n{SQL_APPLICATION_CODE}")



        all_ddl_blocks = []

        for file_path, content in sql_contents.items():
            if not content:
                continue
            ddl_blocks = extract_create_table_blocks(content)
            all_ddl_blocks.extend(ddl_blocks)

        ddl_combined = "\n\n".join(all_ddl_blocks)

        


        claude_prompt = f"""
            I extracted these SQL DDL snippets from a legacy database. Please identify each table’s primary key(s) and foreign key relationships.

            Format your response like this exactly:

            TABLE table_name:
            - Primary Key(s): col1, col2
            - Foreign Key(s):
            - local_col → referenced_table.referenced_col
            - another_col → another_table.another_col

            Here are the DDL blocks:

            {ddl_combined}
            """
        SQL_TABLES = call_claude_api(prompt=claude_prompt, system_prompt="You are an expert database architect.")
        #print(SQL_TABLES)


        parsed = parse_claude_response(SQL_APPLICATION_CODE)

        import pprint
        pprint.pprint(parsed)

        parsed_dict = parse_claude_output_to_dict(SQL_TABLES)

        import pprint
        pprint.pprint(parsed_dict)

        


        mongodb_guidelines = load_mongodb_guidelines()
        
                        # Ask for user question
                # === STEP 2: Developer asks a question ===
        # Extract table names

        
        print("\n" + "="*50)
        
        
        while True:
            available_tables = extract_table_names_from_ddl(SQL_TABLES)

            

            # Force structured question generation
            table_name, user_question = get_table_question_from_user(available_tables)



            queries = parsed[table_name]
            fks = parsed_dict[table_name]['foreign_keys']

            print(queries)
            print(fks)

            

            # Proceed with RAG-style prompt
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

            print(columns)


            # answer if we need to do embedding or refrenced

            

            
            final_prompt = f"""
You are helping design a MongoDB schema for a table from a legacy relational database.

Below is the relevant context:

📌 **Columns**
{columns}

🔗 **Foreign Keys**
{fks}

📝 **Representative SQL Queries**
{queries}

📚 **Guidelines**
{mongodb_guidelines}

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




        

            model_decision = call_claude_api(
                prompt=final_prompt,
                system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
            )

            print(model_decision)


            final_prompt = f"""
You are building a MongoDB document schema based on the following:

- Columns: {columns}
- Foreign keys: {fks}
- Modeling decision: {model_decision}

---

🎯 **Output Format**

1. The MongoDB schema (in JSON format only — no inline comments or explanations).
2. A justification section with **up to 5 concise bullet points** explaining why this structure was chosen.

🛑 **Important**
- Keep justifications practical and short (1 line each).
- Focus on reasons like query patterns, data ownership, update patterns, reusability, or write optimization.
"""




            # save schemas and justification to a dictionary 
        

            schema_block_and_justification = call_claude_api(
                prompt=final_prompt,
                system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
            )

            print(schema_block_and_justification)


            schemas_dictionary[table_name] = schema_block_and_justification

            prompt = f"""
                You are evaluating whether a MongoDB document schema is correctly designed to match the actual SQL query patterns.

                Here is the SQL query workload:

                {queries}

                Here is the current MongoDB document schema:

                {schemas_dictionary[table_name]}

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


            
            # First evaluation
            repeat = call_claude_api(
                prompt=prompt,
                system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
            )

            print(repeat)

            # Parse Claude's output
            match = re.search(r"NEEDS REVISION:\s*(YES|NO).*?NUDGE:\s*(.*)", repeat, re.DOTALL)

            if not match:
                print("❌ Failed to extract revision information.")
                exit(1)

            needs_revision = match.group(1).strip().upper()
            nudge = match.group(2).strip()

            # Ask user whether to apply the nudge
            user_input = input(f"Claude suggests: {nudge}\nDo you want to apply the nudge and retry modeling? (yes/no): ").strip().lower()

            while user_input == "yes" and needs_revision == "YES" and nudge.lower() != "none":
                print(f"\n🔁 Retrying with nudge: {nudge}\n")

                

                # Build schema prompt with nudge included again
                final_prompt = f"""
                    You are building a MongoDB document schema based on the following:

                    - Modeling decision: {model_decision}
                    - Nudge: {nudge}

                    ---

                    Output:
                    1. MongoDB schema document (in JSON format, no explanations).
                    2. Then, briefly justify why this schema structure was chosen.
                """

                model_decision = call_claude_api(
                    prompt=final_prompt,
                    system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
                )

                print(model_decision)

                # Save the new version
                schemas_dictionary[table_name] = model_decision

                # Re-run the evaluation
                prompt = f"""
                    You are evaluating whether a MongoDB document schema is correctly designed to match the actual SQL query patterns.

                    Here is the SQL query workload:

                    {queries}

                    Here is the current MongoDB document schema:

                    {schemas_dictionary[table_name]}

                    Your task is to analyze whether this schema aligns well with the access patterns shown in the queries.

                    Respond in this strict format only:

                    NEEDS REVISION: [YES or NO]

                    IF YES, give a one-line explanation why and suggest what direction to take (e.g., "consider embedding X", "add indexing", "split this field", etc).

                    IF NO, confirm that the schema aligns well with query access patterns.

                    ---

                    NEEDS REVISION: <YES or NO>  
                    JUSTIFICATION: <one-line reason>  
                    NUDGE: <short suggested direction or 'None'>
                """

                repeat = call_claude_api(
                    prompt=prompt,
                    system_prompt="You are a MongoDB schema design expert helping with SQL to MongoDB migrations."
                )

                print("\n🔍 Reevaluation:")
                print(repeat)

                # Update variables for next loop
                match = re.search(r"NEEDS REVISION:\s*(YES|NO).*?NUDGE:\s*(.*)", repeat, re.DOTALL)
                if not match:
                    print("❌ Failed to extract revision information on retry.")
                    break

                needs_revision = match.group(1).strip().upper()
                nudge = match.group(2).strip()

                user_input = input(f"\nClaude suggests again: {nudge}\nRetry again? (yes/no): ").strip().lower()


            
            import subprocess

            generated_code = get_mongo_schema_code_with_claude(schema_block_and_justification, table_name)
            save_generated_schema_files(generated_code)

            result = subprocess.run(["python3", "insert_generated_doc.py"], capture_output=True, text=True)
            print(result.stdout)
            
            
            

