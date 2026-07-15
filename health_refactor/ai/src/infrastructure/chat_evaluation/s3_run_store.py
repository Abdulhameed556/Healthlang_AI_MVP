"""S3-backed run store for persistent chat evaluation results."""
from __future__ import annotations

import dataclasses
import json
import logging
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from ai.src.domain.chat_evaluation.entities import (
    ChatEvalReport,
    ConversationCaseResult,
    ConversationTurn,
)
from ai.src.domain.chat_evaluation.interfaces import IRunStore

logger = logging.getLogger(__name__)

_RUNS_PREFIX = "chat-evaluation/runs"
_AGENTS_PREFIX = "chat-evaluation/agents"
_NO_AGENT_KEY = "_global"


def _agent_key(agent_id: str | None) -> str:
    return agent_id or _NO_AGENT_KEY


def _run_key(run_id: str) -> str:
    return f"{_RUNS_PREFIX}/{run_id}.json"


def _meta_key(agent_id: str | None, run_id: str) -> str:
    return f"{_AGENTS_PREFIX}/{_agent_key(agent_id)}/runs/{run_id}.json"


def _report_to_dict(report: ChatEvalReport) -> dict:
    return dataclasses.asdict(report)


def _report_from_dict(data: dict) -> ChatEvalReport:
    case_results = []
    for raw in data.get("case_results", []):
        if raw.get("turns") is not None:
            turns = [ConversationTurn(**t) for t in raw.pop("turns", [])]
            case_results.append(ConversationCaseResult(**raw, turns=turns))
        else:
            case_results.append(raw)

    return ChatEvalReport(
        run_id=data["run_id"],
        eval_mode=data["eval_mode"],
        agent_id=data.get("agent_id"),
        status=data.get("status", "pending"),
        case_results=case_results,
        aggregate_scores=data.get("aggregate_scores", {}),
        error=data.get("error", ""),
        created_at=data.get("created_at", ""),
    )


def _meta_from_report(report: ChatEvalReport) -> dict:
    return {
        "run_id": report.run_id,
        "eval_mode": report.eval_mode,
        "agent_id": report.agent_id,
        "status": report.status,
        "created_at": report.created_at,
        "aggregate_scores": report.aggregate_scores,
        "error": report.error,
    }


class S3RunStore(IRunStore):
    def __init__(self, bucket: str, region: str | None = None) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            region_name=region,
        )

    async def save(self, report: ChatEvalReport) -> None:
        if not report.created_at:
            report.created_at = datetime.now(timezone.utc).isoformat()

        body = json.dumps(_report_to_dict(report), default=str).encode()
        meta_body = json.dumps(_meta_from_report(report)).encode()

        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=_run_key(report.run_id),
                Body=body,
                ContentType="application/json",
            )
            self._client.put_object(
                Bucket=self._bucket,
                Key=_meta_key(report.agent_id, report.run_id),
                Body=meta_body,
                ContentType="application/json",
            )
        except ClientError as exc:
            logger.error("S3RunStore.save failed: %s", exc)
            raise

    async def get(self, run_id: str) -> ChatEvalReport | None:
        try:
            obj = self._client.get_object(
                Bucket=self._bucket, Key=_run_key(run_id)
            )
            data = json.loads(obj["Body"].read())
            return _report_from_dict(data)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                return None
            logger.error("S3RunStore.get failed: %s", exc)
            raise

    async def list(
        self,
        agent_id: str | None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ChatEvalReport], int]:
        prefix = f"{_AGENTS_PREFIX}/{_agent_key(agent_id)}/runs/"
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self._bucket, Prefix=prefix)
            summaries: list[ChatEvalReport] = []
            for s3_page in pages:
                for obj in s3_page.get("Contents", []):
                    try:
                        meta_obj = self._client.get_object(
                            Bucket=self._bucket, Key=obj["Key"]
                        )
                        meta = json.loads(meta_obj["Body"].read())
                        summaries.append(
                            ChatEvalReport(
                                run_id=meta["run_id"],
                                eval_mode=meta["eval_mode"],
                                agent_id=meta.get("agent_id"),
                                status=meta.get("status", ""),
                                created_at=meta.get("created_at", ""),
                                aggregate_scores=meta.get(
                                    "aggregate_scores", {}
                                ),
                                error=meta.get("error", ""),
                            )
                        )
                    except (ClientError, KeyError, json.JSONDecodeError):
                        continue
            summaries.sort(key=lambda r: r.created_at or "", reverse=True)
            total = len(summaries)
            start = (page - 1) * page_size
            return summaries[start : start + page_size], total
        except ClientError as exc:
            logger.error("S3RunStore.list failed: %s", exc)
            raise
