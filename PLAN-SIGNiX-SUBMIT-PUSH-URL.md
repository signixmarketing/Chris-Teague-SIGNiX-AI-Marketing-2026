# Plan: SIGNiX SubmitDocument with Push URL (Dashboard/Sync Plan 3)

This plan adds the **push notification URL** to every SubmitDocument request (so SIGNiX can send webhooks to this app) and sets **signer_count** when creating a SignatureTransaction. It uses a single helper **get_push_base_url(request=None)** for resolution and wires the submit path and config form to use it. Plan 2 (push listener) must be in place so SIGNiX can reach the endpoint once we send the URL.

**Design reference:** DESIGN-SIGNiX-DASHBOARD-AND-SYNC.md — Section 5 (SubmitDocument push URL), Section 5.4 (get_push_base_url), Section 3.4 (signer_count at submit), **Section 11 decision #7 (submitted event and document as sent)**. PLAN-SIGNiX-DASHBOARD-SYNC-MASTER.md — Plan 3 deliverables.

**Prerequisites:** Plan 1 (PLAN-SIGNiX-SYNC-MODEL) and Plan 2 (PLAN-SIGNiX-PUSH-LISTENER) are implemented. SignatureTransaction has signer_count and status_last_updated; SignixConfig has push_base_url; GET /signix/push/ is deployed and reachable. **For real end-to-end verification after submit, keep Django and ngrok running in parallel** so the callback URL embedded in SubmitDocument remains reachable from SIGNiX.

**Review this plan before implementation.** Implementation order is in **Section 5**; **Section 5a** defines batches and verification.

---

## 1. Goals and Scope

- **Push URL in SubmitDocument** — When a push base URL is available (from request, SignixConfig, or settings), include **ClientPreference** UseClientNotifyVersion2=yes and TransactionClientNotifyURL=**push_base_url** + "/signix/push/" in the SubmitDocument request. When the resolved URL is empty, do not add these elements.
- **Single helper** — **get_push_base_url(request=None)** in `apps.deals.signix` resolves in one place: (1) SignixConfig.push_base_url if set and non-empty; (2) request.build_absolute_uri('/').rstrip('/') when request is provided; (3) settings.SIGNIX_PUSH_BASE_URL or NGROK_DOMAIN; (4) "". No inline derivation in the view or body builder.
- **Body builder** — **build_submit_document_body(deal, document_set, push_base_url=None)** accepts an optional **push_base_url**. When provided and non-empty, the rendered XML includes the two ClientPreference elements; when empty or None, they are omitted. When None is passed, the builder may call get_push_base_url(None) for fallback (config/settings only).
- **Orchestrator** — **submit_document_set_for_signature(deal, document_set, request=None)** accepts an optional **request**. It calls get_push_base_url(request), passes the result to build_submit_document_body, and when creating SignatureTransaction sets **signer_count** to the number of signers (e.g. len(get_signer_order_for_deal(deal, template))). **Immediately after creating the SignatureTransaction**, create the initial **SignatureTransactionEvent**: event_type=**submitted**, occurred_at=transaction.submitted_at (so the detail page timeline starts with "Transaction submitted"). **Document set versions:** Ensure the latest DocumentInstanceVersion for each instance in the document set is marked status **"Submitted to SIGNiX"** (constant VERSION_STATUS_SUBMITTED_TO_SIGNIX in apps.deals.signix)—this is already done in the existing orchestrator per PLAN-SIGNiX-SEND-AND-PERSIST; the detail page uses these versions as "document as sent." If the orchestrator was refactored and no longer marks versions, add that step here.
- **Config form** — Add **push_base_url** to SignixConfigForm as an optional field. When the config page is rendered, pass **get_push_base_url(request)** to the template and display it as read-only text (e.g. “When blank, app will use: &lt;derived&gt;/signix/push/”) so the user sees the effective default without having to set the field.
- **View** — The Send for Signature view passes **request** into submit_document_set_for_signature so the push URL is derived from the current request in the typical case.
- **Out of scope this plan:** Dashboard Signers column (Plan 4), real download on complete (Plan 5). No push request validation (secret/token).

