from custom_components.carpiquet_ems.zendure_command_adapter import prepare_commands


def test_adapter_is_always_write_locked_and_dry_run():
    r = prepare_commands(hyper_entity="number.hyper", solarflow_entity="number.solar",
        hyper_requested_w=600, solarflow_requested_w=900, hyper_observed_w=100,
        solarflow_observed_w=200, previous_hyper_w=None, previous_solarflow_w=None,
        authorized=True, sequence=1)
    assert r.write_locked is True
    assert r.hyper.write_locked is True and r.solarflow.write_locked is True
    assert r.hyper.action == "DRY_RUN" and r.hyper.would_execute is True


def test_adapter_blocks_without_safety_authorization():
    r = prepare_commands(hyper_entity="number.hyper", solarflow_entity="number.solar",
        hyper_requested_w=600, solarflow_requested_w=900, hyper_observed_w=0,
        solarflow_observed_w=0, previous_hyper_w=None, previous_solarflow_w=None,
        authorized=False)
    assert r.hyper.action == "BLOCKED" and r.hyper.would_execute is False
    assert r.solarflow.action == "BLOCKED" and r.solarflow.would_execute is False


def test_adapter_deduplicates_near_observed_setting():
    r = prepare_commands(hyper_entity="number.hyper", solarflow_entity="number.solar",
        hyper_requested_w=503, solarflow_requested_w=1000, hyper_observed_w=500,
        solarflow_observed_w=0, previous_hyper_w=None, previous_solarflow_w=None,
        deadband_w=5, authorized=True)
    assert r.hyper.action == "DEDUPLICATED" and r.hyper.would_execute is False


def test_adapter_applies_secondary_ramp_limit():
    r = prepare_commands(hyper_entity="number.hyper", solarflow_entity="number.solar",
        hyper_requested_w=1200, solarflow_requested_w=0, hyper_observed_w=0,
        solarflow_observed_w=0, previous_hyper_w=100, previous_solarflow_w=0,
        ramp_limit_w=200, authorized=True)
    assert r.hyper.prepared_w == 300
    assert r.hyper.reason == "Rampe adaptateur appliquée"
