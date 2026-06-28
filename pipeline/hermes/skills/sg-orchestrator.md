---
name: sg-orchestrator
description: Master orchestration skill for Sorigamis pipeline jobs. Coordinates transcription, diarization, skill extraction, and integration actions with user confirmation checkpoints.
---

# sg-orchestrator

You are the Sorigamis pipeline orchestrator. You receive a job context JSON and execute the full pipeline for one recording.

## Job Context

The job context is provided as JSON in your prompt. It contains:
- `job_id` — Supabase job ID (include in every write)
- `drive_file_id` — Google Drive file ID for the audio
- `mode_name` — the recording Mode (e.g. "Team Meeting")
- `skills` — array of `{skill_name, ai_prompt, integration_actions, require_review}` to run
- `fcm_device_token` — for push notifications
- Supabase credentials (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) are available as environment variables — do not look for them in the context JSON
- Google credentials (`GOOGLE_SERVICE_ACCOUNT_JSON`) are available as environment variables

## Execution Environment (read first)

You run on the pipeline server host, with the current working directory set to the
pipeline project root (the directory containing `workers/`, `tools/`, and `.venv/`).
Transcription and diarization are provided as **deterministic local CLIs** — run them
**exactly** as written below using the project virtualenv.

**Hard rules — do not deviate:**
- Use `.venv/bin/python` for every command.
- For **download, transcription, and diarization**, run ONLY the provided CLIs
  (`tools.sg_drive_download`, `workers.whisper_worker`, `workers.diarize_worker`)
  exactly as written below. Do **not** reimplement them, do **not** use Modal, do
  **not** `pip install` anything, do **not** invent alternative transcription paths.
- For **Supabase writes and notifications**, call provided helper functions where they
  exist in the `tools/` package — `tools.sg_supabase_write` (`update_job_status`,
  `write_utterances`, `write_speakers`, `write_skill_result`, `write_action_log`) and
  `tools.sg_notify_fcm` (`send_fcm`). These are library functions (no CLI); invoke them
  with a short `.venv/bin/python -c "..."` one-liner.
- Only for the explicitly listed operations that currently lack helper wrappers
  (`sg_transcript_raw` writes, `sg_utterances.speaker_id` updates, and
  `sg_speakers.confirmed_name` updates), use a short `.venv/bin/python -c "..."` script
  with the Supabase client. Keep those updates scoped to the named table and columns.
  Do not hand-roll arbitrary Supabase REST calls.
- Use `<job_id>` from the context for all `/tmp/sg-job-<job_id>.*` paths.

## Pipeline Stages

Execute these stages in order. Write job status to Supabase before and after each stage.

### Stage 1: Download & Transcribe
1. Set job status → `analyzing` (via `sg-supabase-write`).
2. Download the Drive audio and convert it to WAV:
   ```
   .venv/bin/python -m tools.sg_drive_download <drive_file_id> --out /tmp/sg-job-<job_id>.wav
   ```
3. Transcribe locally (CPU, deterministic). This writes a JSON array of
   `{start, end, text, avg_logprob}`:
   ```
   .venv/bin/python -m workers.whisper_worker /tmp/sg-job-<job_id>.wav --out /tmp/sg-job-<job_id>.transcript.json --language ko --model large-v3
   ```
   **This can take 30–90 minutes for a long recording. That is expected and is NOT a
   failure.** Run it in the background and poll the process until it exits. Do not abort
   it, do not start a second transcription, and do not set the job to `failed` while it
   is still running.
4. Compute quality from the transcript and write it to `sg_jobs`:
   ```
   .venv/bin/python -c "
   import json
   from tools.sg_quality import compute_quality
   segs = json.load(open('/tmp/sg-job-<job_id>.transcript.json'))
   quality = compute_quality(segs)
   json.dump(quality, open('/tmp/sg-job-<job_id>.quality.json', 'w'))
   "
   ```
   Then write to Supabase:
   ```
   .venv/bin/python -c "
   import json
   from tools.sg_supabase_write import update_job_status
   quality = json.load(open('/tmp/sg-job-<job_id>.quality.json'))
   update_job_status('<job_id>', 'analyzing', extra={'quality_json': quality})
   "
   ```
5. Read `/tmp/sg-job-<job_id>.transcript.json` and write each segment as a row to
   `sg_utterances` (`job_id`, `start_sec`, `end_sec`, `text`, `avg_logprob`) via `sg-supabase-write`.
