from custom_components.carpiquet_ems.command_pipeline import (
    CommandRequest,
    SafetyContext,
    evaluate_command,
    MODE_SHADOW,
    MODE_ARMED,
)


def _ctx(**kwargs):
    data = dict(
        grid_available=True,
        hyper_available=True,
        solarflow_available=True,
        initialization_ready=True,
        fallback_active=False,
        allow_fallback=True,
        hyper_soc=50.0,
        solarflow_soc=50.0,
        hyper_min_soc=10.0,
        solarflow_min_soc=10.0,
        hyper_pv_w=200.0,
        solarflow_pv_w=300.0,
        hyper_max_power_w=1200.0,
        solarflow_max_power_w=2400.0,
        source_age_seconds=2.0,
    )
    data.update(kwargs)
    return SafetyContext(**data)


def test_shadow_valid_command_is_only_would_send():
    decision = evaluate_command(MODE_SHADOW, CommandRequest(600.0, 700.0), _ctx())
    assert decision.safety_ok is True
    assert decision.would_send_command is True
    assert decision.write_locked is True
    assert decision.validated.hyper_output_w == 600.0


def test_armed_remains_write_locked():
    decision = evaluate_command(MODE_ARMED, CommandRequest(600.0, 700.0), _ctx())
    assert decision.safety_ok is True
    assert decision.would_send_command is False
    assert decision.write_locked is True


def test_stale_data_rejects_command():
    decision = evaluate_command(
        MODE_SHADOW, CommandRequest(600.0, 700.0), _ctx(source_age_seconds=120.0)
    )
    assert decision.safety_ok is False
    assert decision.validated.hyper_output_w == 0.0
    assert "Données trop anciennes" in decision.safety_reason


def test_min_soc_allows_only_direct_pv():
    decision = evaluate_command(
        MODE_SHADOW, CommandRequest(900.0, 700.0), _ctx(hyper_soc=10.0, hyper_pv_w=220.0)
    )
    assert decision.validated.hyper_output_w == 220.0
    assert decision.safety_limited is True