---

## 2. Push URL and Signer Count Behavior

### 2.1 Resolution order (get_push_base_url)

| Priority | Source | Behavior |
|----------|--------|----------|
| 1 | SignixConfig.push_base_url | If set and non-empty (after strip), return it (strip trailing slash if present). |
| 2 | request | If request is not None, return request.build_absolute_uri('/').rstrip('/'). |
| 3 | settings | If settings has SIGNIX_PUSH_BASE_URL, return it (strip trailing slash). Elif settings has NGROK_DOMAIN, return it with https:// if the value has no scheme. |
| 4 | — | Return "". |

Callers that need the full callback URL append "/signix/push/" (no double slash: helper returns base without trailing slash).

### 2.2 When ClientPreference elements are added

- **Added when:** Resolved push_base_url (after get_push_base_url) is non-empty.
- **Omitted when:** Resolved push_base_url is "" (so SIGNiX may use account-level push URL or no push).
- **XML:** UseClientNotifyVersion2 = **yes**; TransactionClientNotifyURL = **push_base_url + "/signix/push/"** (single slash between base and path).

### 2.3 Signer count at create

- When creating SignatureTransaction in the orchestrator, set **signer_count** = len(get_signer_order_for_deal(deal, document_set.document_set_template)). Use the same order that drives MemberInfo in the body so the count matches the transaction.

---

## 3. Helpers (implementation detail)

### 3.1 get_push_base_url(request=None)

- **Signature:** `(request=None) -> str`
- **Returns:** The push base URL (no path, no trailing slash), or "" if none available.
- **Logic:** (1) config = get_signix_config(); if getattr(config, 'push_base_url', None) and str(config.push_base_url).strip(), return that value.rstrip('/'). (2) Elif request is not None, return request.build_absolute_uri('/').rstrip('/'). (3) Elif hasattr(settings, 'SIGNIX_PUSH_BASE_URL') and settings.SIGNIX_PUSH_BASE_URL, return settings.SIGNIX_PUSH_BASE_URL.rstrip('/'). (4) Elif hasattr(settings, 'NGROK_DOMAIN') and settings.NGROK_DOMAIN, val = settings.NGROK_DOMAIN; return val if val.startswith('http') else f"https://{val}". (5) Else return "".
- **Location:** `apps.deals.signix`.

### 3.2 build_submit_document_body(deal, document_set, push_base_url=None)

- **Change:** Add optional parameter **push_base_url**. When None, call get_push_base_url(None) so config/settings still apply when the orchestrator does not pass a request-derived value.
- **Data dict / template:** Pass push_base_url into the data dict (e.g. data["push_base_url"] = push_base_url or get_push_base_url(None) if push_base_url is None). Template conditionally outputs the two ClientPreference elements when data.push_base_url is truthy.

### 3.3 submit_document_set_for_signature(deal, document_set, request=None)

- **Change:** Add optional **request** parameter. Compute push_base_url = get_push_base_url(request); pass to build_submit_document_body(deal, document_set, push_base_url=push_base_url). When creating SignatureTransaction, set signer_count = len(get_signer_order_for_deal(deal, document_set.document_set_template)).

---

## 4. Config Form and Template

