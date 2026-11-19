import json, subprocess, sys, time
# Usage: nova-doc-share.py <docx token> [requester open_id]. Owner gets full access, the group view.
tok = sys.argv[1]
OWNER = "ou_51ce6f46d54cf00324117fffed05336d"
GROUP = "oc_b4c24ca571ae15b76c0b2dfeb18604b3"
members = [("openid", OWNER, "full_access", "user"), ("openchat", GROUP, "view", "chat")]
if len(sys.argv) > 2 and sys.argv[2] != OWNER:
    members.insert(0, ("openid", sys.argv[2], "full_access", "user"))
for mt, mid, perm, typ in members:
    body = json.dumps({"member_type": mt, "member_id": mid, "perm": perm})
    for i in range(6):
        p = subprocess.run(["lark-cli", "--profile", "super-nova", "--as", "bot", "api", "POST",
            f"/open-apis/drive/v1/permissions/{tok}/members",
            "--params", '{"type":"docx","need_notification":false}', "--data", body], capture_output=True, text=True, timeout=60)
        try:
            r = p.stdout; out = json.JSONDecoder().raw_decode(r[r.index("{"):])[0]
        except Exception:
            out = {"raw": p.stdout[:300] + p.stderr[:300]}
        if out.get("code") == 0 or out.get("ok") is True:
            print("OK", mid, perm, flush=True)
            break
        print("try", i + 1, mid, json.dumps(out)[:300], flush=True)
        time.sleep(3)
