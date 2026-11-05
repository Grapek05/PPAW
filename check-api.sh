#!/usr/bin/env bash

API_URL="${API_URL:-http://127.0.0.1:8000}"
API_URL="${API_URL%/}"
CHECK_COUNT=0
FAIL_COUNT=0
LAST_LOCATION=""
PROJECT_ID=""
TASK_ID=""
SECOND_TASK_ID=""
RUN_ID="$$-${RANDOM}"

cleanup() {
  if [[ -n "$TASK_ID" ]]; then
    curl -s -o /dev/null -X DELETE "$API_URL/tasks/$TASK_ID" || true
  fi
  if [[ -n "$SECOND_TASK_ID" ]]; then
    curl -s -o /dev/null -X DELETE "$API_URL/tasks/$SECOND_TASK_ID" || true
  fi
  if [[ -n "$PROJECT_ID" ]]; then
    curl -s -o /dev/null -X DELETE "$API_URL/projects/$PROJECT_ID" || true
  fi
}
trap cleanup EXIT

check() {
  local expected="$1"
  local method="$2"
  local path="$3"
  local body="${4:-}"
  local response
  local actual
  local -a curl_args=(-sS -D - -o /dev/null -w $'\n%{http_code}' -X "$method")

  if [[ -n "$body" ]]; then
    curl_args+=(-H "Content-Type: application/json" --data "$body")
  fi

  if response=$(curl "${curl_args[@]}" "$API_URL$path"); then
    actual="${response##*$'\n'}"
    LAST_LOCATION=$(printf '%s\n' "$response" | sed -n 's/^[Ll]ocation:[[:space:]]*//p' | tr -d '\r' | tail -n 1)
  else
    actual="000"
    LAST_LOCATION=""
  fi

  CHECK_COUNT=$((CHECK_COUNT + 1))
  if [[ "$actual" == "$expected" ]]; then
    printf 'OK   %s %s -> %s\n' "$method" "$path" "$actual"
    return 0
  fi

  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'BLAD %s %s -> %s (oczekiwano %s)\n' "$method" "$path" "$actual" "$expected"
  return 1
}

check 200 GET /users
check 404 GET /users/999
check 200 GET /projects
check 404 GET /projects/999
check 409 POST /projects '{"name":"TaskBoard"}'
check 200 GET /tasks
check 404 GET /tasks/999
check 422 POST /tasks '{"title":"Bez projektu"}'
check 422 POST /tasks '{"project_id":999999,"title":"Nieistniejacy projekt"}'
check 422 POST /tasks '{"project_id":1,"title":"Nieistniejacy uzytkownik","assignee_id":999999}'

project_name="contract-check-$RUN_ID"
check 201 POST /projects "{\"name\":\"$project_name\"}"
project_id="${LAST_LOCATION##*/}"
if [[ ! "$project_id" =~ ^[0-9]+$ ]]; then
  CHECK_COUNT=$((CHECK_COUNT + 1))
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'BLAD POST /projects: brak poprawnego naglowka Location\n'
else
  PROJECT_ID="$project_id"
  check 200 GET "/projects/$PROJECT_ID"
  check 200 PATCH "/projects/$PROJECT_ID" '{"description":"Test kontraktu"}'
  check 409 PATCH "/projects/$PROJECT_ID" '{"name":"TaskBoard"}'

  task_title="contract-task-$RUN_ID"
  check 201 POST /tasks "{\"project_id\":$PROJECT_ID,\"title\":\"$task_title\",\"assignee_id\":1}"
  task_id="${LAST_LOCATION##*/}"
  if [[ ! "$task_id" =~ ^[0-9]+$ ]]; then
    CHECK_COUNT=$((CHECK_COUNT + 1))
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf 'BLAD POST /tasks: brak poprawnego naglowka Location\n'
  else
    TASK_ID="$task_id"
    second_task_title="contract-second-task-$RUN_ID"
    check 201 POST /tasks "{\"project_id\":$PROJECT_ID,\"title\":\"$second_task_title\"}"
    second_task_id="${LAST_LOCATION##*/}"
    if [[ "$second_task_id" =~ ^[0-9]+$ ]]; then
      SECOND_TASK_ID="$second_task_id"
    fi

    check 200 GET "/tasks/$TASK_ID"
    check 200 GET "/tasks?project_id=$PROJECT_ID"
    check 200 GET "/tasks?assignee_id=1"
    check 200 PATCH "/tasks/$TASK_ID" "{\"title\":\"contract-updated-$RUN_ID\"}"
    check 422 PATCH "/tasks/$TASK_ID" '{"assignee_id":999999}'
    if [[ -n "$SECOND_TASK_ID" ]]; then
      check 409 PATCH "/tasks/$TASK_ID" "{\"title\":\"$second_task_title\"}"
    fi
    check 409 DELETE "/projects/$PROJECT_ID"
    check 204 DELETE "/tasks/$TASK_ID"
    check 404 GET "/tasks/$TASK_ID"
    if [[ -n "$SECOND_TASK_ID" ]]; then
      check 204 DELETE "/tasks/$SECOND_TASK_ID"
      check 404 GET "/tasks/$SECOND_TASK_ID"
    fi
  fi

  check 204 DELETE "/projects/$PROJECT_ID"
  check 404 GET "/projects/$PROJECT_ID"
fi

printf 'Podsumowanie: %s sprawdzen, %s bledow\n' "$CHECK_COUNT" "$FAIL_COUNT"
if [[ "$FAIL_COUNT" -eq 0 ]]; then
  exit 0
fi
exit 1