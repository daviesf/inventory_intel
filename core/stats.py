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


def calculate_coefficient_of_variation(values: List[float]) -> float:
    """
    Calcula o Coeficiente de Variação (CV) = desvio padrão / média.

    - CV baixo (<0.5): demanda estável → alta confiabilidade
    - CV médio (0.5-1.0): demanda moderada → média confiabilidade
    - CV alto (>1.0): demanda volátil → baixa confiabilidade

    Retorna 0.0 se não houver dados suficientes ou média zero.
    """
    if len(values) < 2:
        return 0.0

    mean = statistics.mean(values)
    if mean == 0:
        return 0.0

    stdev = statistics.stdev(values)
    return stdev / mean


def calculate_reliability_from_cv(cv: float, n_samples: int) -> tuple[float, str]:
    """
    Converte CV e número de amostras em reliability score e nível.

    Retorna (score, level) onde:
    - score: 0.0 a 1.0
    - level: 'high', 'medium', 'low'
    """
    # Penaliza se tiver poucos dados
    sample_penalty = 1.0 if n_samples >= 14 else (0.8 if n_samples >= 7 else 0.6)

    if cv < 0.3:
        base_score = 0.9
        level = "high"
    elif cv < 0.6:
        base_score = 0.7
        level = "medium"
    elif cv < 1.0:
        base_score = 0.5
        level = "medium"
    else:
        base_score = 0.3
        level = "low"

    final_score = base_score * sample_penalty
    return round(final_score, 2), level
