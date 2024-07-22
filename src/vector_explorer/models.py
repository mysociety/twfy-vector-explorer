from __future__ import annotations

from typing import Annotated, Callable, TypeVar, Union

from django.db import models
from django.db.models import F

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pgvector.django import CosineDistance, HnswIndex, VectorField

from .tools.inference import Inference
from .tools.model_helpers import field

FloatArray384 = Annotated[NDArray[np.float64], 384]

M = TypeVar("M", bound=models.Model, covariant=True)


class DistanceQuerySet(models.QuerySet):
    """
    Include some extra functions on querysets avaliable to models
    """

    def pipe(self, item: Callable):
        return item(self)

    def search_distance(self, search_term: str, threshold: float = 0.4):
        infer = Inference(model_id="BAAI/bge-small-en-v1.5", local=False)
        embedding = infer.query([search_term])[0]

        return (
            self.alias(distance=CosineDistance("embedding", embedding))
            .filter(distance__lte=threshold)
            .annotate(distance=F("distance"))
            .order_by("distance")
        )

    def df(self, *args: Union[str, tuple[str, str]], **kwargs) -> pd.DataFrame:
        """
        Args will be passed to queryset.values.
        A tuple can be passed to rename a field in the dataframe.
        e.g. ("field_in_other_model__name", "model_name")
        will return a model name
        """
        rename_map = {x[0]: x[1] for x in args if isinstance(x, tuple)}
        items = [x[0] if isinstance(x, tuple) else x for x in args]
        return (
            self.values(*items, **kwargs).pipe(pd.DataFrame).rename(columns=rename_map)  # type: ignore
        )


class ParagraphVector(models.Model):
    source_file = models.CharField()
    speech_id = models.CharField()
    text = models.TextField()
    transcript_type = models.CharField()
    chamber_type = models.CharField()
    embedding: FloatArray384 = field(VectorField, dimensions=384)
    objects: DistanceQuerySet[ParagraphVector] = DistanceQuerySet.as_manager()  # type: ignore

    class Meta:
        indexes = [
            HnswIndex(
                name="nhsw_index",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    @classmethod
    def ingest_df(cls, *, source_file: str, df: pd.DataFrame, verbose: bool = True):
        # delete existing records for this source file

        if verbose:
            print(f"Loading {len(df)} records for {source_file}")

        cls.objects.filter(source_file=source_file).delete()
        to_create = []

        for _, row in df.iterrows():
            to_create.append(
                cls(
                    source_file=source_file,
                    speech_id=row["id"],
                    text=row["text"],
                    transcript_type=row["transcript_type"],
                    chamber_type=row["chamber_type"],
                    embedding=row["embedding"],
                )
            )

        cls.objects.bulk_create(to_create)
