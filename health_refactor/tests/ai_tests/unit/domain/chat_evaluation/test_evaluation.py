"""Unit tests: ai/src/domain/chat_evaluation/entities.py + interfaces.py"""


# ── EvalMode / RunStatus constants ────────────────────────────────────────────


def test_eval_mode_values() -> None:
    from ai.src.domain.chat_evaluation.entities import EvalMode

    assert EvalMode.INPUT_GUARDRAIL == "input_guardrail"
    assert EvalMode.SCENARIO == "scenario"
    assert EvalMode.OUTPUT_GUARDRAIL == "output_guardrail"
    assert EvalMode.E2E == "e2e"
    assert EvalMode.CONVERSATION == "conversation"


def test_run_status_values() -> None:
    from ai.src.domain.chat_evaluation.entities import RunStatus

    assert RunStatus.PENDING == "pending"
    assert RunStatus.RUNNING == "running"
    assert RunStatus.COMPLETED == "completed"
    assert RunStatus.FAILED == "failed"


# ── GuardrailTestCase / GuardrailCaseResult ───────────────────────────────────


def test_guardrail_test_case_defaults() -> None:
    from ai.src.domain.chat_evaluation.entities import GuardrailTestCase

    tc = GuardrailTestCase(query="hello", should_block=False)
    assert tc.rules == []


def test_guardrail_case_result_fields() -> None:
    from ai.src.domain.chat_evaluation.entities import GuardrailCaseResult

    r = GuardrailCaseResult(
        query="hi",
        expected_blocked=True,
        actual_status="block",
        correct=True,
        attack_category="jailbreak",
    )
    assert r.correct is True
    assert r.attack_category == "jailbreak"
    assert r.blocked_reason is None


# ── ScenarioTestCase / ScenarioCaseResult ─────────────────────────────────────


def test_scenario_test_case_defaults() -> None:
    from ai.src.domain.chat_evaluation.entities import ScenarioTestCase

    tc = ScenarioTestCase(query="send money")
    assert tc.expected_scenario_ids == []


def test_scenario_case_result_kb_relevancy_optional() -> None:
    from ai.src.domain.chat_evaluation.entities import ScenarioCaseResult

    r = ScenarioCaseResult(
        query="send money",
        scenario_correct=True,
        actual_scenario_ids=["s1"],
        expected_scenario_ids=["s1"],
        kb_relevancy_score=None,
        kb_id_selected=None,
        reason="no KB needed",
    )
    assert r.kb_relevancy_score is None
    assert r.scenario_correct is True


# ── OutputGuardrailTestCase / OutputGuardrailCaseResult ───────────────────────


def test_output_guardrail_test_case_defaults() -> None:
    from ai.src.domain.chat_evaluation.entities import OutputGuardrailTestCase

    tc = OutputGuardrailTestCase(
        query="q", assistant_message="msg", expected_action="pass"
    )
    assert tc.rules == []


def test_output_guardrail_case_result_correct_flag() -> None:
    from ai.src.domain.chat_evaluation.entities import OutputGuardrailCaseResult

    r = OutputGuardrailCaseResult(
        query="q",
        expected_action="block",
        actual_status="block",
        correct=True,
    )
    assert r.correct is True
    assert r.violation_category is None


# ── E2ETestCase / E2ETurnResult / MetricResult ────────────────────────────────


def test_e2e_turn_result_defaults() -> None:
    from ai.src.domain.chat_evaluation.entities import E2ETurnResult

    r = E2ETurnResult(
        query="q",
        expected_answer="e",
        actual_response="a",
        input_guardrail_status="pass",
        scenario_ids=[],
        kb_id_selected=None,
        chunks_retrieved=0,
        output_guardrail_status="pass",
    )
    assert r.metrics == []
    assert r.pipeline_stopped is None


def test_metric_result_fields() -> None:
    from ai.src.domain.chat_evaluation.entities import MetricResult

    m = MetricResult(name="answer_relevancy", score=0.88, threshold=0.7, success=True)
    assert m.reason == ""
    assert m.success is True


# ── ChatEvalDataset ───────────────────────────────────────────────────────────


def test_chat_eval_dataset_defaults() -> None:
    from ai.src.domain.chat_evaluation.entities import ChatEvalDataset, EvalMode

    ds = ChatEvalDataset(
        dataset_id="d1", eval_mode=EvalMode.INPUT_GUARDRAIL, test_cases=[]
    )
    assert ds.created_at == ""
    assert ds.test_cases == []


# ── ConversationTurn / ConversationCaseResult ─────────────────────────────────


def test_conversation_turn_fields() -> None:
    from ai.src.domain.chat_evaluation.entities import ConversationTurn

    turn = ConversationTurn(
        user="My transfer is stuck.",
        agent_expected="Let me look into that.",
        agent_actual="I can help with your transfer.",
        input_guardrail_status="pass",
        output_guardrail_status="pass",
    )
    assert turn.scenario_ids == []
    assert turn.kb_id_selected is None
    assert turn.input_guardrail_status == "pass"


def test_conversation_turn_with_kb_and_scenarios() -> None:
    from ai.src.domain.chat_evaluation.entities import ConversationTurn

    turn = ConversationTurn(
        user="What are the fees?",
        agent_expected="Fees are 0%.",
        agent_actual="Afriex charges 0%.",
        input_guardrail_status="pass",
        output_guardrail_status="pass",
        scenario_ids=["fee_query"],
        kb_id_selected="afriex-kb-001",
    )
    assert turn.scenario_ids == ["fee_query"]
    assert turn.kb_id_selected == "afriex-kb-001"


def test_conversation_case_result_defaults() -> None:
    from ai.src.domain.chat_evaluation.entities import ConversationCaseResult

    r = ConversationCaseResult(
        scenario_id="scn-1",
        scenario_name="Transfer Issues",
        persona="frustrated_customer",
        run_index=0,
    )
    assert r.turns == []
    assert r.scores == {}
    assert r.run_index == 0


def test_conversation_case_result_with_scores() -> None:
    from ai.src.domain.chat_evaluation.entities import ConversationCaseResult

    r = ConversationCaseResult(
        scenario_id="scn-2",
        scenario_name="Fee Query",
        persona="calm_detailed",
        run_index=1,
        scores={
            "conversation_quality": 0.82,
            "kb_utilization": 0.75,
            "rule_adherence": 0.91,
        },
    )
    assert r.scores["conversation_quality"] == 0.82
    assert r.run_index == 1


# ── ChatEvalReport ────────────────────────────────────────────────────────────


def test_chat_eval_report_defaults() -> None:
    from ai.src.domain.chat_evaluation.entities import ChatEvalReport, RunStatus

    r = ChatEvalReport(run_id="r1", eval_mode="e2e", agent_id=None)
    assert r.status == RunStatus.PENDING
    assert r.case_results == []
    assert r.aggregate_scores == {}
    assert r.error == ""
