"""Wires concrete dependencies into the chat evaluation pipeline."""
from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline
from ai.src.domain.chat_evaluation.entities import EvalMode
from ai.src.infrastructure.chat_evaluation.run_store import get_run_store


def build_chat_evaluation_pipeline(  # noqa: PLR0911
    eval_mode: str,
    conversation_source: str = "synthetic",
) -> ChatEvaluationPipeline:
    run_store = get_run_store()

    if eval_mode == EvalMode.INPUT_GUARDRAIL:
        from ai.src.application.chat_evaluation.steps.run_input_guardrail_cases import (  # noqa: E501
            RunInputGuardrailCasesStep,
        )
        steps = [RunInputGuardrailCasesStep()]

    elif eval_mode == EvalMode.SCENARIO:
        from ai.src.application.chat_evaluation.steps.label_expected_scenarios import (  # noqa: E501
            LabelExpectedScenariosStep,
        )
        from ai.src.application.chat_evaluation.steps.run_scenario_cases import (  # noqa: E501
            RunScenarioCasesStep,
        )
        from ai.src.application.retrieval.dependencies import (
            build_retrieval_pipeline,
        )
        from ai.src.infrastructure.chat_evaluation.scorer import (
            KBRelevancyScorer,
        )
        steps = [
            LabelExpectedScenariosStep(),
            RunScenarioCasesStep(
                build_retrieval_pipeline(), KBRelevancyScorer()
            ),
        ]

    elif eval_mode == EvalMode.OUTPUT_GUARDRAIL:
        from ai.src.application.chat_evaluation.steps.run_output_guardrail_cases import (  # noqa: E501
            RunOutputGuardrailCasesStep,
        )
        steps = [RunOutputGuardrailCasesStep()]

    elif eval_mode == EvalMode.E2E:
        from ai.src.application.chat_evaluation.steps.run_e2e_cases import (
            RunE2ECasesStep,
        )
        from ai.src.application.retrieval.dependencies import (
            build_retrieval_pipeline,
        )
        from ai.src.infrastructure.chat_evaluation.scorer import E2EScorer
        steps = [RunE2ECasesStep(build_retrieval_pipeline(), E2EScorer())]

    elif eval_mode == EvalMode.CONVERSATION:
        from ai.src.application.retrieval.dependencies import (
            build_retrieval_pipeline,
        )
        from ai.src.application.chat_evaluation.steps.run_conversation_cases import (  # noqa: E501
            RunConversationCasesStep,
        )
        from ai.src.application.chat_evaluation.steps.score_with_judge import (
            ScoreWithJudgeStep,
        )
        from ai.src.infrastructure.chat_evaluation.conversation_scorer import (
            ConversationScorer,
        )
        replay_step = RunConversationCasesStep(
            build_retrieval_pipeline(), ConversationScorer()
        )
        judge_step = ScoreWithJudgeStep()
        if conversation_source == "real":
            from ai.src.application.chat_evaluation.steps.load_real_conversations import (  # noqa: E501
                LoadRealConversationsStep,
            )
            steps = [LoadRealConversationsStep(), replay_step, judge_step]
        else:
            from ai.src.application.chat_evaluation.steps.generate_conversations import (  # noqa: E501
                GenerateConversationsStep,
            )
            steps = [GenerateConversationsStep(), replay_step, judge_step]

    else:
        raise ValueError(f"Unknown eval_mode: {eval_mode!r}")

    return ChatEvaluationPipeline(steps=steps, run_store=run_store)
