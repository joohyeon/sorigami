import os
import sys
import time
import argparse
import json
from uuid import uuid4
import httpx
from supabase import create_client, Client

def load_dotenv(filepath: str):
    """Simple parser to load a local .env file into os.environ."""
    if not os.path.exists(filepath):
        print(f"Warning: env file '{filepath}' not found. Relying on system environment variables.")
        return
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                # Strip spaces and optional quotes
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                os.environ[key] = val

def main():
    parser = argparse.ArgumentParser(description="Sorigamis Pipeline Team Meeting E2E Test Runner")
    parser.add_argument("--file-id", required=True, help="Google Drive Audio File ID")
    parser.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
    parser.add_argument("--server-url", default="http://localhost:8080", help="FastAPI Server URL")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv(args.env_file)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in your environment or .env file.")
        sys.exit(1)

    print(f"Connecting to Supabase at {supabase_url}...")
    supabase: Client = create_client(supabase_url, supabase_key)

    # 1. Fetch or create a user in Supabase auth to map our tables to
    print("Fetching active users from Supabase...")
    user_id = None
    try:
        users = supabase.auth.admin.list_users()
        if users and len(users) > 0:
            user_id = users[0].id
            print(f"Found active user: {user_id}")
    except Exception as exc:
        print(f"Warning: Could not list users via admin API: {exc}")

    if not user_id:
        print("No users found in auth.users. Attempting to create a test user...")
        try:
            new_user = supabase.auth.admin.create_user({
                "email": f"test-{uuid4()}@example.com",
                "password": "super-secret-password-123",
                "email_confirm": True
            })
            user_id = new_user.user.id
            print(f"Successfully created test user: {user_id}")
        except Exception as exc:
            print(f"Failed to create test user: {exc}")
            sys.exit(1)

    # 2. Seed Team Meeting mode and associated skills
    print("Seeding/verifying skills in Supabase...")
    skills_to_seed = [
        {
            "name": "Meeting Summary",
            "description": "Concise summary of the meeting",
            "ai_prompt": "Summarize the transcript into a clear, concise paragraph covering the main topics discussed.",
            "is_default": True
        },
        {
            "name": "Action Items",
            "description": "Extract tasks and owners",
            "ai_prompt": "Extract all action items from the transcript. For each item return: text (the task), owner (speaker name if mentioned, else null). Return as JSON array: [{\"text\":\"...\",\"owner\":\"...\"}]",
            "is_default": True
        },
        {
            "name": "Decision Log",
            "description": "Key decisions made",
            "ai_prompt": "List all decisions made during the conversation. Return as a JSON array of strings: [\"Decision 1\",\"Decision 2\"]",
            "is_default": True
        }
    ]

    skill_ids = []
    for s in skills_to_seed:
        # Check if skill exists
        exist = supabase.table("sg_skills").select("id").eq("name", s["name"]).execute()
        if exist.data:
            sid = exist.data[0]["id"]
            print(f"Skill '{s['name']}' already exists (ID: {sid})")
            skill_ids.append(sid)
        else:
            res = supabase.table("sg_skills").insert({
                "name": s["name"],
                "description": s["description"],
                "ai_prompt": s["ai_prompt"],
                "is_default": s["is_default"]
            }).execute()
            sid = res.data[0]["id"]
            print(f"Seeded skill '{s['name']}' (ID: {sid})")
            skill_ids.append(sid)

    print("Seeding/verifying 'Team Meeting' mode...")
    mode_id = None
    mode_exist = supabase.table("sg_modes").select("id").eq("name", "Team Meeting").execute()
    if mode_exist.data:
        mode_id = mode_exist.data[0]["id"]
        print(f"Mode 'Team Meeting' already exists (ID: {mode_id}). Updating skill associations...")
        supabase.table("sg_modes").update({
            "skill_ids": skill_ids
        }).eq("id", mode_id).execute()
    else:
        res = supabase.table("sg_modes").insert({
            "name": "Team Meeting",
            "user_id": user_id,
            "skill_ids": skill_ids
        }).execute()
        mode_id = res.data[0]["id"]
        print(f"Seeded Mode 'Team Meeting' (ID: {mode_id})")

    # 3. Submit job request to FastAPI
    payload = {
        "drive_file_id": args.file_id,
        "mode_id": mode_id,
        "user_id": user_id
    }
    print(f"\nSubmitting job to {args.server_url}/jobs...")
    try:
        resp = httpx.post(f"{args.server_url}/jobs", json=payload, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Failed to submit job to server: {exc}")
        print("Please make sure your FastAPI server is running locally (e.g. uvicorn main:app --port 8080)")
        sys.exit(1)

    job_data = resp.json()
    job_id = job_data["job_id"]
    print(f"Job submitted successfully! Job ID: {job_id}")

    # 4. Poll job and respond to checkpoints
    print("\nStarting E2E Job Polling loop...")
    while True:
        job_info_resp = httpx.get(f"{args.server_url}/jobs/{job_id}")
        job_info = job_info_resp.json()
        status = job_info["status"]
        print(f"[{time.strftime('%H:%M:%S')}] Job Status: {status}")

        if status == "complete":
            print("\n🎉 Job completed successfully!")
            break
        elif status == "failed":
            print(f"\n❌ Job failed! Error: {job_info.get('error')}")
            sys.exit(1)
        elif status == "awaiting_plan_confirmation":
            print("Action Required: Plan confirmation received.")
            plan = job_info.get("plan")
            print(f"Proposed Plan: {json.dumps(plan, indent=2, ensure_ascii=False)}")
            
            # Approve all steps
            approved_steps = plan.get("approved_steps", []) if plan else []
            # Fallback to approve the 3 seeded skills + speaker alignment if empty
            if not approved_steps:
                approved_steps = ["speaker_assignment", "Meeting Summary", "Action Items", "Decision Log"]
            
            print(f"Confirming/approving steps: {approved_steps}")
            confirm_resp = httpx.post(
                f"{args.server_url}/jobs/{job_id}/confirm",
                json={"approved_steps": approved_steps, "per_step_overrides": {}}
            )
            confirm_resp.raise_for_status()
            print("Plan confirmation submitted.")
        elif status == "awaiting_checkpoint":
            checkpoint = job_info.get("checkpoint")
            print(f"Action Required: Checkpoint encountered: {checkpoint}")
            
            if checkpoint and checkpoint.get("type") == "speaker_assignment":
                # Auto-assign detected speakers
                detected_speakers = checkpoint.get("speakers", [])
                confirmed_speakers = []
                for idx, spk in enumerate(detected_speakers):
                    spk_id = spk.get("id")
                    spk_label = spk.get("label", f"Speaker {idx+1}")
                    # Give them mock names
                    mock_name = f"Participant {spk_label}"
                    if idx == 0:
                        mock_name = "Alice"
                    elif idx == 1:
                        mock_name = "Bob"
                    confirmed_speakers.append({"id": spk_id, "confirmed_name": mock_name})
                
                print(f"Submitting speaker assignment checkpoint: {confirmed_speakers}")
                chk_resp = httpx.post(
                    f"{args.server_url}/jobs/{job_id}/checkpoint",
                    json={"data": {"speakers": confirmed_speakers}}
                )
                chk_resp.raise_for_status()
                print("Speaker checkpoint submitted.")
            else:
                # Other checkpoints (e.g. integration actions), approve them automatically
                print("Submitting general checkpoint confirmation...")
                chk_resp = httpx.post(
                    f"{args.server_url}/jobs/{job_id}/checkpoint",
                    json={"data": {"approved": True}}
                )
                chk_resp.raise_for_status()
                print("Checkpoint confirmation submitted.")

        time.sleep(5)

    # 5. Fetch and print final results
    print("\nFetching job results...")
    results_resp = httpx.get(f"{args.server_url}/jobs/{job_id}/results")
    results = results_resp.json()

    print("\n================== MEETING SUMMARY ==================")
    summaries = [r for r in results.get("skill_results", []) if r["skill_name"] == "Meeting Summary"]
    if summaries:
        print(summaries[0].get("output_markdown"))
    else:
        print("No Summary result found.")

    print("\n================== ACTION ITEMS ==================")
    actions = [r for r in results.get("skill_results", []) if r["skill_name"] == "Action Items"]
    if actions:
        out_json = actions[0].get("output_json") or []
        for idx, act in enumerate(out_json):
            print(f"{idx+1}. {act.get('text')} (Owner: {act.get('owner')})")
    else:
        print("No Action Items result found.")

    print("\n================== DECISION LOG ==================")
    decisions = [r for r in results.get("skill_results", []) if r["skill_name"] == "Decision Log"]
    if decisions:
        out_json = decisions[0].get("output_json") or []
        for idx, dec in enumerate(out_json):
            print(f"- {dec}")
    else:
        print("No Decision Log result found.")
    print("==================================================")

if __name__ == "__main__":
    main()
