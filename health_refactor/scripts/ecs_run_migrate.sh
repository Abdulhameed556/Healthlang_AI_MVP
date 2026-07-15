#!/usr/bin/env bash
# Run a one-off Fargate ECS task to apply Alembic migrations before service deploy.
set -euo pipefail

: "${AWS_REGION:?AWS_REGION is required}"
: "${CLUSTER:?CLUSTER is required}"
: "${TASK_DEFINITION:?TASK_DEFINITION is required}"
: "${CONTAINER_NAME:?CONTAINER_NAME is required}"
: "${IMAGE:?IMAGE is required}"

MIGRATE_CMD="${MIGRATE_CMD:-PYTHONPATH=. alembic -c backend/src/infrastructure/database/migrations/alembic.ini upgrade head}"

SUBNET_1="$(aws ssm get-parameter --name /devops/private-subnet-1 --query Parameter.Value --output text --region "$AWS_REGION")"
SUBNET_2="$(aws ssm get-parameter --name /devops/private-subnet-2 --query Parameter.Value --output text --region "$AWS_REGION")"
SUBNET_3="$(aws ssm get-parameter --name /devops/private-subnet-3 --query Parameter.Value --output text --region "$AWS_REGION")"

if [[ -z "${SECURITY_GROUP_ID:-}" ]]; then
  echo "SECURITY_GROUP_ID is required (migrate task security group)" >&2
  exit 1
fi

REGISTER_OUTPUT="$(MIGRATE_CMD="$MIGRATE_CMD" \
  AWS_REGION="$AWS_REGION" \
  TASK_DEFINITION="$TASK_DEFINITION" \
  CONTAINER_NAME="$CONTAINER_NAME" \
  IMAGE="$IMAGE" \
  python3 - <<'PY'
import json
import os
import subprocess
import sys
import tempfile

region = os.environ["AWS_REGION"]
family = os.environ["TASK_DEFINITION"]
container_name = os.environ["CONTAINER_NAME"]
image = os.environ["IMAGE"]

describe = subprocess.run(
    [
        "aws", "ecs", "describe-task-definition",
        "--region", region,
        "--task-definition", family,
        "--query", "taskDefinition",
        "--output", "json",
    ],
    capture_output=True,
    text=True,
    check=True,
)
task_def = json.loads(describe.stdout)

for key in (
    "taskDefinitionArn",
    "revision",
    "status",
    "requiresAttributes",
    "compatibilities",
    "registeredAt",
    "registeredBy",
):
    task_def.pop(key, None)

updated = False
for container in task_def.get("containerDefinitions", []):
    if container.get("name") == container_name:
        container["image"] = image
        updated = True
        break

if not updated:
    print(f"Container {container_name!r} not found in task definition {family!r}", file=sys.stderr)
    sys.exit(1)

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
    json.dump(task_def, fh)
    path = fh.name

try:
    register = subprocess.run(
        [
            "aws", "ecs", "register-task-definition",
            "--region", region,
            "--cli-input-json", f"file://{path}",
            "--output", "json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
finally:
    os.unlink(path)

task_def = json.loads(register.stdout)["taskDefinition"]
print(f"{task_def['family']}:{task_def['revision']}")
PY
)"

TASK_DEFINITION_ARN="$(printf '%s' "$REGISTER_OUTPUT" | tail -n 1 | tr -d '"')"
echo "Registered migration task definition: ${TASK_DEFINITION_ARN}"

OVERRIDES="$(MIGRATE_CMD="$MIGRATE_CMD" CONTAINER_NAME="$CONTAINER_NAME" python3 - <<'PY'
import json
import os

print(json.dumps({
    "containerOverrides": [{
        "name": os.environ["CONTAINER_NAME"],
        "command": ["/bin/sh", "-c", os.environ["MIGRATE_CMD"]],
    }]
}))
PY
)"

echo "Running migration task on cluster=${CLUSTER} task_definition=${TASK_DEFINITION_ARN}"
TASK_ARN="$(aws ecs run-task \
  --region "$AWS_REGION" \
  --cluster "$CLUSTER" \
  --task-definition "$TASK_DEFINITION_ARN" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2,$SUBNET_3],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=DISABLED}" \
  --overrides "$OVERRIDES" \
  --query 'tasks[0].taskArn' \
  --output text)"

if [[ -z "$TASK_ARN" || "$TASK_ARN" == "None" ]]; then
  echo "Failed to start migration ECS task" >&2
  exit 1
fi

echo "Migration task started: $TASK_ARN"
aws ecs wait tasks-stopped --region "$AWS_REGION" --cluster "$CLUSTER" --tasks "$TASK_ARN"

EXIT_CODE="$(aws ecs describe-tasks \
  --region "$AWS_REGION" \
  --cluster "$CLUSTER" \
  --tasks "$TASK_ARN" \
  --query 'tasks[0].containers[0].exitCode' \
  --output text)"

STOP_REASON="$(aws ecs describe-tasks \
  --region "$AWS_REGION" \
  --cluster "$CLUSTER" \
  --tasks "$TASK_ARN" \
  --query 'tasks[0].stoppedReason' \
  --output text)"

if [[ "$EXIT_CODE" != "0" ]]; then
  echo "Migration task failed (exitCode=${EXIT_CODE}, stoppedReason=${STOP_REASON})" >&2
  exit 1
fi

echo "Migration task completed successfully"
