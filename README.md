# Delta Agent Gatekeeper

A small Flask prototype that demonstrates how an airline could control requests made by a customer's third-party AI agent.

## Features
- Register an agent against a customer.
- Revoke an agent and save the revocation timestamp.
- Evaluate `view_fares`, `book`, `change`, and `refund` requests.
- Return `ALLOW`, `ASK CUSTOMER`, or `BLOCK` with a rule number and reason.
- Save every evaluated request to `data/audit_log.json`.
- Run six built-in demonstration tests.

## Rules
- R1: Unknown/unregistered agents are blocked.
- R2: Revoked agents are always blocked.
- R3: An agent cannot act for a different customer.
- R4: Registered active agents may view fares (read-only).
- R5: Bookings up to USD 500 are allowed.
- R6: Bookings above USD 500 require customer confirmation.
- R7: Flight changes and refunds require customer confirmation.

The USD 500 threshold is a prototype risk-control choice: it allows low-value bookings while asking the customer to approve larger financial commitments. It is not a statement of Delta's actual policy.

## Run on Windows
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
$env:ENROLLMENT_NUMBER="YOUR_ENROLMENT_NUMBER"
python app.py
```
Open http://127.0.0.1:5000

If you do not set `ENROLLMENT_NUMBER`, the dashboard displays a placeholder. Replace it with your actual number before taking submission screenshots.

## Important
This is an educational prototype only. It does not connect to Delta systems, access real passenger data, issue tickets, or process payments. The rules are the student's proposed model, not Delta's official operating policy.
