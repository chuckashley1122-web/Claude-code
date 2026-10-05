# Runbook: production website widget

Covers source steps 34-35. **Human-only.** Requires the client's GoHighLevel location
and website admin access granted by the owner.

1. Create the client widget in the client location. Confirm the text agent mapping and
   the voice mapping separately; one selection does not connect both.
2. GHL-hosted site: select the widget in the site settings.
3. External site: back up the current footer / code-injection content first (record
   the backup location: `<<FILL: backup location>>`), then paste the supported embed
   snippet into the shared footer or code-injection area.
4. Avoid duplicate widgets: confirm only one widget loads on each page.
5. Test on desktop and mobile in a fresh browser session; record evidence for
   acceptance test T11.
6. Additional channels (Messenger, SMS, WhatsApp, email, social) only within the agreed
   written scope: verify support and permissions, connect the correct business
   account, select the intended agent, test reply ownership and human takeover (T06).
7. Rollback: restore the backed-up footer or remove the widget selection; reload the
   site and confirm the widget no longer loads.

Record widget ID (`GHL_WIDGET_ID`) and install timestamp in
`records/Asset_Register.csv` and `records/Build_Log.csv`.
