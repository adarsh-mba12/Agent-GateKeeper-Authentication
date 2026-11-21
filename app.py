import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-for-local-demo")
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
AGENTS_FILE = DATA_DIR / "agents.json"
AUDIT_FILE = DATA_DIR / "audit_log.json"
ENROLLMENT_NUMBER = os.environ.get("ENROLLMENT_NUMBER", "ENTER YOUR ENROLMENT NUMBER")
TZ = ZoneInfo("Asia/Kolkata")

ACTIONS = {
    "view_fares": "View Fares",
    "book": "Book Flight",
    "change": "Change Flight",
    "refund": "Refund",
}

RULES = {
    "R1": "Unknown or unregistered agent is blocked.",
    "R2": "A revoked agent is always blocked.",
    "R3": "An agent cannot act for a different customer.",
    "R4": "A registered active agent may view fares (read-only).",
    "R5": "A registered active agent may book a flight costing up to $500.",
    "R6": "A flight booking above $500 requires customer confirmation.",
    "R7": "Change and refund requests always require customer confirmation.",
}

def now_text():
    return datetime.now(TZ).isoformat(timespec="seconds")

def ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not AGENTS_FILE.exists():
        AGENTS_FILE.write_text("[]", encoding="utf-8")
    if not AUDIT_FILE.exists():
        AUDIT_FILE.write_text("[]", encoding="utf-8")

def read_json(path):
    ensure_files()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

def write_json(path, data):
    ensure_files()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def add_audit(customer, agent_name, action, amount, decision, rule, reason):
    logs = read_json(AUDIT_FILE)
    logs.insert(0, {
        "date_time": now_text(),
        "customer": customer,
        "agent": agent_name,
        "action": ACTIONS.get(action, action),
        "amount": float(amount or 0),
        "decision": decision,
        "rule": rule,
        "reason": reason,
    })
    write_json(AUDIT_FILE, logs)

def evaluate(customer, agent_name, action, amount):
    agents = read_json(AGENTS_FILE)
    agent = next((a for a in agents if a["name"].casefold() == agent_name.casefold()), None)

    if agent is None:
        return "BLOCK", "R1", RULES["R1"]
    if agent["status"] == "REVOKED":
        return "BLOCK", "R2", RULES["R2"]
    if agent["customer"].casefold() != customer.casefold():
        return "BLOCK", "R3", RULES["R3"]
    if action == "view_fares":
        return "ALLOW", "R4", RULES["R4"]
    if action == "book":
        if float(amount or 0) <= 0:
            return "BLOCK", "R5", "Flight amount must be greater than zero."
        if float(amount) <= 500:
            return "ALLOW", "R5", RULES["R5"]
        return "ASK CUSTOMER", "R6", RULES["R6"]
    if action in ("change", "refund"):
        return "ASK CUSTOMER", "R7", RULES["R7"]
    return "BLOCK", "R1", "Unsupported action."

def register_agent(customer, name):
    agents = read_json(AGENTS_FILE)
    if any(a["name"].casefold() == name.casefold() for a in agents):
        return False, "An agent with this name already exists."
    agents.append({
        "id": f"AG-{len(agents)+1:04d}",
        "customer": customer,
        "name": name,
        "status": "ACTIVE",
        "registered_at": now_text(),
        "revoked_at": None,
    })
    write_json(AGENTS_FILE, agents)
    return True, "Agent registered successfully."

@app.route("/", methods=["GET"])
def index():
    agents = read_json(AGENTS_FILE)
    logs = read_json(AUDIT_FILE)[:12]
    test_results = read_json(DATA_DIR / "last_test_results.json")
    return render_template(
        "index.html",
        agents=agents,
        logs=logs,
        test_results=test_results,
        actions=ACTIONS,
        rules=RULES,
        enrollment=ENROLLMENT_NUMBER,
    )

@app.route("/register", methods=["POST"])
def register():
    customer = request.form.get("customer", "").strip()
    name = request.form.get("agent_name", "").strip()
    if not customer or not name:
        flash("Enter both customer name and agent name.", "error")
    else:
        ok, message = register_agent(customer, name)
        flash(message, "success" if ok else "error")
    return redirect(url_for("index"))

@app.route("/revoke/<agent_id>", methods=["POST"])
def revoke(agent_id):
    agents = read_json(AGENTS_FILE)
    found = False
    for agent in agents:
        if agent["id"] == agent_id:
            found = True
            if agent["status"] == "ACTIVE":
                agent["status"] = "REVOKED"
                agent["revoked_at"] = now_text()
                write_json(AGENTS_FILE, agents)
                flash(f'{agent["name"]} revoked. Revocation time saved.', "success")
            else:
                flash("This agent is already revoked.", "error")
            break
    if not found:
        flash("Agent not found.", "error")
    return redirect(url_for("index"))

@app.route("/decide", methods=["POST"])
def decide():
    customer = request.form.get("customer", "").strip()
    agent_name = request.form.get("agent_name", "").strip()
    action = request.form.get("action", "")
    try:
        amount = float(request.form.get("amount", "0") or 0)
    except ValueError:
        amount = -1
    if not customer or not agent_name or action not in ACTIONS or amount < 0:
        flash("Enter valid request details.", "error")
        return redirect(url_for("index"))
    decision, rule, reason = evaluate(customer, agent_name, action, amount)
    add_audit(customer, agent_name, action, amount, decision, rule, reason)
    flash(f"{decision} — {rule}: {reason}", "decision")
    return redirect(url_for("index"))

@app.route("/run-demo-tests", methods=["POST"])
def run_demo_tests():
    agents = read_json(AGENTS_FILE)
    # Use fixed demo identities so tests are repeatable; do not overwrite a user's own agents.
    for name, status in [("DemoAgent", "ACTIVE"), ("RevokedDemoAgent", "REVOKED")]:
        if not any(a["name"].casefold() == name.casefold() for a in agents):
            agents.append({
                "id": f"DEMO-{name}",
                "customer": "Demo Customer",
                "name": name,
                "status": status,
                "registered_at": now_text(),
                "revoked_at": now_text() if status == "REVOKED" else None,
            })
    write_json(AGENTS_FILE, agents)

    tests = [
        ("Known agent views fares", "Demo Customer", "DemoAgent", "view_fares", 0, "ALLOW", "R4"),
        ("Unknown agent requests fares", "Demo Customer", "UnknownBot", "view_fares", 0, "BLOCK", "R1"),
        ("Flight booking above limit", "Demo Customer", "DemoAgent", "book", 800, "ASK CUSTOMER", "R6"),
        ("Flight booking below limit", "Demo Customer", "DemoAgent", "book", 300, "ALLOW", "R5"),
        ("Revoked agent tries to view fares", "Demo Customer", "RevokedDemoAgent", "view_fares", 0, "BLOCK", "R2"),
        ("Agent requests a flight change", "Demo Customer", "DemoAgent", "change", 0, "ASK CUSTOMER", "R7"),
    ]
    results = []
    for title, customer, agent, action, amount, expected, expected_rule in tests:
        decision, rule, reason = evaluate(customer, agent, action, amount)
        add_audit(customer, agent, action, amount, decision, rule, reason)
        results.append({
            "test": title,
            "expected": expected,
            "actual": decision,
            "expected_rule": expected_rule,
            "actual_rule": rule,
            "status": "PASS" if decision == expected and rule == expected_rule else "FAIL",
        })
    write_json(BASE_DIR / "data" / "last_test_results.json", results)
    flash("Six demo tests completed. Results are shown below.", "success")
    return redirect(url_for("index") + "#tests")

if __name__ == "__main__":
    ensure_files()
    app.run(debug=True)
