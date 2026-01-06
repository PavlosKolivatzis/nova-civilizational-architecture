from nova.compliance.arhp import (
    ArhpEnvelope,
    ArhpExpressionOutput,
    ArhpRefusalEvent,
    ArhpSilenceToken,
    verify_compliance,
)


def _make_envelope(domain: str = "R") -> ArhpEnvelope:
    return ArhpEnvelope(
        envelope_id="env-test",
        timestamp="2026-01-06T00:00:00Z",
        domain=domain,
        intent="explain",
        constraints={
            "forbidden_moves": ["advice", "decision", "normative_claim"],
            "required_labels": ["uncertainty"],
        },
        allowed_outputs=["explanation"],
        silence_policy={"on_violation": "emit_refusal"},
    )


def test_safe_string_passes() -> None:
    envelope = _make_envelope()
    result = verify_compliance(envelope, "This may occur in some contexts.")
    assert isinstance(result, ArhpExpressionOutput)
    assert result.envelope_id == envelope.envelope_id
    assert result.refusal is None


def test_prescriptive_string_refuses() -> None:
    envelope = _make_envelope()
    result = verify_compliance(envelope, "You should immediately stop.")
    assert isinstance(result, ArhpRefusalEvent)
    assert "prescriptive_or_normative_language" in result.violations
    assert result.envelope_id == envelope.envelope_id


def test_silence_token_pass_through() -> None:
    envelope = _make_envelope()
    token = ArhpSilenceToken(envelope_id=envelope.envelope_id)
    result = verify_compliance(envelope, token)
    assert isinstance(result, ArhpSilenceToken)
    assert result.envelope_id == envelope.envelope_id


def test_refusal_event_is_attached_to_envelope() -> None:
    envelope = _make_envelope()
    refusal = ArhpRefusalEvent(
        refusal_code="TEST",
        domain=envelope.domain,
        reason_class="test",
    )
    result = verify_compliance(envelope, refusal)
    assert isinstance(result, ArhpRefusalEvent)
    assert result.envelope_id == envelope.envelope_id


def test_output_type_not_allowed() -> None:
    envelope = _make_envelope()
    output = ArhpExpressionOutput(
        envelope_id=envelope.envelope_id,
        rendered_text="This may be acceptable.",
        labels={"uncertainty": "medium"},
        output_type="render",
    )
    result = verify_compliance(envelope, output)
    assert isinstance(result, ArhpRefusalEvent)
    assert "output_type_not_allowed" in result.violations
