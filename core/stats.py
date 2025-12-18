# core/stats.py
from __future__ import annotations

import statistics
from typing import List


def calculate_robust_z_score(values: List[float]) -> List[float]:
    """
    Calcula Z-Score robusto usando Mediana + MAD (Median Absolute Deviation).

    Z_robust = 0.6745 * (x - median) / MAD

    - Se tiver poucos valores ou MAD == 0, devolve zeros.
    """
    n = len(values)
    if n == 0:
        return []
    if n == 1:
        return [0.0]

    med = statistics.median(values)
    abs_dev = [abs(x - med) for x in values]
    mad = statistics.median(abs_dev)

    if mad == 0:
        return [0.0 for _ in values]

    factor = 0.6745 / mad
    return [(x - med) * factor for x in values]


def filter_outliers(values: List[float], threshold: float = 3.5) -> List[float]:
    """
    Remove outliers altos/baixos com base no Z-Score robusto.

    - threshold padrão 3.5 (valor clássico do "modified z-score")
    - Se tiver poucos pontos, retorna igual.
    """
    n = len(values)
    if n < 3:
        return values[:]

    z_scores = calculate_robust_z_score(values)
    clean: List[float] = []

    for v, z in zip(values, z_scores):
        if abs(z) <= threshold:
            clean.append(v)
        else:
            # Aqui poderíamos logar / marcar anomalia
            # Por enquanto só ignoramos o ponto.
            pass

    # Se por acaso filtrou tudo, volta original pra não zerar
    return clean if clean else values[:]
