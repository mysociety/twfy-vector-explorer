from typing import Annotated

from django.db import models

import numpy as np
from numpy.typing import NDArray
from pgvector.django import VectorField

from .tools.model_helpers import field

FloatArray384 = Annotated[NDArray[np.float64], 384]

class ParagraphVector(models.Model):
    speech_id = models.CharField()
    paragraph_id = models.CharField()
    text = models.TextField()
    embedding: FloatArray384 = field(VectorField, dimensions=384)