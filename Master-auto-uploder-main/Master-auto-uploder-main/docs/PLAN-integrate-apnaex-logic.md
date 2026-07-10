# PLAN-integrate-apnaex-logic

## Goal Description
Integrate the batch extraction and content decryption logic from `ApnaEx-main` (specifically `appex_v4.py`) into the `Autoappx-main` project. The goal is to make `Autoappx` use `ApnaEx`'s superior extraction logic (including AES decryption) to process batches, but output the data in the structured format `Autoappx` expects for its database and downstream processing (instead of just a text file).

## User Review Required
> [!IMPORTANT]
> **Logic Replacement**: This plan proposes replacing the core extraction logic in `Autoappx` with `ApnaEx`'s logic.
> **Decryption**: `ApnaEx` handles decryption inline (e.g., specific AES keys/IVs). We will port this logic directly into `Autoappx`.

## Proposed Changes

### Autoappx-main

#### [NEW] `modules/apnaex_extractor.py`
Create a new module that encapsulates the logic from `ApnaEx/Extractor/modules/appex_v4.py`.
- **Function**: `extract_batch(batch_id, api_url, token)`
- **Logic**:
    - Replicate `ApnaEx`'s `fetch`, `handle_course`, and `process_video` functions.
    - Include the `decrypt(enc)` function with the hardcoded key/IV (`638udh...`, `fedcba...`).
    - **Crucial Change**: Instead of writing strings to a file (`f.writelines(...)`), yield or return a list of dictionaries matching `Autoappx`'s `appxdata.py` structure:
      ```python
      {
          "name": video_title,
          "url": decrypted_video_url,
          "type": "video", # or "pdf"
          "topicName": topic_name,
          "subjectName": subject_name
      }
      ```

#### [MODIFY] `modules/appx_master.py`
Update `collect_data` implementation to use the new `apnaex_extractor`.
- **Change**: integrating `apnaex_extractor.extract_batch` call.
- **Fallback**: optionally keep the old `appxdata.collect_data` as a backup or remove it entirely if `ApnaEx` logic is preferred exclusively.

#### [MODIFY] `modules/appxdata.py`
- Consider deprecating or removing conflicting logic if `apnaex_extractor.py` becomes the primary source.
- (Optional) Refactor to share `HttpxClient` session management or headers if beneficial, but `ApnaEx` uses `aiohttp`/`requests` while `Autoappx` uses `HttpxClient`, so distinct implementation might be cleaner initially.

## Verification Plan

### Automated Tests
- None planned (script-based verification).

### Manual Verification
1.  **Command Test**: Run `/addbatch` in the Telegram bot.
2.  **Logic Check**: Verify that the bot successfully logs in, fetches the batch list (using `ApnaEx` logic if applicable, or existing `Autoappx` logic), and then *extracts* the content using the new `apnaex_extractor`.
3.  **Data Check**: Verify that the extracted data (videos/PDFs) are correctly saved to the `Autoappx` database and that the bot starts processing/downloading them.
4.  **Decryption Check**: Verify that encrypted links (which `ApnaEx` handles) are correctly decrypted and playable/downloadable.
