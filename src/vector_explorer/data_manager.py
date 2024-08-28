import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import sysrsync
from pydantic import BaseModel
from tqdm import tqdm

from vector_explorer.data_models.transcripts import DailyRecord
from vector_explorer.tools.inference import Inference
from vector_explorer.tools.model_helpers import MiniEnum, StrEnum

data_dir = Path("data", "pwdata")


class TranscriptType(StrEnum):
    DEBATES = "debates"
    WRITTEN_QUESTIONS = "written_questions"
    WRITTEN_STATEMENTS = "written_statements"


class ChamberType(StrEnum):
    UK_COMMONS = "uk_commons"
    UK_LORDS = "uk_lords"
    SCOTTISH_PARLIAMENT = "scottish_parliament"
    WELSH_SENEDD = "welsh_senedd"
    NI_ASSEMBLY = "ni_assembly"


class XMLManager(BaseModel):
    label: str
    relative_path: str
    file_structure_pre_date: str
    transcript_type: TranscriptType
    chamber_type: ChamberType

    def infer_missing(self, pattern: str = "", override: bool = False):
        dest_dir = data_dir / self.relative_path
        infer = Inference(model_id="BAAI/bge-small-en-v1.5", local=False)

        for file_path in tqdm(
            list(dest_dir.glob(f"{self.file_structure_pre_date}{pattern}*.xml")),
            desc="Infering missing embeddings",
        ):
            embeddings_file = file_path.with_suffix(".parquet")
            if not embeddings_file.exists() or override:
                record = DailyRecord.from_path(file_path)
                data = dict(record.iter_headings_and_paragraphs())
                df = infer.query_id_and_text(data)
                df.to_parquet(embeddings_file)

    def get_embeddings_n(self, pattern: str = "") -> int:
        dest_dir = data_dir / self.relative_path
        items = list(dest_dir.glob(f"{self.file_structure_pre_date}{pattern}*.xml"))
        return len(items)

    def get_embeddings(self, pattern: str = "", infer_missing: bool = False):
        dest_dir = data_dir / self.relative_path
        if infer_missing:
            self.infer_missing(pattern)

        for file_path in dest_dir.glob(
            f"{self.file_structure_pre_date}{pattern}*.parquet"
        ):
            df = pd.read_parquet(file_path)
            df["transcript_type"] = self.transcript_type
            df["chamber_type"] = self.chamber_type
            yield file_path, df

    def path_options(self, pattern: str = ""):
        dest_dir = data_dir / self.relative_path

        for file_path in dest_dir.glob(f"{self.file_structure_pre_date}{pattern}*"):
            yield file_path

    def validate_year(self, year: int):
        for file_path in self.path_options(str(year)):
            print(f"Validating {file_path}")
            DailyRecord.from_path(file_path)

    def download_pattern(self, pattern: str, quiet: bool = False):
        if not quiet:
            print(f"Downloading {self.label} for {pattern}")
        path = f"data.theyworkforyou.com::parldata/{self.relative_path}{self.file_structure_pre_date}{pattern}*"
        sysrsync.run(
            source=path,
            destination=str(data_dir),
            sync_source_contents=False,
            options=["-az", "--progress", "--relative"],
            exclusions=["'.svn'", "'tmp/'"],
        )

    def download_year(self, year: int):
        self.download_pattern(str(year))

    def get_date(
        self, date: datetime.date, update_download: bool = False
    ) -> Optional[DailyRecord]:
        iso_date = date.isoformat()
        if update_download:
            self.download_pattern(iso_date)
        options = sorted(list(self.path_options(iso_date)))
        if not options:
            return None
        return DailyRecord.from_path(options[-1])


class TranscriptXMl(MiniEnum[XMLManager]):
    UK_COMMONS_DEBATES = XMLManager(
        label="uk_commons_debates",
        relative_path="scrapedxml/debates/",
        file_structure_pre_date="debates",
        transcript_type=TranscriptType.DEBATES,
        chamber_type=ChamberType.UK_COMMONS,
    )
    UK_LORDS_DEBATES = XMLManager(
        label="uk_lords_debates",
        relative_path="scrapedxml/lordspages/",
        file_structure_pre_date="daylord",
        transcript_type=TranscriptType.DEBATES,
        chamber_type=ChamberType.UK_LORDS,
    )
    SCOTTISH_PARLIAMENT_DEBATES = XMLManager(
        label="scottish_parliament_debates",
        relative_path="scrapedxml/sp-new/meeting-of-the-parliament/",
        file_structure_pre_date="",
        transcript_type=TranscriptType.DEBATES,
        chamber_type=ChamberType.SCOTTISH_PARLIAMENT,
    )
    WELSH_SENEDD_DEBATES = XMLManager(
        label="welsh_senedd_debates",
        relative_path="scrapedxml/senedd/en/",
        file_structure_pre_date="senedd",
        transcript_type=TranscriptType.DEBATES,
        chamber_type=ChamberType.WELSH_SENEDD,
    )
    NI_ASSEMBLY_DEBATES = XMLManager(
        label="ni_assembly_debates",
        relative_path="scrapedxml/ni/",
        file_structure_pre_date="ni",
        transcript_type=TranscriptType.DEBATES,
        chamber_type=ChamberType.NI_ASSEMBLY,
    )

    @classmethod
    def get_transcript_manager(
        cls,
        chamber: Optional[str] = None,
        transcript: Optional[str] = None,
    ):
        for option in cls.options():
            if (chamber is None or option.chamber_type == chamber) and (
                transcript is None or option.transcript_type == transcript
            ):
                yield option

    @classmethod
    def download_all_debates(cls, year: int):
        for chamber in cls.options():
            chamber.download_year(year)
            chamber.validate_year(year)


if __name__ == "__main__":
    TranscriptXMl.download_all_debates(2023)
