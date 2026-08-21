from custom_components.carpiquet_ems.command_pipeline import (
    CommandRequest,
    SafetyContext,
    evaluate_command,
    MODE_SHADOW,
    WATCHDOG_OK,
    WATCHDOG_GRID_STALE,
)


def _ctx(**kwargs):
    data = dict(
        grid_available=True,
        grid_fresh=True,
        hyper_available=True,
        solarflow_available=True,
        initialization_ready=True,
        fallback_active=False,
        allow_fallback=True,
        hyper_soc=50.0,
        solarflow_soc=50.0,
        hyper_min_soc=10.0,
        solarflow_min_soc=10.0,
        hyper_pv_w=0.0,
        solarflow_pv_w=0.0,
        hyper_max_power_w=1200.0,
        solarflow_max_power_w=2400.0,
        grid_source_age_seconds=2.0,
    )
    data.update(kwargs)
    return SafetyContext(**data)


def test_shadow_accepts_stable_zendure_values_when_grid_is_fresh():
    decision = evaluate_command(
        MODE_SHADOW,
        CommandRequest(300.0, 400.0),
        _ctx(),
    )
    assert decision.safety_ok is True
    assert decision.watchdog_state == WATCHDOG_OK
    assert decision.would_send_command is True
    assert decision.validated.hyper_output_w == 300.0
    assert decision.validated.solarflow_output_w == 400.0


def test_grid_stale_rejects_shadow_command():
    decision = evaluate_command(
        MODE_SHADOW,
        CommandRequest(300.0, 400.0),
        _ctx(grid_fresh=False, grid_source_age_seconds=75.0),
    )
    assert decision.safety_ok is False
    assert decision.watchdog_state == WATCHDOG_GRID_STALE
    assert decision.would_send_command is False
    assert decision.validated.hyper_output_w == 0.0
    assert "Compteur réseau" in decision.safety_reason


def test_min_soc_still_blocks_battery_discharge_but_allows_direct_pv():
    decision = evaluate_command(
        MODE_SHADOW,
        CommandRequest(500.0, 400.0),
        _ctx(hyper_soc=10.0, hyper_pv_w=125.0),
    )
    assert decision.safety_ok is True
    assert decision.validated.hyper_output_w == 125.0
    assert decision.safety_limited is True
