# 006-05 Hermes provider preflight (PROVIDER_OK)

**Why:** The source playbook (steps 5-8) assumes the pilot runs inside a Hermes session
and checks the model first. This coding agent has no Hermes session, so the check is
`NOT EXECUTABLE` here. The pipeline itself is deterministic and calls no model, but the
playbook's environment check is still open.

**Where:** Chuck's Hermes installation, using the profile that will run the pilot.
Reference: https://hermes-agent.nousresearch.com/docs/integrations/providers

**Steps:**
1. Start a fresh Hermes chat with the intended profile.
2. Send: `Reply with exactly PROVIDER_OK`.
3. Record the reply, time, and the provider/model labels (names only, never a key) in
   `build/caj-hvac-research-pilot/evidence/preflight.md` section 1.
4. If it fails, record the exact error text (with any secret removed). If the installed
   CLI supports it, run `hermes model` to check the selected provider/model, start a
   fresh session, and repeat step 2.
5. Do not move to a paid plan or a new provider without Chuck's explicit decision and a
   stated cost.
6. Update `environment.md` rows for Hermes version, profile, and model labels.

**Verify:** `evidence/preflight.md` section 1 shows the literal `PROVIDER_OK` reply from
the same profile that will run the pilot.

**Blocked by:** Access to Chuck's Hermes installation and its provider login. Provider
cost: NEEDS_EVIDENCE; approval required before any paid usage.