- **SignixConfigForm:** Add **push_base_url** to the form’s Meta.fields (optional; CharField already on model from Plan 1). Use a URLField or CharField with a short help_text (e.g. “Optional. When blank, the app uses the current site URL or NGROK_DOMAIN.”).
- **View (signix_config_edit):** When rendering the form (GET or before POST), call **derived_push_base_url = get_push_base_url(request)** and pass it to the template as **derived_push_base_url** (or **push_base_url_derived**). Do not overwrite the form field value—this is read-only display only.
- **Template (signix_config_form.html):** Add a **Settings** (or “Push notifications”) subsection: the push_base_url form field, and below or next to it a line such as: “When blank, app will use: **&lt;derived_push_base_url&gt;/signix/push/**” (or “Current site URL (used when field is blank): &lt;derived_push_base_url&gt;”). When derived_push_base_url is empty, show e.g. “When blank, no push URL is sent (or use SIGNIX_PUSH_BASE_URL / NGROK_DOMAIN if set).”

---

## 5. Implementation Order (Checklist)

### Batch 1 — Helper and body builder (steps 1–5)

1. **Add get_push_base_url**
   - In `apps/deals/signix.py`, implement get_push_base_url(request=None) per Section 3.1. Use django.conf.settings for SIGNIX_PUSH_BASE_URL and NGROK_DOMAIN. Handle SignixConfig.push_base_url with getattr and strip; avoid breaking when the field is missing (Plan 1 adds it).

2. **Add push_base_url to build_submit_document_body**
   - Change signature to build_submit_document_body(deal, document_set, push_base_url=None). If push_base_url is None, set push_base_url = get_push_base_url(None). After building the data dict (build_submit_data_dict), set data["push_base_url"] = (push_base_url or "").strip().rstrip("/") so the template sees a clean base URL or empty string.

3. **Update SubmitDocument XML template**
   - In `apps/deals/templates/signix/submit_document_request.xml`, inside `<Data>`, add a conditional block: when data.push_base_url is set, output **immediately after `<SuspendOnStart>` and before the first `<MemberInfo>`**:
     - `<ClientPreference name="UseClientNotifyVersion2">yes</ClientPreference>`
     - `<ClientPreference name="TransactionClientNotifyURL">{{ data.push_base_url }}/signix/push/</ClientPreference>`
   - This order matches the working SubmitDocument example (Section 8).

4. **Orchestrator: pass push_base_url and set signer_count**
   - In submit_document_set_for_signature, add parameter request=None. At the start, push_base_url = get_push_base_url(request). Call build_submit_document_body(deal, document_set, push_base_url=push_base_url). When creating SignatureTransaction, compute signer_count = len(get_signer_order_for_deal(deal, document_set.document_set_template)) and add signer_count=signer_count to .objects.create(...). **Immediately after creating the transaction**, create **SignatureTransactionEvent**(signature_transaction=transaction, event_type="submitted", occurred_at=transaction.submitted_at). **Verify (or restore)** the step that marks the latest DocumentInstanceVersion per instance to status VERSION_STATUS_SUBMITTED_TO_SIGNIX ("Submitted to SIGNiX")—this is in the existing orchestrator per PLAN-SIGNiX-SEND-AND-PERSIST; if refactors removed it, add it here so the detail page can link to "document as sent."

5. **View: pass request**
   - In deal_send_for_signature (apps/deals/views.py), change the call to submit_document_set_for_signature(deal, document_set, request=request) so the push URL is derived from the current request.

6. **Update signix_dump_body command**
   - In the management command that dumps the SubmitDocument body, call build_submit_document_body(deal, document_set, push_base_url=get_push_base_url(None)) so the dumped XML includes the ClientPreference elements when config or settings provide a push base URL. Optionally add a --push-url argument to override for testing.

### Batch 2 — Config form and display (steps 7–10)

7. **Add push_base_url to SignixConfigForm**
   - In `apps/deals/forms.py`, add "push_base_url" to SignixConfigForm.Meta.fields. Optionally set help_text and widget (e.g. URLInput or TextInput). Field is optional (blank=True on model).
   - **Codebase note:** In this repo, `SignixConfigForm` already uses an explicit `Meta.fields` list, so the Batch 2 model field does **not** appear on the existing config page automatically. Plan 3 must add it intentionally here; updating only the model is not enough.

8. **Config view: pass derived URL**
   - In signix_config_edit, when rendering (GET or POST with form errors), derived = get_push_base_url(request). Pass derived_push_base_url=derived (or push_base_url_derived) in the context.

9. **Config template: show derived default**
   - In signix_config_form.html, add a “Push notifications” or “Push URL” subsection: label for push_base_url, form field, and below it a line “When blank, app will use: &lt;strong&gt;&lt;span&gt;{{ derived_push_base_url|default:"(none)" }}&lt;/span&gt;/signix/push/&lt;/strong&gt;” or “Current site URL (when field is blank): {{ derived_push_base_url|default:"(not set)" }}”. If derived_push_base_url is empty, show “When blank, no push URL is sent unless SIGNIX_PUSH_BASE_URL or NGROK_DOMAIN is set.”

10. **Verification (Batch 2)**
   - Django check passes. Open SIGNiX Configuration as staff; confirm push_base_url field and derived default text. Submit a deal; confirm SignatureTransaction has signer_count set and (if push URL is set) built XML contains the two ClientPreference elements (e.g. via signix_dump_body or a test).

---

## 5a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps and tests below.

### Batch 1 — Helper, body builder, orchestrator, view

**Includes:** get_push_base_url(request=None); build_submit_document_body(deal, document_set, push_base_url=None) and data["push_base_url"]; SubmitDocument XML template conditional ClientPreference; submit_document_set_for_signature(deal, document_set, request=None) with push_base_url and signer_count; deal_send_for_signature passes request; signix_dump_body updated to pass get_push_base_url(None) (and optional --push-url).

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.
2. **Unit tests:** `python manage.py test apps.deals.tests.test_signix_submit_push_url` — all pass (Section 6). These tests do not require ngrok.
3. **Build body with push URL:** In shell or test: build_submit_document_body(deal, document_set, push_base_url="https://example.ngrok-free.dev"). Assert the returned XML contains UseClientNotifyVersion2 and TransactionClientNotifyURL with /signix/push/.
4. **Build body without push URL:** build_submit_document_body(deal, document_set, push_base_url=""). Assert the returned XML does not contain ClientPreference or TransactionClientNotifyURL.
5. **Signer count:** Submit a deal (or call submit_document_set_for_signature in test with mocked send). Reload the created SignatureTransaction; assert signer_count equals the number of signers (e.g. 2 for a two-signer template).
6. **Real callback verification requirement:** If you verify that SIGNiX actually calls back after submit, keep `python manage.py runserver` and ngrok running in parallel and make sure the generated TransactionClientNotifyURL uses the active ngrok domain. Without the tunnel, the app will not receive the push notifications.

### Batch 2 — Config form and derived default

**Includes:** SignixConfigForm.push_base_url; signix_config_edit passes derived_push_base_url; signix_config_form.html shows push_base_url field and “When blank, app will use: …” text.

**How to test after Batch 2:**

1. **Config form:** Log in as staff, open SIGNiX Configuration. Confirm push_base_url field is present and the derived default line shows (e.g. current request host + /signix/push/ or “(not set)”).
2. **Save override:** Set push_base_url to https://override.example.com, save. Reload; confirm value persisted. Build body with get_push_base_url(None) (no request); assert resolved URL is the override.
3. **Manual submit:** From deal detail, click Send for Signature. Confirm transaction is created with signer_count set and (if using ngrok or override) that SIGNiX would receive the push URL in SubmitDocument (optional: inspect dump or logs).
4. **Real callback verification requirement:** If you are testing the full submit-to-push round trip, keep Django and ngrok running in parallel during the submit and the subsequent SIGNiX callback window. The callback URL in the built XML must point to the currently running ngrok tunnel.

---

## 6. Unit Tests (add to apps.deals.tests)

Create **apps/deals/tests/test_signix_submit_push_url.py** (or add to an existing signix test module). Use the same test setup as test_signix_build_body (Deal, DocumentSet, SignixConfig, template with two signers, etc.).

### 6.1 get_push_base_url

- **test_get_push_base_url_uses_config_when_set** — Set SignixConfig.push_base_url = "https://config.example.com"; get_push_base_url(None) returns "https://config.example.com" (or with trailing slash stripped).
- **test_get_push_base_url_uses_request_when_config_blank** — SignixConfig.push_base_url = "". Mock or use RequestFactory: request with path "/" and get_host() returning "testserver"; get_push_base_url(request) returns the request-derived base (e.g. "http://testserver").
- **test_get_push_base_url_returns_empty_when_nothing_set** — SignixConfig.push_base_url = "", no request, no settings; get_push_base_url(None) returns "".
- **test_get_push_base_url_strips_trailing_slash** — Config set to "https://x.com/"; assert get_push_base_url(None) == "https://x.com".

### 6.2 build_submit_document_body with push_base_url

- **test_build_body_includes_client_preferences_when_push_base_url_set** — build_submit_document_body(deal, document_set, push_base_url="https://push.example.com"). Assert "UseClientNotifyVersion2" in body and "TransactionClientNotifyURL" in body and "https://push.example.com/signix/push/" in body.
- **test_build_body_omits_client_preferences_when_push_base_url_empty** — build_submit_document_body(deal, document_set, push_base_url=""). Assert "TransactionClientNotifyURL" not in body (or ClientPreference block absent).
- **test_build_body_uses_get_push_base_url_when_push_base_url_none** — With SignixConfig.push_base_url set to "https://fallback.com", build_submit_document_body(deal, document_set, push_base_url=None). Assert body contains "https://fallback.com/signix/push/" (or fallback from config).

### 6.3 Orchestrator signer_count and document versions

- **test_submit_sets_signer_count** — Mock send_submit_document to return a result; call submit_document_set_for_signature(deal, document_set, request=request). Get the created SignatureTransaction (e.g. by deal.signature_transactions.first()); assert signer_count == 2 (or len(get_signer_order_for_deal(deal, template))). Assert **transaction.events.filter(event_type="submitted").count() == 1** and event.occurred_at == transaction.submitted_at.
- **test_submit_marks_document_versions_submitted_to_signix** — Mock send_submit_document; call submit_document_set_for_signature(deal, document_set, request=request). For every document instance in the document_set, assert the **latest** DocumentInstanceVersion has **status == VERSION_STATUS_SUBMITTED_TO_SIGNIX** ("Submitted to SIGNiX"). This verifies the orchestrator marks "document as sent" so the signature transaction detail page can link to it.

### 6.4 Integration (optional)

- **test_full_submit_includes_push_url** — If not mocking the full POST, use a test that builds the body via the orchestrator path and asserts the built XML (before send) contains the push URL when get_push_base_url(request) would return a value.
- **test_config_view_renders_with_derived_push_url** — (Optional.) GET the SIGNiX config edit view as staff; assert response.status_code == 200 and response contains push_base_url or "signix/push" (or derived_push_base_url text) so the config form renders with the push URL section.

---

## 7. File Summary

| Item | Value |
|------|--------|
| App / module | `apps.deals` (signix.py, views.py, forms.py, templates) |
| New helper | get_push_base_url(request=None) in signix.py |
| Modified | build_submit_document_body(deal, document_set, push_base_url=None); submit_document_set_for_signature(deal, document_set, request=None); deal_send_for_signature passes request |
| Template | apps/deals/templates/signix/submit_document_request.xml (conditional ClientPreference); templates/deals/signix_config_form.html (push_base_url field + derived default) |
| Form | SignixConfigForm — add push_base_url to fields |
| Tests | apps/deals/tests/test_signix_submit_push_url.py |

---

## 8. Open Issues / Implementation Decisions

- **Version status step (document as sent):** Before considering Batch 1 complete, **verify** that submit_document_set_for_signature still contains the step that marks the latest DocumentInstanceVersion for each instance in the document set to VERSION_STATUS_SUBMITTED_TO_SIGNIX. If it is missing (e.g. removed in a refactor), restore it in this plan so the signature transaction detail page "As sent" links work. **Decided:** Implement verification as part of step 4; restore the step if absent.
- **ClientPreference placement in XML:** Put the two ClientPreference elements **inside `<Data>`, immediately after `<SuspendOnStart>` and before the first `<MemberInfo>`**. Order: … SuspendOnStart → UseClientNotifyVersion2, TransactionClientNotifyURL → (optional NotificationSchedule if used) → MemberInfo → Form(s). This matches the working SubmitDocument example.
- **request in orchestrator:** submit_document_set_for_signature(deal, document_set, request=None) is backward-compatible when called without request (e.g. from management command); get_push_base_url(None) then uses config/settings. **Decided:** Optional request; view passes request so typical use gets request-derived URL.
- **signer_count when template has no signers:** If get_signer_order_for_deal returns [] (e.g. no template or no slots), signer_count would be 0. **Decided:** Allow 0; dashboard will show "0/0". Validation in validate_submit_preconditions already fails when a slot is unresolved, so a transaction is not normally created with no signers. Do not add extra validation to forbid signer_count=0.
- **NGROK_DOMAIN format:** Some setups use NGROK_DOMAIN without "https://". **Decided:** If the value does not start with "http", prepend "https://" (Section 3.1).
- **Dump command:** signix_dump_body currently calls build_submit_document_body(deal, document_set) with no push_base_url. **Decided:** Update the command to pass get_push_base_url(None) into build_submit_document_body so dumps include the push URL when config or settings provide one. Optionally support a --push-url flag to override for testing. Include this in the implementation (e.g. Batch 1 or a verification step).

---

## 9. Implementation Notes

- **Backward compatibility:** build_submit_document_body(deal, document_set) with no third argument must still work; use push_base_url=None and then push_base_url = push_base_url if push_base_url is not None else get_push_base_url(None).
- **Existing tests:** test_signix_build_body and test_signix_send may call build_submit_document_body(deal, document_set) or submit_document_set_for_signature(deal, document_set). After adding optional parameters, those calls remain valid; new tests explicitly pass push_base_url or request as needed.
- **SignixConfig.push_base_url:** Plan 1 adds the field; it may be blank. get_push_base_url should use getattr(config, 'push_base_url', None) and treat None or "" as “not set”.

---

## 10. Manual Testing (Details)

Use the following to verify the behavior without SIGNiX. If you want SIGNiX itself to deliver the follow-up push after submit, keep Django and ngrok running in parallel for the duration of the test.

**1. Config form — derived default**  
Log in as staff. Open **SIGNiX Configuration**. Confirm:
- A **Push base URL** (or “Push notification URL”) field is present and optional.
- Below it, text like “When blank, app will use: **&lt;your current host&gt;/signix/push/**” (e.g. http://127.0.0.1:8000/signix/push/ or your ngrok URL).  
If you open the page via ngrok, the derived URL should show the ngrok host.

**2. Config form — override**  
Set Push base URL to `https://my-override.example.com`, save. Reload the page; the field shows the override. The derived-default line can still show “when blank …” (it reflects what would be used if the field were blank).

**3. Dump body with push URL**  
Run:  
`python manage.py signix_dump_body <deal_id>`  
(If the command is updated to pass get_push_base_url(None), ensure config or NGROK_DOMAIN is set.) Open the generated XML and confirm it contains:
- `<ClientPreference name="UseClientNotifyVersion2">yes</ClientPreference>`
- `<ClientPreference name="TransactionClientNotifyURL">.../signix/push/</ClientPreference>`

**4. Submit and check transaction**  
From the deal detail page, click **Send for Signature** (with valid config and document set). After success:
- Open the signature transactions list or the deal’s related transactions.
- Open the new transaction and confirm **signer_count** is set (e.g. 2 for a two-signer template).
If you expect SIGNiX to call back after this submit, keep ngrok running and confirm the generated callback URL points at the active tunnel.

**5. Omit push URL**  
Clear SignixConfig.push_base_url and (if possible) ensure no SIGNIX_PUSH_BASE_URL or NGROK_DOMAIN. Build body (e.g. via dump or test) with push_base_url="". Confirm the built XML does not contain TransactionClientNotifyURL.

---

*End of plan. Proceed to implementation only after review. Next: PLAN-SIGNiX-DASHBOARD-SIGNERS.md (Plan 4).*
