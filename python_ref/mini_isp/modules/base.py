"""Unified module interface: every stage is (image, meta) -> (image, meta).

- `image` stays in the linear DN domain as float64 in the reference model, so the
  C fixed-point model can be compared stage by stage without rescaling.
- `meta` carries information downstream stages need (e.g. black level already
  removed, AWB gains that were applied). Modules must not mutate the input dict.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class ISPModule(ABC):
    name: str = "base"

    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def run(self, img: np.ndarray, meta: dict) -> tuple[np.ndarray, dict]:
        ...

    def __call__(self, img: np.ndarray, meta: dict) -> tuple[np.ndarray, dict]:
        return self.run(img.astype(np.float64, copy=True), dict(meta))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.params})"
