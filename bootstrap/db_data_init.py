import pandas as pd
from pathlib import Path
from db import engine, MetaData, session
import os


def load_data():
    folder_path = Path('./bootstrap/data')

    # Get a list of all the files in the folder
    files = os.listdir(folder_path)

    metadata = MetaData()

    # reflect the database schema
    metadata.reflect(bind=engine)

    # Print the list of files
    for file in files:
        generated_table_name = file.title().strip('.Csv')
        tbl = generated_table_name

        table = metadata.tables[tbl]
        rows = session.query(table).count()

        if rows == 0:
            chunk_size = 10  # number of rows to read at a time

            # get the table object for the generated table name
            table = metadata.tables[tbl]

            # get the list of columns for the table
            columns = [c.name for c in table.columns]

            df = pd.read_csv(folder_path / file, chunksize=chunk_size, low_memory=True)

            # Create a Pandas dataframe from the CSV file
            for chunk in df:
                # with engine.connect() as conn:

                chunk.to_sql(name=tbl, con=engine, if_exists="append", index_label=table.columns, index=False,
                             method='multi')

