# Implementation Plan — Pipeline E2E Test (Team Meeting Mode)

This plan outlines how to build a test scenario to verify the `sg-pipeline` backend. The scenario simulates a user uploading a meeting recording to Google Drive and submitting it to the Hermes orchestrator using the **Team Meeting** mode.

## 1. Team Meeting Mode Configuration

Based on the codebase design, the **Team Meeting** mode (emoji: `🗓`) is configured to run the following three skills in order:
1. **Meeting Summary** (`output_type: 'summary'`): Synthesizes the speaker-attributed transcript into a paragraph describing the main topics discussed.
2. **Action Items** (`output_type: 'tasks'`): Extracts actionable items and attributes them to speaker names if identified, returning a JSON array.
3. **Decision Log** (`output_type: 'custom'`, `focus_area: 'decisions made'`): Lists all key decisions made during the conversation.

---

## 2. Prerequisites & Credentials

To run this test scenario, a local `pipeline/.env` must be created with the following variables:
* **`SUPABASE_URL`** & **`SUPABASE_SERVICE_ROLE_KEY`**: To query and write state/results to Supabase tables.
* **`GOOGLE_SERVICE_ACCOUNT_JSON`**: The raw JSON string of a service account key that has the Drive API enabled.
* **`HERMES_PROVIDER`** & **`HERMES_MODEL`**: To configure the LLM (e.g., `github-copilot` / `gemini-2.5-pro`).
* **Modal Tokens** (Optional, if using real GPU workers): `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`.

> [!IMPORTANT]
> The test audio file must be uploaded to Google Drive, and the file (or the folder it is in) **must be shared** with the service account email address found in the `GOOGLE_SERVICE_ACCOUNT_JSON`.

---

## 3. Proposed Changes

We will create a new Python script inside the scratch directory to orchestrate the test scenario.

### Scratch Scripts

#### [NEW] [test_team_meeting_e2e.py](file:///Users/hyeonjoo/VSCodeTestProjects/sorigamis/pipeline/scratch/test_team_meeting_e2e.py)
This script will:
1. Connect to the Supabase database.
2. Seed the **Team Meeting** mode and its three skills (`Meeting Summary`, `Action Items`, `Decision Log`) in the database if they are not already present.
3. Submit a job payload to the FastAPI `POST /jobs` endpoint with a designated `drive_file_id`.
4. Poll `GET /jobs/{id}` and act on checkpoints:
   - When status becomes `awaiting_plan_confirmation`, automatically submit approval to `/jobs/{id}/confirm`.
   - When status becomes `awaiting_checkpoint` for speaker assignment, automatically map detected speakers to confirmed names (e.g., `Speaker A` $\rightarrow$ `Alice`, `Speaker B` $\rightarrow$ `Bob`) and submit to `/jobs/{id}/checkpoint`.
5. Wait for the job status to become `complete`.
6. Query and display the generated results from the `sg_skill_results` table.

---

## 4. Option for GPU Workers: Real vs. Mocked

Depending on your environment setup, the GPU-heavy transcription and diarization steps can be run in two ways:

* **Option A: Real Modal GPU Deployment**
  You deploy the workers to Modal before running the test:
  ```bash
  modal deploy workers/whisper_worker.py
  modal deploy workers/diarize_worker.py
  ```
* **Option B: Local/Mocked Execution**
  If you do not have Modal credentials configured, we can update the test script to temporarily mock the responses of `sg-whisper-transcribe` and `sg-diarize` tools so that the Hermes session runs successfully on CPU-only.

---

## 5. Verification Plan

### Automated Steps
1. Run the local FastAPI server:
   ```bash
   cd pipeline
   uv run uvicorn main:app --reload --port 8080
   ```
2. Execute the test script:
   ```bash
   uv run python scratch/test_team_meeting_e2e.py --file-id <drive_file_id>
   ```

### Manual Verification
- Observe the server logs to verify Hermes subprocess instantiation.
- Verify status changes in the Supabase dashboard `sg_jobs` table.
- Verify final output formats printed to the console.