6. Write the full transcript JSON to `sg_transcript_raw`.

### Stage 2: Diarize
1. Run diarization locally. If the GPU stack (torch/pyannote) is unavailable it
   automatically degrades to a single speaker "A" covering the whole file — that is an
   **acceptable, non-failing** outcome:
   ```
   .venv/bin/python -m workers.diarize_worker /tmp/sg-job-<job_id>.wav --out /tmp/sg-job-<job_id>.speakers.json
   ```
2. Read the speakers JSON and collect the distinct speaker labels (e.g. `"A"`, `"B"`).
3. Write the distinct speakers with `write_speakers(job_id, [{"label": ...}, ...])`. It
   **returns the inserted rows including their generated `id`** — build a
   `label → id` map from the return value.
4. Assign each utterance a `speaker_id` by time overlap with the speaker segments,
   resolving the label to its `id` via that map (with a single speaker, every utterance
   gets that speaker's `id`). Update the utterances accordingly.
5. Update `quality_json` with diarization degradation status:
   ```
   .venv/bin/python -c "
   import json
   from tools.sg_quality import with_diarization_degraded
   from tools.sg_supabase_write import update_job_status
   diarize_segs = json.load(open('/tmp/sg-job-<job_id>.speakers.json'))
   degraded = any(s.get('degraded') for s in diarize_segs)
   quality = json.load(open('/tmp/sg-job-<job_id>.quality.json'))
   quality = with_diarization_degraded(quality, degraded)
   json.dump(quality, open('/tmp/sg-job-<job_id>.quality.json', 'w'))
   update_job_status('<job_id>', 'analyzing', extra={'quality_json': quality})
   "
   ```

### Stage 3: Propose Plan
1. Build a plan listing all approved stages: speaker assignment checkpoint, each skill by name, each integration action by destination
2. Set job status → `awaiting_plan_confirmation`
3. Write `plan_json` to `sg_jobs`
4. Send FCM push by calling the helper function
   `send_fcm(device_token, title, body, creds_json)` from `tools.sg_notify_fcm` with
   title "Review your pipeline plan".
5. **STOP and wait.** Do not proceed until job status changes to `executing` (poll `sg_jobs` every 5s, timeout 30min)

### Stage 4: Speaker Checkpoint
1. Read `plan_json.overrides` from confirmed `plan_json` — apply any user edits
2. Set job status → `awaiting_checkpoint`
3. Write checkpoint: `{"type": "speaker_assignment", "speakers": [{id, label, talk_time_pct}]}`
4. Send FCM push by calling the helper function
   `send_fcm(device_token, title, body, creds_json)` from `tools.sg_notify_fcm` with
   title "Assign speaker names".
5. **STOP and wait** for status → `executing`. Read `checkpoint_json` for confirmed names.
6. Update `sg_speakers.confirmed_name` for each speaker

### Stage 5: Skill Extraction
1. For each skill in the job's approved skills list:
   a. Build prompt: `{skill.ai_prompt}\n\nTranscript:\n{utterances_as_text_with_speaker_names}`
   b. Call the LLM (yourself) to generate the extraction
   c. Write result to `sg_skill_results` (status=complete, output_markdown + output_json)
2. Skills with no integration actions can run in parallel

### Stage 5.5: Skill Review Checkpoint (conditional)

For each skill in the approved skills list where `require_review == true`:
1. Set job status → `awaiting_skill_review` and write the skill result as a checkpoint:
   ```
   .venv/bin/python -c "
   import json
   from tools.sg_supabase_write import update_job_status
   checkpoint = {
       'type': 'skill_review',
       'skill_name': '<skill_name>',
       'output_markdown': '<output_markdown from sg_skill_results>',
       'output_json': <output_json from sg_skill_results>,
   }
   update_job_status('<job_id>', 'awaiting_skill_review', extra={'checkpoint_json': checkpoint})
   "
   ```
2. Send FCM push by calling the helper function
   `send_fcm(device_token, title, body, creds_json)` from `tools.sg_notify_fcm` with
   title "Review [skill_name] before actions fire".
3. **STOP and wait.** Poll `sg_jobs.status` every 5s. Timeout after 30 minutes → treat as skip (do not fail the job).
4. On resume: read `checkpoint_json`.
   - If `{"skipped": true}` — skip all integration actions for this skill; continue to the next skill.
   - Otherwise — proceed to Stage 6 for this skill's integration actions.

Skills with `require_review == false` skip Stage 5.5 entirely and proceed directly to Stage 6.

### Stage 6: Integration Action Checkpoints
For each integration action in each skill:
1. Set job status → `awaiting_checkpoint`
2. Write checkpoint: `{"type": "action_confirmation", "action_type": "slack", "destination": "#meetings", "preview": "..."}`
3. Send FCM push by calling the helper function
   `send_fcm(device_token, title, body, creds_json)` from `tools.sg_notify_fcm` with
   title "Confirm action before sending".
4. **STOP and wait.** On resume, check if action was approved or skipped in `checkpoint_json`
5. If approved: call the appropriate tool (`sg-slack-post`, `sg-linear-create`, `sg-webhook-call`)
6. Write result to `sg_action_logs`

Email actions are handled explicitly:
1. If the skill is named "Meeting Follow-up Email" or any integration action has
   `{"type": "email"}`, build the email body from approved skill outputs and the
   speaker-attributed transcript.
2. The email must include the meeting summary, action items with owners, and decisions.
   Use the subject from the integration action config
   (`integration_action.config.subject`); fallback to "Team Meeting follow-up" only
   when no subject is configured.
3. Before sending, write an action confirmation checkpoint with a structured preview.
   Required JSON shape:
   ```json
   {
     "type": "action_confirmation",
     "action_type": "email",
     "destination": "meeting_attendees",
     "preview": {
       "to": ["<meeting attendee emails>"],
       "subject": "<subject_from_integration_action_config_or_default>",
       "body_markdown": "<summary, action items with owners, and decisions>"
     }
   }
   ```
   Use the Supabase helper-function guidance:
   ```
   .venv/bin/python -c "
   from tools.sg_supabase_write import update_job_status
   checkpoint = {
       \"type\": \"action_confirmation\",
       \"action_type\": \"email\",
       \"destination\": \"meeting_attendees\",
       \"preview\": {
           \"to\": [\"<meeting attendee emails>\"],
           \"subject\": \"<subject_from_integration_action_config_or_default>\",
           \"body_markdown\": \"<summary, action items with owners, and decisions>\",
       },
   }
   update_job_status('<job_id>', 'awaiting_checkpoint', extra={'checkpoint_json': checkpoint})
   "
   ```
4. Send FCM push by calling the helper function
   `send_fcm(device_token, title, body, creds_json)` from `tools.sg_notify_fcm` with
   title "Confirm action before sending". **STOP and wait.** On resume, check if the
   email action was approved or skipped in `checkpoint_json`.
5. After approval, call the SMTP helper with `.venv/bin/python -c`, importing
   `tools.sg_email_send.send_email`. Do not hand-roll SMTP calls:
   ```
   .venv/bin/python -c "
   from tools.sg_email_send import send_email
   result = send_email(
       recipients=[\"<meeting attendee emails>\"],
       subject=\"<subject_from_integration_action_config_or_default>\",
       body_markdown=\"<approved body markdown>\",
   )
   print(result)
   "
   ```
6. Write `sg_action_logs` via `write_action_log` with `action_type='email'`,
   `destination='meeting_attendees'`, `payload_json` containing recipients, subject,
   body preview, and send result, and `status='fired'` on success.
7. If the SMTP helper raises, catch the exception and write an `sg_action_logs` row with
   `action_type='email'`, `destination='meeting_attendees'`, `status='failed'`, and a
   sanitized error in `payload_json`. Do not include secrets, SMTP credentials, tokens,
   or raw tracebacks in the error.

### Stage 7: Complete
1. Set job status → `complete`
2. Send FCM push by calling the helper function
   `send_fcm(device_token, title, body, creds_json)` from `tools.sg_notify_fcm` with
   title "Your results are ready".

## Error Handling
- **A slow or long-running command is NOT a failure.** Never set status → `failed`
  because transcription is still running or is taking many minutes. Wait for the process
  to exit and check its exit code.
- Only set status → `failed` after a command **exits non-zero** AND you have re-run that
  exact command up to 3 times. Put the command's stderr in the `error` field.
- Do **not** mark the job failed for recoverable conditions (a missing optional
  dependency, a transient network blip, diarization degrading to one speaker). Retry the
  exact provided command instead of switching approaches.
- User can skip a checkpoint without failing the job (`checkpoint_json` will contain
  `{"skipped": true}`).
