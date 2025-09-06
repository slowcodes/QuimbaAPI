import json

import pandas as pd
from pathlib import Path

from bootstrap.migration.migrate_lab_service import insert_lab_service
from bootstrap.migration.migrate_lab_service_params import insert_params
from bootstrap.migration.migrate_patients import insert_patients
from db import engine, session
import os
from sqlalchemy import text, MetaData

from sqlalchemy import text


def update_id_sequence(table_name, pk_column='id'):
    # Validate the table name and primary key column (basic safety)
    if not table_name.isidentifier() or not pk_column.isidentifier():
        raise ValueError("Invalid table or column name")

    # Build the assumed sequence name: {table}_{column}_seq
    sequence_name = f"{table_name}_{pk_column}_seq"

    # Create the SQL query to reset the sequence
    query = text(f"""
        SELECT setval(
            :sequence_name,
            COALESCE((SELECT MAX({pk_column})+1 FROM {table_name}), 1),
            false
        )
    """)

    # Execute the query with parameter binding
    session.execute(query, {'sequence_name': sequence_name})


def table_exists(tbl):
    """Check if a table exists in PostgreSQL"""
    query = text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :tbl)")
    result = session.execute(query, {"tbl": tbl.lower()}).fetchone()
    return result[0] if result else False


def get_row_count(tbl):
    """Get the row count of a table"""
    query = text(f"SELECT COUNT(*) FROM {tbl}")  # Query actual table
    result = session.execute(query).fetchone()
    return result[0] if result else 0


def load_pg_data():
    folder_path = Path('./bootstrap/data')

    # Get a list of all the files in the folder
    priority_files = ["lab_service_group","state", "user_role", "lga", "laboratory", "client_occupation", "user_privilege_listing", "person", "users"]

    def sort_key(file_path):
        file_name = file_path.stem.lower().strip()  # ✅ Get file name without extension
        if file_name in priority_files:
            return 0, priority_files.index(file_name)  # ✅ Use index() to enforce order
        return 1, file_name  # Non-priority files come later, sorted alphabetically

    files = sorted(folder_path.iterdir(), key=sort_key)

    for file in files:
        print(f"Processing file: {file}")  # Debugging output
        # tbl = os.path.splitext(file)[0].strip().lower()  # Normalize table name
        # print(f"Processing file: {file} -> Table: {tbl}")  # Debugging output

        tbl = os.path.splitext(os.path.basename(file))[0].strip().lower()
        if table_exists(tbl):
            print(f"✅ Table '{tbl}' exists.")
            rows = get_row_count(tbl)  # Get row count
            print(f"📊 Table '{tbl}' has {rows} rows.")

            if rows == 0:
                chunk_size = 10
                df = pd.read_csv(file, chunksize=chunk_size, low_memory=True)

                for chunk in df:
                    chunk.to_sql(name=tbl, con=engine, if_exists="append", index=False, method="multi")

                session.commit()  # Commit after inserting
                print(f"✅ Data inserted into '{tbl}'")

                # update auto increment id
                update_id_sequence(tbl)

            import_legacy_data(tbl, rows)
            update_id_sequence(tbl) # Update the sequence after data insertion

        else:
            print(f"⚠️ Table '{tbl}' does not exist in the database. Skipping...")

    session.close()  # Close session to free resources


def load_sqlite_data():
    folder_path = Path('./bootstrap/data')

    # Get a list of all the files in the folder
    files = sorted(os.listdir(folder_path), reverse=True)

    metadata = MetaData()

    try:
        metadata.reflect(bind=engine)  # Reflecting schema
        print("Tables found:", metadata.tables.keys())  # Debugging
    except Exception as e:
        print(f"Error reflecting metadata: {e}")
        return

    for file in files:
        tbl = os.path.splitext(file)[0].strip().lower()  # Normalize table name
        print(f"Processing file: {file} -> Table: {tbl}")  # Debugging output

        if tbl in metadata.tables:
            table = metadata.tables[tbl]
            rows = session.query(table).count()
            print(f"Table '{tbl}' exists with {rows} rows.")

            if rows == 0:
                chunk_size = 10
                df = pd.read_csv(folder_path / file, chunksize=chunk_size, low_memory=True)

                for chunk in df:
                    chunk.to_sql(name=tbl, con=engine, if_exists="append", index=False, method="multi")

                # query = text(f"UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM {tbl}) WHERE name = '{tbl}'")
                # session.execute(query)
            import_legacy_data(tbl, rows)

        else:
            print(f"Table '{tbl}' does not exist in the database. Skipping...")


def import_legacy_data(tbl: str, rows: int):
    if tbl == 'person' and rows < 5:
        # insert patients data
        with open("patients.json", "r") as fie:
            patients_data = json.load(fie)
        insert_patients(session, patients_data)

        # insert lab services
        with open("lab_services.json", "r") as fle:
            data = json.load(fle)
        insert_lab_service(session, data)

        # insert lab service parameters
        with open("parameters.json", "r") as file:
            data = json.load(file)
        insert_params(session, data)

    else:
        print("skipping patients data migration")
