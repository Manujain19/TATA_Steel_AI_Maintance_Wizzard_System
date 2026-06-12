from __future__ import annotations

from src.web_app import build_asset_context, build_plant_command_center


def test_asset_context_is_asset_specific():
    gearbox = build_asset_context("TSA-RM-GBX-002")
    hydraulic = build_asset_context("TSA-RM-HPP-003")
    assert gearbox["report"]["diagnosis"]["probable_fault"] != hydraulic["report"]["diagnosis"]["probable_fault"]
    assert gearbox["failure_cost_impact"]["production_loss_inr"] != hydraulic["failure_cost_impact"]["production_loss_inr"]


def test_command_center_has_dynamic_sections():
    command = build_plant_command_center()
    assert len(command["kpis"]) == 6
    assert len(command["sector_heatmap"]) == 6
    assert len(command["critical_assets"]) == 10
    assert len(command["predictive_timeline"]) == 4
