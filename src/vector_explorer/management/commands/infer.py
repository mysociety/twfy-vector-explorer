# Create a new file named `import_transcripts.py` in your Django app's `management/commands` directory.

from typing import Optional

from django.core.management.base import BaseCommand

from vector_explorer.data_manager import TranscriptXMl
from vector_explorer.models import ParagraphVector


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

    def handle(
        self,
        *,
        transcript_type: Optional[str],
        chamber_type: Optional[str],
        pattern: str,
        **kwargs,
    ):
        valid_transcript_formats = TranscriptXMl.get_transcript_manager(
            chamber=chamber_type, transcript=transcript_type
        )

        for transcript_format in valid_transcript_formats:
            print(f"Importing transcripts for {transcript_format.label}")
            for file_path, df in transcript_format.get_embeddings(
                pattern=pattern, infer_missing=True
            ):
                ParagraphVector.ingest_df(
                    source_file=file_path.name, df=df, verbose=True
                )
