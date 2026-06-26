"""Attach to an EXISTING live job and drive its checkpoints to completion.

Replaces the e2e test's poll/checkpoint loop (steps 4-5) when the original
test process has exited but the Hermes agent is still running the job.
Usage: python scratch/drive_existing_job.py <job_id> [--server-url URL]
"""
import sys
import time
import json
import argparse
import httpx


def main():
    p = argparse.ArgumentParser()
    p.add_argument("job_id")
    p.add_argument("--server-url", default="http://localhost:8080")
    args = p.parse_args()
    base = args.server_url
    jid = args.job_id

    def get_info():
        """Fetch job info, tolerating transient empty/non-JSON/network responses."""
        for _ in range(5):
            try:
                r = httpx.get(f"{base}/jobs/{jid}", timeout=30)
                return r.json()
            except Exception as exc:  # empty body, 5xx, connection blip
                print(f"  (transient poll error: {exc}; retrying)")
                time.sleep(3)
        return None

    print(f"Driving existing job {jid} at {base}")
    while True:
        info = get_info()
        if info is None:
            time.sleep(5)
            continue
        status = info["status"]
        print(f"[{time.strftime('%H:%M:%S')}] status={status} err={info.get('error')}")

        if status == "complete":
            print("\n🎉 Job completed!")
            break
        elif status == "failed":
            # Don't bail immediately — the agent has been seen to overwrite a
            # transient 'failed' back to 'analyzing'. Give it a grace window.
            print("status=failed; waiting 20s to see if the agent recovers...")
            time.sleep(20)
            recheck = get_info() or {"status": "failed"}
            if recheck["status"] == "failed":
                print(f"\n❌ Job failed (stable). Error: {recheck.get('error')}")
                sys.exit(1)
            print(f"recovered → {recheck['status']}; continuing")
            continue
        elif status == "awaiting_plan_confirmation":
            plan = info.get("plan") or {}
            approved = plan.get("approved_steps") or [
                "speaker_assignment", "Meeting Summary", "Action Items", "Decision Log",
            ]
            print(f"  → confirming plan: {approved}")
            httpx.post(f"{base}/jobs/{jid}/confirm",
                       json={"approved_steps": approved, "per_step_overrides": {}},
                       timeout=30).raise_for_status()
        elif status == "awaiting_checkpoint":
            chk = info.get("checkpoint") or {}
            if chk.get("type") == "speaker_assignment":
                names = ["Alice", "Bob"]
                confirmed = []
                for idx, spk in enumerate(chk.get("speakers", [])):
                    nm = names[idx] if idx < len(names) else f"Speaker {idx+1}"
                    confirmed.append({"id": spk.get("id"), "confirmed_name": nm})
                print(f"  → speaker assignment: {confirmed}")
                httpx.post(f"{base}/jobs/{jid}/checkpoint",
                           json={"data": {"speakers": confirmed}}, timeout=30).raise_for_status()
            else:
                print("  → generic checkpoint approve")
                httpx.post(f"{base}/jobs/{jid}/checkpoint",
                           json={"data": {"approved": True}}, timeout=30).raise_for_status()
        time.sleep(5)

    results = httpx.get(f"{base}/jobs/{jid}/results", timeout=30).json()
    print("\n==== RESULTS ====")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
