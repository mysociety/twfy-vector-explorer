# Create a new file named `import_transcripts.py` in your Django app's `management/commands` directory.

from typing import Optional

from django.core.management.base import BaseCommand
from django.db import connection

from tqdm import tqdm
from vector_explorer.data_manager import TranscriptXMl
from vector_explorer.models import ParagraphVector


def drop_indexes():
    with connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS nhsw_index;")


def build_index():
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE INDEX nhsw_index ON vector_explorer_paragraphvector USING hnsw (embedding vector_cosine_ops);"
        )


class BulkAdder:
    def __init__(self, batch_size=10000):
        self.batch_size = batch_size
        self.records: list[ParagraphVector] = []

    def add(self, records: list[ParagraphVector]):
        self.records.extend(records)
        if len(self.records) > self.batch_size:
            self.bulk_create()

    def bulk_create(self):
        if self.records:
            ParagraphVector.objects.bulk_create(self.records)
            tqdm.write(f"Created {len(self.records)} records")
        self.records = []

    def finish(self):
        self.bulk_create()


class Command(BaseCommand):
    help = "Import transcripts based on type, chamber, and pattern"

    def add_arguments(self, parser):
        parser.add_argument(
            "--transcript_type",
            type=str,
            help="Type of the transcript",
            default=None,
            required=False,
        )
        parser.add_argument(
            "--chamber_type",
            type=str,
            help="Type of the chamber",
            default=None,
            required=False,
        )
        parser.add_argument(
            "--pattern", type=str, help="Pattern to match", default="", required=False
        )

        parser.add_argument(
            "--recreate_indexes",
            type=bool,
            help="Recreate indexes",
            default=False,
            required=False,
        )

    def handle(
        self,
        *,
        transcript_type: Optional[str],
        chamber_type: Optional[str],
        pattern: str,
        recreate_indexes: bool,
        **kwargs,
    ):
        valid_transcript_formats = TranscriptXMl.get_transcript_manager(
            chamber=chamber_type, transcript=transcript_type
        )

        adder = BulkAdder()
        if recreate_indexes:
            print("dropping indexes")
            drop_indexes()

        existing_sources = set(
            ParagraphVector.objects.values_list("source_file", flat=True).distinct()
        )

        for transcript_format in valid_transcript_formats:
            print(f"Importing transcripts for {transcript_format.label}")

            files_to_import = transcript_format.get_embeddings_n(pattern=pattern)

            for file_path, df in tqdm(
                transcript_format.get_embeddings(pattern=pattern, infer_missing=True),
                total=files_to_import,
            ):
                if file_path.name in existing_sources:
                    tqdm.write(f"Skipping {file_path.name}")
                    continue
                records = ParagraphVector.ingest_df(
                    source_file=file_path.name, df=df, verbose=True, defer=True
                )
                if records:
                    adder.add(records)
        adder.finish()
        if recreate_indexes:
            print("recreating indexes")
            build_index()
