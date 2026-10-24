# ============================================
# Copyright (c) 2026
# PRIZOLOV SPORTS AI
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""Прогнозирующие агенты разных стратегий для набора Q4 в Agenomics.

Все агенты читают одни и те же вероятности 1/X/2 матча (консенсус
источников из Prediction.factors) и различаются только правилом выбора
исхода. Поэтому у них разная история точности, а значит, и разный Trust
Score на момент заморозки: это даёт Agenomics разброс score, которого не
было у единственного агента.

Важно для интерпретации: агенты оцениваются на одних и тех же матчах,
их исходы коррелируют. Это больше строк Q4, но не больше независимых
матчей. Число независимых событий считается по матчам, а не по строкам.

Агент "underdog" намеренно контрарный: это контрольный слабый агент, а не
рекомендация.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

Probs = Dict[str, float]
Pick = Tuple[str, float]


def _best(probs: Probs, keys: str) -> str:
    return max(keys, key=lambda k: probs.get(k, 0.0))


def consensus(probs: Probs) -> Pick:
    sel = _best(probs, "1X2")
    return sel, probs.get(sel, 0.0)


def no_draw(probs: Probs) -> Pick:
    sel = _best(probs, "12")
    return sel, probs.get(sel, 0.0)


def home_bias(probs: Probs) -> Pick:
    """Домашний бонус 0.10 к вероятности хозяев, ничьи не выбирает."""
    sel = "1" if probs.get("1", 0.0) + 0.10 >= probs.get("2", 0.0) else "2"
    return sel, probs.get(sel, 0.0)


def draw_hunter(probs: Probs) -> Pick:
    """Ничья, если команды близки по силе и вероятность ничьей заметна."""
    if probs.get("X", 0.0) >= 0.27 and abs(probs.get("1", 0.0) - probs.get("2", 0.0)) <= 0.12:
        return "X", probs.get("X", 0.0)
    return consensus(probs)


def underdog(probs: Probs) -> Pick:
    """Контрольный контрарный агент: менее вероятный из 1 и 2."""
    sel = "1" if probs.get("1", 0.0) < probs.get("2", 0.0) else "2"
    return sel, probs.get(sel, 0.0)


@dataclass(frozen=True)
class StrategyAgent:
    agent_id: str
    theme: str
    pick: Callable[[Probs], Pick]


STRATEGY_AGENTS = (
    StrategyAgent("prizolov-forecast-agent", "consensus", consensus),
    StrategyAgent("prizolov-nodraw-agent", "no-draw favourite", no_draw),
    StrategyAgent("prizolov-homebias-agent", "home advantage", home_bias),
    StrategyAgent("prizolov-drawhunter-agent", "draw hunter", draw_hunter),
    StrategyAgent("prizolov-underdog-agent", "contrarian control", underdog),
)

BY_ID = {a.agent_id: a for a in STRATEGY_AGENTS}


def probs_from_factors(factors) -> Probs:
    factors = factors or {}
    return {
        "1": float(factors.get("home_prob", 0.0)),
        "X": float(factors.get("draw_prob", 0.0)),
        "2": float(factors.get("away_prob", 0.0)),
    }
