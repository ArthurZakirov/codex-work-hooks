# Assess the requested work

Assess the supplied JSON without executing the request. Use the following steps in order.

## 1. Identify the request

Read the current submission together with any pending request. A clarification supplements the pending request. If the submission clearly replaces it, assess the new task independently.

## 2. Classify the work

Choose one classification according to who benefits and what the requester wants done.

| Classification | When to use it |
| --- | --- |
| `criteria_only` | The current message supplies acceptance criteria as context without asking to perform work. If it also asks for implementation, classify and score the requested work against the newly supplied criteria. |
| `explanation` | The user asks only to understand existing code or behavior. Allow the main chat to explain using its existing context. For a mixed explanation and change request, assess the change. |
| `personal` | The work serves the requester’s own learning, devices, or hobby tools. |
| `exception` | The requester is reviewing a colleague’s PR or offering roughly five minutes of colleague assistance. Treat substantial implementation inside a review as professional work. |
| `professional` | The work serves a team deliverable, or the requester explicitly asks to simulate professional work. |
| `unclear` | The beneficiary remains ambiguous. Ask who commissioned the work. |

Jira, Slack, and programming languages are clues. Use the request itself to establish the beneficiary.

## 3. Score professional work

Assess the whole requested scope against the supplied acceptance criteria. Choose a score according to the evidence.

| Score | Evidence | What to tell the requester |
| --- | --- | --- |
| 8–10 | Explicit requirement or demonstrated prerequisite, including a concrete reviewer or repository requirement | Name the criterion and explain why the work is necessary. |
| 4–7 | Plausible connection with an unproven dependency | Ask what makes the work necessary. |
| 1–3 | Unrelated work or a justification based only on general usefulness | Suggest a separate work item for team discussion. |

## 4. Return the assessment

Return one JSON object with these fields.

| Field | Value |
| --- | --- |
| `kind` | The classification from step 2. |
| `criteria` | Copy each newly supplied acceptance criterion verbatim from this submission. Use an empty array when none are supplied. A desired implementation or a proposal for extra work does not itself establish acceptance criteria. |
| `replacement` | Boolean indicating whether the new submission clearly replaces the pending request. |
| `score` | Integer from 1 to 10. For professional work, apply step 3. |
| `reason` | A brief explanation addressed to the requester. |
