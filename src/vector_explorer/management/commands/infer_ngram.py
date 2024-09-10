# Create a new file named `import_transcripts.py` in your Django app's `management/commands` directory.

from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection

import pandas as pd
from tqdm import tqdm
from vector_explorer.models import NgramVector


def drop_indexes():
    with connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS ngram_nhsw_index;")


def build_index():
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE INDEX ngram_nhsw_index ON vector_explorer_ngramvector USING hnsw (embedding vector_cosine_ops);"
        )


class BulkAdder:
    def __init__(self, batch_size=10000):
        self.batch_size = batch_size
        self.records: list[NgramVector] = []

    def add(self, records: list[NgramVector]):
        self.records.extend(records)
        if len(self.records) > self.batch_size:
            self.bulk_create()

    def bulk_create(self):
        if self.records:
            NgramVector.objects.bulk_create(self.records, batch_size=10000)
            tqdm.write(f"Created {len(self.records)} records")
        self.records = []

    def finish(self):
        self.bulk_create()


class Command(BaseCommand):
    help = "Import nigram data"

    def handle(
        self,
        **kwargs,
    ):
        recreate_indexes: bool = True

        parquet_file = Path("data", "big_vector", "parts")

        # NgramVector.objects.all().delete()

        if recreate_indexes:
            print("dropping indexes")
            drop_indexes()

        # Create a ParquetFile object

        files = list(parquet_file.glob("*.parquet"))
        files.sort()

        adder = BulkAdder()

        starting = True
        for parquet_path in tqdm(files):
            if not starting:
                continue
            print(f"Reading {parquet_path}")
            df = pd.read_parquet(parquet_path)

            # Iterate over the file in chunks of chunk_size
            # Read the next chunk
            for _, row in df.iterrows():
                adder.add(
                    [
                        NgramVector(
                            text=row["ngram"],
                            count=row["count"],
                            embedding=row["embeddings"],
                        )
                    ]
                )
            df = None

        if recreate_indexes:
            print("recreating indexes")
            build_index()
            print("done")
