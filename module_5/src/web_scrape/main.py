"""
This module manages scraping, cleaning, structuring data, and LLM-based processing.

This orchestrator prepares the data that is eventually passed to the database
loading modules. It ensures data consistency and structural integrity before 
secure insertion via psycopg SQL composition and parameter binding (Step 2).
It also follows Step 3 requirements by managing local file-based checkpoints 
safely within the configured data directories.
"""
import json
import os
import sys
import gc
import time
from datetime import datetime
from .scrape import scrape_data, save_data
from .clean import load_data
from .llm_hosting.app import _call_llm, _load_llm, _split_fallback

# Configuration for CPU+LLM processing
SKIP_SCRAPING = True
CHECKPOINT_INTERVAL = 50  # Save progress every N entries
MODEL_RELOAD_INTERVAL = 750
LLM_TIMEOUT = 60  # Timeout per LLM call in seconds

def log(msg: str):
    """
    Print a timestamped log message to stdout and immediately flush output.

    :param msg: The message to print to the console.
    :type msg: str
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

class TimeoutException(Exception):
    """
    Custom exception raised when an LLM call exceeds the allowed timeout.

    :param Exception: Base exception class.
    :type Exception: Exception
    """

def timeout_handler(signum, frame):
    """
    Signal handler that raises a TimeoutException when triggered.

    :param signum: The signal number received.
    :param frame: The current stack frame.
    :raises TimeoutException: Always raised to interrupt LLM execution.
    """
    raise TimeoutException("LLM call timed out")

# Check if raw.json already exists to skip scraping
RAW_JSON_PATH = "raw_data/raw.json"
if not os.path.exists(RAW_JSON_PATH):
    if SKIP_SCRAPING:
        log("[ERROR] raw.json doesn't exist and SKIP_SCRAPING is True!")
        log("Either set SKIP_SCRAPING=False or run scraping first")
        sys.exit(1)
    else:
        log("[START] Web scraping phase (~1-2 min per page)...")
        scrape_start = time.time()
        scraped_data = scrape_data()
        save_data(scraped_data)
        scrape_time = time.time() - scrape_start
        log(f"[OK] Scraped {len(scraped_data)} entries in {scrape_time/60:.1f} minutes")
else:
    log("[OK] Found existing raw.json - skipping scrape")

# Load and clean data
try:
    log("[START] Cleaning and parsing data...")
    clean_start = time.time()
    cleaned_data = load_data()
    clean_time = time.time() - clean_start
    log(f"[OK] Cleaned {len(cleaned_data)} entries in {clean_time:.1f} seconds")
except (FileNotFoundError, json.JSONDecodeError) as e:
    log(f"[ERROR] {e}")
    log("Run scraping first or check that raw_data/raw.json exists")
    sys.exit(1)

# Create output directory
OUTPUT_DIR = "raw_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_PATH = f"{OUTPUT_DIR}/llm_extended_applicant_data.json"
CHECKPOINT_PATH = f"{OUTPUT_DIR}/.llm_checkpoint.json"

# Check for checkpoint to resume processing
start_index = 0
if os.path.exists(CHECKPOINT_PATH):
    try:
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
            start_index = checkpoint.get("last_index", 0)
            # Restore previously processed data
            for i in range(start_index):
                if i < len(cleaned_data):
                    for key in ["LLM Program Name", "LLM University Name"]:
                        if key in checkpoint.get(str(i), {}):
                            cleaned_data[i][key] = checkpoint[str(i)][key]
            log(f"[RESUME] Resuming from checkpoint at entry {start_index}...")
    except (json.JSONDecodeError, OSError) as e:
        log(f"[WARNING] Could not load checkpoint: {e}")
        start_index = 0

# Load LLM model once
log("[START] Loading LLM model (TinyLlama 1.1B, ~2GB)...")
llm_load_start = time.time()
try:
    llm = _load_llm()
    llm_load_time = time.time() - llm_load_start
    log(f"[OK] LLM loaded in {llm_load_time:.1f}s. Starting LLM phase...")
except RuntimeError as e:
    log(f"[ERROR] Failed to load LLM: {e}")
    sys.exit(1)

# Track failures and successes
llm_failures = 0
LLM_TIMEOUTS = 0
llm_successes = 0
checkpoint_data = {}
last_checkpoint_time = time.time()
processing_start = time.time()

log(f"[START] Processing {len(cleaned_data)} entries...")

try:
    for i in range(start_index, len(cleaned_data)):
        row = cleaned_data[i]
        program_text = row.get("Program Name", "")
        university = row.get("University", "Unknown")

        if i > start_index and (i) % 10 == 0:
            elapsed = time.time() - processing_start
            rate = i / elapsed if elapsed > 0 else 0
            log(f"[TICK] {i:6d}/{len(cleaned_data)} @ {rate:.1f} entries/sec")

        if (i) % CHECKPOINT_INTERVAL == 0 and i > start_index:
            percent = int(i / len(cleaned_data) * 100)
            elapsed = time.time() - processing_start
            if i > 0:
                est_rem = (elapsed * len(cleaned_data) / i) - elapsed
                TIME_STR = f"{int(est_rem / 3600)}h {int((est_rem % 3600) / 60)}m"
            else:
                TIME_STR = "calculating..."
            log(f"[PROGRESS] {i}/{len(cleaned_data)} ({percent}%) | Est. {TIME_STR} left")

        if i > 0 and i % MODEL_RELOAD_INTERVAL == 0:
            log(f"[MEMORY] Reloading model at entry {i}...")
            del llm
            gc.collect()
            time.sleep(1)
            try:
                llm = _load_llm()
                log("[OK] Model reloaded successfully")
            except RuntimeError as e:
                log(f"[WARNING] Failed to reload model: {e}")

        if not program_text:
            row["LLM Program Name"] = ""
            row["LLM University Name"] = university
            checkpoint_data[str(i)] = {"LLM Program Name": "", "LLM University Name": university}
            continue

        try:
            llm_result = _call_llm(program_text)
            row["LLM Program Name"] = llm_result.get("standardized_program", "")
            row["LLM University Name"] = university
            checkpoint_data[str(i)] = {
                "LLM Program Name": row["LLM Program Name"],
                "LLM University Name": row["LLM University Name"]
            }
            llm_successes += 1
        except (TimeoutException, RuntimeError, ValueError) as e:
            llm_failures += 1
            prog = _split_fallback(program_text)[0]
            row["LLM Program Name"] = prog
            row["LLM University Name"] = university
            checkpoint_data[str(i)] = {
                "LLM Program Name": prog,
                "LLM University Name": university
            }
            if llm_failures <= 5:
                log(f"[FALLBACK] Row {i}: {type(e).__name__}: {str(e)[:80]}")

        if (i + 1) % CHECKPOINT_INTERVAL == 0:
            try:
                checkpoint = {
                    "last_index": i + 1,
                    "total_entries": len(cleaned_data),
                    "successes": llm_successes,
                    "failures": llm_failures
                }
                checkpoint.update(checkpoint_data)
                with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
                    json.dump(checkpoint, f)
                checkpoint_data = {}
                gc.collect()
                last_checkpoint_time = time.time()
                sys.stdout.flush()
            except OSError as e:
                log(f"[WARNING] Could not save checkpoint: {e}")

except KeyboardInterrupt:
    log(f"\n[WARNING] Interrupted at row {i+1}. Saving checkpoint...")

log(f"\n[START] Saving final output to {OUTPUT_PATH}...")
try:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(cleaned_data, file, indent=4, ensure_ascii=False)

    if os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)

    total_time = time.time() - processing_start
    log(f"[OK] Complete! Saved {len(cleaned_data)} entries to {OUTPUT_PATH}")
    log(f"[OK] Summary: {llm_successes} successes, {llm_failures} failures")
    log(f"[OK] Total processing time: {int(total_time / 3600)}h {int((total_time % 3600) / 60)}m")
except OSError as e:
    log(f"[ERROR] Failed to save output: {e}")
    sys.exit(1)
