from __future__ import annotations

import logging
import sys
from collections.abc import Iterable as IterableABC

logger = logging.getLogger(__name__)


def apply_numpy_compat() -> None:
    """Patch removed NumPy 1.x aliases for optional ML libraries during import.

    The application code avoids deprecated NumPy APIs. This shim is only for
    third-party packages that still reference removed aliases while importing
    under NumPy 2.x.
    """
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover
        logger.warning("NumPy compatibility shim skipped: %s", exc)
        return

    alias_map = {
        "float": float,
        "int": int,
        "bool": bool,
        "complex": complex,
        "object": object,
        "float_": getattr(np, "float64", float),
        "int_": getattr(np, "int64", int),
        "NaN": getattr(np, "nan", float("nan")),
        "string_": getattr(np, "bytes_", bytes),
    }
    for name, value in alias_map.items():
        if name not in np.__dict__:
            try:
                setattr(np, name, value)
            except Exception:
                pass

    if "iterable" not in np.__dict__:
        try:
            setattr(np, "iterable", lambda value: isinstance(value, IterableABC))
        except Exception:
            pass

    if "matrix" not in np.__dict__:
        try:
            setattr(np, "matrix", getattr(np, "asmatrix", np.asarray))
        except Exception:
            pass

    ndarray_alias = getattr(np, "ndarray", object)
    try:
        import numpy.typing as npt

        if not hasattr(npt, "NDArray"):
            setattr(npt, "NDArray", ndarray_alias)
    except Exception:
        pass

    try:
        import numpy._typing as private_npt  # type: ignore

        if not hasattr(private_npt, "NDArray"):
            setattr(private_npt, "NDArray", ndarray_alias)
    except Exception:
        private_npt = sys.modules.get("numpy._typing")
        if private_npt is not None and not hasattr(private_npt, "NDArray"):
            try:
                setattr(private_npt, "NDArray", ndarray_alias)
            except Exception:
                pass
