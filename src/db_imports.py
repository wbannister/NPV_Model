import pyodbc
import pandas as pd
from dotenv import load_dotenv
import os


def extract_data(connection_string, query):
    # connect to the database
    with pyodbc.connect(connection_string) as conn:
        # execute the query and return the result as a pandas Dataframe
        df = pd.read_sql(query, conn)

    return df

# Build an absolute path to the .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# Access the variables
server = os.getenv('SERVER')
house_db = os.getenv('HOUSE_DB')
user_id = os.getenv('USER_ID')
db_password = os.getenv('DB_PASSWORD')

# Connection string for the house database
connection_string_house = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={house_db};"
    f"UID={user_id};"
    f"PWD={db_password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

query = '''SELECT * from dbo.business_plans'''

bp_df = extract_data(connection_string_house, query)

print(bp_df.head())
