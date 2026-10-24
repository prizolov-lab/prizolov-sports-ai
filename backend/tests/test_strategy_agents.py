# ============================================
# Copyright (c) 2026
# PRIZOLOV SPORTS AI
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""Стратегические агенты: правила выбора и заморозка/подтверждение Q4 по каждому."""

from datetime import UTC, datetime, timedelta

import pytest

from app.engine import agenomics_evidence as ae
from app.engine.strategy_agents import BY_ID, STRATEGY_AGENTS

PROBS = {"1": 0.48, "X": 0.27, "2": 0.25}
CLOSE = {"1": 0.36, "X": 0.29, "2": 0.35}


def test_picks_differ_by_strategy():
    assert BY_ID["prizolov-forecast-agent"].pick(PROBS)[0] == "1"
    assert BY_ID["prizolov-nodraw-agent"].pick(CLOSE)[0] == "1"
    assert BY_ID["prizolov-underdog-agent"].pick(PROBS)[0] == "2"
    assert BY_ID["prizolov-drawhunter-agent"].pick(CLOSE)[0] == "X"
    assert BY_ID["prizolov-drawhunter-agent"].pick(PROBS)[0] == "1"
    assert BY_ID["prizolov-homebias-agent"].pick({"1": 0.30, "X": 0.25, "2": 0.45})[0] == "2"
    assert BY_ID["prizolov-homebias-agent"].pick({"1": 0.36, "X": 0.25, "2": 0.39})[0] == "1"


def test_agent_ids_unique():
    ids = [a.agent_id for a in STRATEGY_AGENTS]
    assert len(ids) == len(set(ids)) and ids[0] == ae.AGENT_ID


@pytest.mark.skipif(not ae.available(), reason="нужен agenomics >= 0.9.6")
def test_each_agent_frozen_and_confirmed(tmp_path):
    store = ae.EvidenceStore(str(tmp_path / "e.db"))
    now = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    for spec in STRATEGY_AGENTS:
        sel, p = spec.pick(PROBS)
        n = ae.freeze_forecasts(
            store, [{"event_id": 7, "market_id": 1, "prediction_id": 1, "selection": sel, "probability": p}],
            70.0, "Conditional", "hash", now, agent_id=spec.agent_id)
        assert n == 1
        again = ae.freeze_forecasts(
            store, [{"event_id": 7, "market_id": 1, "prediction_id": 1, "selection": sel, "probability": p}],
            70.0, "Conditional", "hash", now, agent_id=spec.agent_id)
        assert again == 0  # повторной заморозки нет
    confirmed = ae.confirm_event(store, 7, "1", "ref", now + timedelta(hours=3),
                                 agent_ids=[a.agent_id for a in STRATEGY_AGENTS])
    assert confirmed == len(STRATEGY_AGENTS)
    wrong = {a.agent_id: ae.evidence_summary(store, a.agent_id)["forecast_wrong"] for a in STRATEGY_AGENTS}
    assert wrong["prizolov-underdog-agent"] == 1 and wrong["prizolov-forecast-agent"] == 0
    store.close()
