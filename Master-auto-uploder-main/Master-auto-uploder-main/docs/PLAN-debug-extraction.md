# PLAN-debug-extraction

## Context
When performing batch extraction, the system fails with:
1.  **JSON Decode Error**: `apnaex_extractor` failed to parse the response (Line 3, Column 1). This indicates the server returned non-JSON (likely an HTML error or empty body).
2.  **401 Unauthorized**: The fallback `appxdata` extraction failed with HTTP 401. This suggests invalid Auth credentials.
3.  **Warning**: "No subjects found for batch ..."

## Hypotheses
1.  **Authorization Header Format**: The `token` might include "Bearer " prefix which `ApnaEx` might handle differently (or the API expects raw).
2.  **User-ID Mismatch**: `apnaex_extractor.extract_batch_apnaex_logic` currently defaults `userid` to `"-2"`. The fallback logic uses the *extracted* user ID from the JWT. If the API requires matching User-ID, passing `"-2"` fails.
3.  **Token Expiry**: The token itself might be expired.

## Plan

### Phase 1: Investigation & Fix (backend-specialist)
1.  **Modify `apnaex_extractor.py`**:
    - Add robust error handling to print the *raw response text* when JSON parsing fails. This is critical to see what the server is actually saying (e.g. "Token Missing").
    - Accept `userid` as a mandatory argument instead of defaulting to `"-2"`.
    - Ensure `Authorization` header format matches what works (try stripping `Bearer ` if present, or adding it if missing).
2.  **Modify `appx_master.py`**:
    - Pass the extracted `userid` to `extract_batch_apnaex_logic`.
    - Ensure `token` is clean (strip "Bearer " prefix if the API expects raw token).

### Phase 2: Verification (debugger)
1.  **Test**: Run `/addbatch` again with valid credentials.
2.  **Validate**: Check logs for successful extraction or specific error messages.

## Verification Checklist
- [ ] User ID is correctly passed to extractor.
- [ ] Token is correctly formatted in headers.
- [ ] Raw response body is logged on failure.
- [ ] Extraction succeeds or returns clear error.
