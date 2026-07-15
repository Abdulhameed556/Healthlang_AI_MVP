"""Unit tests: S3-backed run store for chat evaluation."""
from unittest.mock import MagicMock, patch

import pytest

from ai.src.domain.chat_evaluation.entities import (
    ChatEvalReport,
    RunStatus,
)
from ai.src.infrastructure.chat_evaluation.s3_run_store import (
    S3RunStore,
    _agent_key,
    _meta_key,
    _run_key,
)

_BUCKET = "test-bucket"
_RUN_ID = "run-abc-123"
_AGENT_ID = "agent-xyz-456"


def _store() -> S3RunStore:
    with patch(
        "ai.src.infrastructure.chat_evaluation.s3_run_store.boto3"
    ):
        store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    return store


def _report(
    run_id: str = _RUN_ID,
    agent_id: str | None = _AGENT_ID,
    status: str = RunStatus.COMPLETED,
) -> ChatEvalReport:
    return ChatEvalReport(
        run_id=run_id,
        eval_mode="conversation",
        agent_id=agent_id,
        status=status,
        aggregate_scores={"judge_score": 0.8},
        created_at="2026-07-02T10:00:00+00:00",
    )


# ── key helpers ─────────────────────────────────────────────────────────────


def test_run_key_uses_run_id() -> None:
    assert _run_key("abc") == "chat-evaluation/runs/abc.json"


def test_meta_key_uses_agent_id_and_run_id() -> None:
    key = _meta_key("agent-1", "run-1")
    assert "agent-1" in key
    assert "run-1" in key


def test_meta_key_uses_global_when_no_agent() -> None:
    key = _meta_key(None, "run-1")
    assert "_global" in key


def test_agent_key_returns_id_when_present() -> None:
    assert _agent_key("ag-1") == "ag-1"


def test_agent_key_returns_global_when_none() -> None:
    assert _agent_key(None) == "_global"


# ── save ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_uploads_full_report_and_meta() -> None:
    mock_client = MagicMock()
    store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    store._client = mock_client

    report = _report()
    await store.save(report)

    assert mock_client.put_object.call_count == 2
    keys = {
        call.kwargs["Key"]
        for call in mock_client.put_object.call_args_list
    }
    assert _run_key(_RUN_ID) in keys
    assert _meta_key(_AGENT_ID, _RUN_ID) in keys


@pytest.mark.asyncio
async def test_save_sets_created_at_if_empty() -> None:
    mock_client = MagicMock()
    store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    store._client = mock_client

    report = ChatEvalReport(
        run_id=_RUN_ID,
        eval_mode="conversation",
        agent_id=_AGENT_ID,
        status=RunStatus.PENDING,
    )
    assert report.created_at == ""
    await store.save(report)
    assert report.created_at != ""


# ── get ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_returns_report_from_s3() -> None:
    import json

    mock_client = MagicMock()
    report = _report()
    import dataclasses

    body = json.dumps(dataclasses.asdict(report)).encode()
    mock_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=body))
    }

    store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    store._client = mock_client

    result = await store.get(_RUN_ID)

    assert result is not None
    assert result.run_id == _RUN_ID
    assert result.agent_id == _AGENT_ID


@pytest.mark.asyncio
async def test_get_returns_none_when_key_missing() -> None:
    from botocore.exceptions import ClientError

    mock_client = MagicMock()
    mock_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
        "GetObject",
    )

    store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    store._client = mock_client

    result = await store.get("nonexistent-run")

    assert result is None


# ── list ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_returns_summaries_for_agent() -> None:
    import json

    mock_client = MagicMock()
    meta = {
        "run_id": _RUN_ID,
        "eval_mode": "conversation",
        "agent_id": _AGENT_ID,
        "status": RunStatus.COMPLETED,
        "created_at": "2026-07-02T10:00:00+00:00",
        "aggregate_scores": {"judge_score": 0.8},
        "error": "",
    }
    meta_body = json.dumps(meta).encode()

    paginator = MagicMock()
    paginator.paginate.return_value = [
        {"Contents": [{"Key": _meta_key(_AGENT_ID, _RUN_ID)}]}
    ]
    mock_client.get_paginator.return_value = paginator
    mock_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=meta_body))
    }

    store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    store._client = mock_client

    results, total = await store.list(_AGENT_ID)

    assert total == 1
    assert len(results) == 1
    assert results[0].run_id == _RUN_ID
    assert results[0].status == RunStatus.COMPLETED


@pytest.mark.asyncio
async def test_list_returns_empty_when_no_runs() -> None:
    mock_client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [{"Contents": []}]
    mock_client.get_paginator.return_value = paginator

    store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    store._client = mock_client

    results, total = await store.list(_AGENT_ID)

    assert results == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_skips_corrupted_meta_entries() -> None:
    mock_client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {"Contents": [{"Key": "some/key.json"}]}
    ]
    mock_client.get_paginator.return_value = paginator
    mock_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"not-valid-json"))
    }

    store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    store._client = mock_client

    results, total = await store.list(_AGENT_ID)

    assert results == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_paginates_results() -> None:
    import json

    mock_client = MagicMock()

    def _meta_body(run_id: str, ts: str) -> bytes:
        return json.dumps({
            "run_id": run_id,
            "eval_mode": "conversation",
            "agent_id": _AGENT_ID,
            "status": RunStatus.COMPLETED,
            "created_at": ts,
            "aggregate_scores": {},
            "error": "",
        }).encode()

    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": _meta_key(_AGENT_ID, "run-1")},
                {"Key": _meta_key(_AGENT_ID, "run-2")},
                {"Key": _meta_key(_AGENT_ID, "run-3")},
            ]
        }
    ]
    mock_client.get_paginator.return_value = paginator
    mock_client.get_object.side_effect = [
        {"Body": MagicMock(read=MagicMock(return_value=_meta_body("run-1", "2026-07-03T10:00:00+00:00")))},
        {"Body": MagicMock(read=MagicMock(return_value=_meta_body("run-2", "2026-07-02T10:00:00+00:00")))},
        {"Body": MagicMock(read=MagicMock(return_value=_meta_body("run-3", "2026-07-01T10:00:00+00:00")))},
    ]

    store = S3RunStore(bucket=_BUCKET, region="us-east-1")
    store._client = mock_client

    results, total = await store.list(_AGENT_ID, page=1, page_size=2)

    assert total == 3
    assert len(results) == 2
    assert results[0].run_id == "run-1"  # newest first
    assert results[1].run_id == "run-2"
