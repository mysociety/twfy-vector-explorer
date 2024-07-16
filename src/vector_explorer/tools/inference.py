import os
from typing import Optional

import numpy as np
import requests
from fastembed import TextEmbedding
from numpy.typing import NDArray


class Inference:
    """
    Class to handle inference for text embeddings.
    Uses hugging faces free api if not local, but setting local
    will use fastembed's approach
    """

    def __init__(
        self, model_id: str, hf_token: Optional[str] = None, local: bool = False
    ):
        self.model_id: str = model_id
        self.hf_token = hf_token if hf_token else os.environ.get("HF_TOKEN", None)
        self.local = local
        if self.hf_token is None and self.local is False:
            raise ValueError("Need to set hf_token for remote embedding generation.")

    def query_local(self, texts: list[str]) -> list[NDArray[np.float64]]:
        model = TextEmbedding(model_name=self.model_id)
        return list(model.embed(texts))

    def query_remote(self, texts: list[str]) -> list[NDArray[np.float64]]:
        api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_id}"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": texts, "options": {"wait_for_model": True}},
        )
        return [np.array(x) for x in response.json()]

    def query(self, texts: list[str]):
        if self.local:
            return self.query_local(texts)
        else:
            return self.query_remote(texts)
