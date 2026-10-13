from .awb import AWB
from .blc import BLC

# Registry used by the pipeline config. Add new modules here (dpc, demosaic, ccm, gamma ...).
REGISTRY = {cls.name: cls for cls in (BLC, AWB)}

__all__ = ["BLC", "AWB", "REGISTRY"]
