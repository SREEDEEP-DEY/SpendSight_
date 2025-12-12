"""
Unified SpendSight Pipeline (Parallel / Batched / Instrumented)
----------------------------------------------------------------
Features:
 B) Batch classification logs (fast bulk writes)
 C) Parallel file-level processing (ProcessPoolExecutor)
 D) Instrumentation and progress logging (logging + tqdm)

Notes:
 - Uses classify_single() from nlp.miniLM_classifier (per-process safe).
 - Worker processes will initialize model lazily on first classify_single() call.
"""

import os
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Tuple, Any, Optional

from dotenv import load_dotenv
from psycopg2.extras import DictCursor, execute_values
import psycopg2

from tqdm import tqdm

load_dotenv()
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

# pipeline helpers (your module)
from PipeLine import (
    get_db_connection,
    parse_statement,
    normalize_txn,
    create_document_and_statement,
    insert_transactions,
    update_document_status,
    insert_classification_log,
)

# classifiers & engines
from regex_engine.regex_classifier import classify_with_regex
from heuristics.heuristics_classifier import classify_with_heuristics
# Use the worker-safe single-call API
from nlp.miniLM_classifier import classify_single
from llm.llm_classifier import llm_clf

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------
MAX_WORKERS = int(os.getenv("UNIFIED_PIPELINE_MAX_WORKERS", min(8, (os.cpu_count() or 2))))
LLM_BATCH_SIZE = int(os.getenv("UNIFIED_PIPELINE_LLM_BATCH_SIZE", 32))
LLM_RETRY_MAX = int(os.getenv("UNIFIED_PIPELINE_LLM_RETRY_MAX", 3))
LLM_BACKOFF_BASE = float(os.getenv("UNIFIED_PIPELINE_LLM_BACKOFF_BASE", 2.0))

MINILM_LOW_CONF_THRESHOLD = float(os.getenv("MINILM_LOW_CONF_THRESHOLD", 0.50))
LLM_FALLBACK_CONF_THRESHOLD = float(os.getenv("LLM_FALLBACK_CONF_THRESHOLD", 0.25))

# bulk insert SQL (classification_log). Adjust schema if different.
BULK_INSERT_CLASSIFICATION_LOG_SQL = """
INSERT INTO classification_log (log_id, txn_id, prediction, confidence, meta, created_at)
VALUES %s
"""

# ---------------------------------------------------------------------
# Logging config
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(processName)s] %(message)s"
)
logger = logging.getLogger("UnifiedPipeline")

# ---------------------------------------------------------------------
# Retry/backoff for LLM batched calls
# ---------------------------------------------------------------------
def llm_classify_with_retry(descriptions: List[str]) -> List[Tuple[str, Optional[str], float, Dict]]:
    attempt = 0
    while attempt < LLM_RETRY_MAX:
        try:
            results = llm_clf.classify_batch(descriptions)
            return results
        except Exception as e:
            attempt += 1
            backoff = (LLM_BACKOFF_BASE ** attempt)
            logger.warning("[LLM] classify_batch failed (attempt %d/%d): %s. Sleeping %.1fs",
                           attempt, LLM_RETRY_MAX, str(e)[:200], backoff)
            time.sleep(backoff)
    logger.error("[LLM] classify_batch failed after %d attempts", LLM_RETRY_MAX)
    return [("PENDING", None, 0.0, {"error": "llm_failed"}) for _ in descriptions]

# ---------------------------------------------------------------------
# Bulk insert classification logs helper (with fallback)
# ---------------------------------------------------------------------

# Updated BULK SQL (removed 'created_at' column)
BULK_INSERT_CLASSIFICATION_LOG_SQL = """
INSERT INTO classification_log (log_id, txn_id, stage, prediction, confidence, meta)
VALUES %s
"""

def bulk_insert_classification_log(conn, logs: List[Dict[str, Any]]):
    """
    Bulk-insert classification logs using execute_values.
    Each log should be a dict with keys:
      txn_id, source (for stage fallback), stage (optional), prediction, confidence, meta (python dict)
    """
    if not logs:
        return

    # Prepare tuples for execute_values: (txn_id, stage, prediction, confidence, meta_json)
    # NOTE: 'source' is NOT a column - it's only used as fallback for 'stage'
    tuples = []
    for log in logs:
        stage = log.get("stage", log.get("source", "unknown"))  # fallback to source if stage missing
        meta_json = json.dumps(log.get("meta", {}))
        tuples.append((
            log["txn_id"],
            stage,  # Only stage goes into DB
            log["prediction"],
            float(log.get("confidence", 0.0)),
            meta_json
        ))

    # Template: removed 'created_at' - only has log_id (auto-generated), txn_id, stage, prediction, confidence, meta
    template = "(uuid_generate_v4(), %s, %s, %s, %s::double precision, %s::jsonb)"

    try:
        with conn.cursor() as cur:
            execute_values(cur, BULK_INSERT_CLASSIFICATION_LOG_SQL, tuples, template=template)
        conn.commit()
    except Exception as e:
        logger.warning("[bulk_insert] bulk insert failed: %s. Falling back to per-row insert.", e)
        conn.rollback()
        
        # Need to get a fresh connection after rollback for fallback inserts
        for log in logs:
            try:
                # Rollback any pending transaction first
                conn.rollback()
                
                # ensure we pass 'stage' to the single-row helper
                insert_classification_log(
                    conn,
                    txn_id=log["txn_id"],
                    stage=log.get("stage", log.get("source", "unknown")),
                    prediction=log["prediction"],
                    confidence=float(log.get("confidence", 0.0)),
                    meta=log.get("meta", {})
                )
            except Exception as fallback_error:
                logger.exception("[bulk_insert] fallback failed for txn_id=%s: %s", 
                               log.get("txn_id"), fallback_error)
# ---------------------------------------------------------------------
# DB helpers used inside workers
# ---------------------------------------------------------------------
def statement_exists(conn, user_id, original_filename) -> Tuple[bool, Optional[str]]:
    query = """
    SELECT s.statement_id
    FROM statements s
    JOIN documents d ON d.doc_id = s.doc_id
    WHERE d.user_id = %s
      AND d.original_filename = %s
    ORDER BY d.upload_time DESC
    LIMIT 1;
    """
    with conn.cursor() as cur:
        cur.execute(query, (user_id, original_filename))
        row = cur.fetchone()
        if row:
            return True, row[0]
    return False, None

def fetch_transactions_for_minilm(conn, statement_id):
    q = """
        SELECT txn_id, description_clean, description_raw, category, confidence
        FROM transactions
        WHERE statement_id = %s
          AND (
               category IS NULL
            OR category = 'PENDING'
            OR (classification_source IN ('regex','heuristic') AND confidence < %s)
          );
    """
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(q, (statement_id, MINILM_LOW_CONF_THRESHOLD))
        return cur.fetchall()

def fetch_transactions_for_llm(conn, statement_id):
    q = """
    SELECT txn_id, description_clean, description_raw, category, confidence
    FROM transactions
    WHERE statement_id = %s
      AND (
          category = 'PENDING'
          OR (classification_source = 'bert' AND confidence < %s)
      );
    """
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(q, (statement_id, LLM_FALLBACK_CONF_THRESHOLD))
        return cur.fetchall()

# Worker-local MiniLM application using classify_single (per-process safe)
def apply_minilm_to_txn_worker(conn, txn):
    """
    Uses classify_single from nlp.miniLM_classifier which lazily loads the model
    inside the worker process. Updates DB and inserts a per-row log (the row-log
    will still be included in the classification_log bulk list where applicable).
    """
    try:
        desc = txn.get("description_clean") or txn.get("description_raw") or ""
        if not desc:
            with conn.cursor() as cur:
                cur.execute("UPDATE transactions SET classification_source='bert', confidence=0.0 WHERE txn_id=%s", (txn["txn_id"],))
            conn.commit()
            # log
            insert_classification_log(conn, txn["txn_id"], "bert", "PENDING", 0.0, {"reason": "empty"})
            return "PENDING"

        label, confidence, meta = classify_single(desc)
        if label == "PENDING":
            category = "PENDING"
            subcategory = None
        else:
            parts = label.split(".")
            category = parts[0]
            subcategory = parts[1] if len(parts) > 1 else None

        with conn.cursor() as cur:
            cur.execute("""
                UPDATE transactions
                SET category=%s, subcategory=%s, confidence=%s, classification_source='bert'
                WHERE txn_id=%s
            """, (category, subcategory, confidence, txn["txn_id"]))
        # Insert a log (per-row). We still accumulate logs for bulk insertion for sources that were batched.
        insert_classification_log(conn, txn["txn_id"], "bert", label, confidence, meta or {})
        conn.commit()
        return label
    except Exception:
        logger.exception("[Worker:minilm] failed for txn %s", txn.get("txn_id"))
        try:
            conn.rollback()
        except Exception:
            pass
        return "PENDING"

# ---------------------------------------------------------------------
# Worker: full file processing
# ---------------------------------------------------------------------


def worker_process_file(args: Tuple[str, str]) -> Tuple[str, Dict[str, Any]]:
    filepath, user_id = args
    start_time = time.time()
    conn = None
    metrics = {
        "inserted": 0,
        "regex_attempted": 0,
        "regex_classified": 0,
        "heur_attempted": 0,
        "heur_classified": 0,
        "mini_attempted": 0,
        "mini_classified": 0,
        "mini_pending": 0,
        "llm_attempted": 0,
        "llm_classified": 0,
        "timings": {},
    }

    try:
        logger.info("[Worker] Processing file: %s", filepath)
        conn = get_db_connection()
        original_filename = os.path.basename(filepath)

        # Idempotency: skip already-processed files but run ALL classifiers on low-conf/pending
        exists, existing_statement_id = statement_exists(conn, user_id, original_filename)
        if exists and existing_statement_id:
            logger.info("[Worker] already processed: %s, re-running all classifiers on pending/low-conf", original_filename)
            
            # REGEX pass on PENDING transactions
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT txn_id, description_raw
                    FROM transactions
                    WHERE statement_id = %s
                      AND (category IS NULL OR category = 'PENDING')
                """, (existing_statement_id,))
                pending_regex = cur.fetchall()
            
            metrics["regex_attempted"] = len(pending_regex)
            for txn in pending_regex:
                desc = txn.get("description_raw") or ""
                category, subcat, vendor, conf, meta = classify_with_regex(desc)
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE transactions
                        SET vendor=%s, category=%s, subcategory=%s, confidence=%s, classification_source='regex'
                        WHERE txn_id=%s
                    """, (vendor, category, subcat, conf, txn["txn_id"]))
                prediction = f"{category}.{subcat}" if subcat else category
                insert_classification_log(conn, txn["txn_id"], "regex", prediction, conf, meta or {})
                if category != "PENDING":
                    metrics["regex_classified"] += 1
            conn.commit()
            
            # HEURISTICS pass on still-pending
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT txn_id, description_clean, description_raw
                    FROM transactions
                    WHERE statement_id = %s
                      AND (category IS NULL OR category = 'PENDING')
                """, (existing_statement_id,))
                pending_heur = cur.fetchall()
            
            metrics["heur_attempted"] = len(pending_heur)
            for txn in pending_heur:
                desc = txn["description_clean"] or txn["description_raw"] or ""
                cat, sub, conf, meta = classify_with_heuristics(desc)
                if cat != "PENDING":
                    metrics["heur_classified"] += 1
                    with conn.cursor() as cur_update:
                        cur_update.execute("""
                            UPDATE transactions
                            SET category=%s, subcategory=%s, confidence=%s, classification_source='heuristic'
                            WHERE txn_id=%s
                        """, (cat, sub, conf, txn["txn_id"]))
                    prediction = f"{cat}.{sub}" if sub else cat
                    insert_classification_log(conn, txn["txn_id"], "heuristic", prediction, conf, meta or {})
            conn.commit()
            
            # MiniLM pass on low-conf
            pending_bert = fetch_transactions_for_minilm(conn, existing_statement_id)
            metrics["mini_attempted"] = len(pending_bert)
            for txn in pending_bert:
                label = apply_minilm_to_txn_worker(conn, txn)
                if label == "PENDING":
                    metrics["mini_pending"] += 1
                else:
                    metrics["mini_classified"] += 1
            
            # LLM pass on remaining low-conf
            llm_pending = fetch_transactions_for_llm(conn, existing_statement_id)
            metrics["llm_attempted"] = len(llm_pending)
            if llm_pending:
                descriptions = [(t["description_clean"] or t["description_raw"] or "") for t in llm_pending]
                all_results = []
                for i in range(0, len(descriptions), LLM_BATCH_SIZE):
                    batch = descriptions[i:i+LLM_BATCH_SIZE]
                    res = llm_classify_with_retry(batch)
                    all_results.extend(res)
                for txn, res in zip(llm_pending, all_results):
                    category, subcategory, confidence, meta = res
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE transactions
                            SET category=%s, subcategory=%s, confidence=%s, classification_source='llm'
                            WHERE txn_id=%s
                        """, (category, subcategory, confidence, txn["txn_id"]))
                    prediction = f"{category}.{subcategory}" if subcategory else category
                    insert_classification_log(conn, txn["txn_id"], "llm", prediction, confidence, meta or {})
                    if category and category not in ("PENDING", "UNCLEAR"):
                        metrics["llm_classified"] += 1
                conn.commit()
            
            metrics["timings"]["total_s"] = time.time() - start_time
            return filepath, metrics

        # Step 1: Parse
        t0 = time.time()
        bank_name, raw_txns = parse_statement(filepath)
        metrics["timings"]["parse_s"] = time.time() - t0
        logger.info("[Worker] parsed=%d bank=%s", len(raw_txns) if raw_txns else 0, bank_name)

        if not bank_name or not raw_txns:
            logger.warning("[Worker] no transactions parsed: %s", filepath)
            metrics["timings"]["total_s"] = time.time() - start_time
            return filepath, metrics

        # Step 2: create document & statement
        t0 = time.time()
        doc_id, statement_id = create_document_and_statement(conn, user_id, bank_name, filepath, original_filename)
        metrics["timings"]["docstmt_s"] = time.time() - t0

        # Step 3: normalize
        t0 = time.time()
        normalized = []
        for tx in raw_txns:
            n = normalize_txn(tx, statement_id, user_id)
            if n:
                normalized.append(n)
        metrics["timings"]["normalize_s"] = time.time() - t0

        # Step 4: insert txns
        t0 = time.time()
        txn_ids = insert_transactions(conn, normalized) or []
        metrics["inserted"] = len(txn_ids)
        metrics["timings"]["insert_txns_s"] = time.time() - t0

        # Prepare log collector
        classification_log: List[Dict[str, Any]] = []

        # Step 5: Regex classification
        t0 = time.time()
        regex_attempted = len(txn_ids)
        regex_classified = 0
        regex_failed = 0
        for i, txn_id in enumerate(txn_ids):
            tx = normalized[i]
            desc = tx.get("description_raw") or ""
            category, subcat, vendor, conf, meta = classify_with_regex(desc)
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE transactions
                    SET vendor=%s, category=%s, subcategory=%s, confidence=%s, classification_source='regex'
                    WHERE txn_id=%s
                """, (vendor, category, subcat, conf, txn_id))
            prediction = f"{category}.{subcat}" if subcat else category
            classification_log.append({
                "txn_id": txn_id,
                "stage": "regex",
                "prediction": prediction,
                "confidence": conf,
                "meta": meta or {}
            })
            if category != "PENDING":
                regex_classified += 1
            else:
                regex_failed += 1
        conn.commit()
        metrics["regex_attempted"] = regex_attempted
        metrics["regex_classified"] = regex_classified
        metrics["timings"]["regex_s"] = time.time() - t0

        # Step 5b: heuristics for remaining
        t0 = time.time()
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT txn_id, description_clean, description_raw
                FROM transactions
                WHERE statement_id = %s
                  AND (category IS NULL OR category = 'PENDING')
            """, (statement_id,))
            pending_heur = cur.fetchall()
        heur_attempted = len(pending_heur)
        heur_classified = 0
        for txn in pending_heur:
            desc = txn["description_clean"] or txn["description_raw"] or ""
            cat, sub, conf, meta = classify_with_heuristics(desc)
            if cat != "PENDING":
                heur_classified += 1
                with conn.cursor() as cur_update:
                    cur_update.execute("""
                        UPDATE transactions
                        SET category=%s, subcategory=%s, confidence=%s, classification_source='heuristic'
                        WHERE txn_id=%s
                    """, (cat, sub, conf, txn["txn_id"]))
                classification_log.append({
                    "txn_id": txn["txn_id"],
                    "stage": "heuristic",
                    "prediction": f"{cat}.{sub}" if sub else cat,
                    "confidence": conf,
                    "meta": meta or {}
                })
        conn.commit()
        metrics["heur_attempted"] = heur_attempted
        metrics["heur_classified"] = heur_classified
        metrics["timings"]["heur_s"] = time.time() - t0

        # Step 6: MiniLM classification for pending/low-conf
        t0 = time.time()
        pending_bert = fetch_transactions_for_minilm(conn, statement_id)
        metrics["mini_attempted"] = len(pending_bert)
        # We run classify_single in this worker process (model will be loaded lazily inside classify_single)
        for txn in pending_bert:
            label = apply_minilm_to_txn_worker(conn, txn)
            if label == "PENDING":
                metrics["mini_pending"] += 1
            else:
                metrics["mini_classified"] += 1
            # The per-txn insert_classification_log is already done inside apply_minilm_to_txn_worker
        metrics["timings"]["minilm_s"] = time.time() - t0

        # Step 7: LLM fallback (batched) for remaining
        t0 = time.time()
        llm_pending = fetch_transactions_for_llm(conn, statement_id)
        metrics["llm_attempted"] = len(llm_pending)
        if llm_pending:
            descriptions = [(t["description_clean"] or t["description_raw"] or "") for t in llm_pending]
            llm_results = []
            for i in range(0, len(descriptions), LLM_BATCH_SIZE):
                batch = descriptions[i:i+LLM_BATCH_SIZE]
                llm_results.extend(llm_classify_with_retry(batch))
            for txn, (category, subcategory, confidence, meta) in zip(llm_pending, llm_results):
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE transactions
                        SET category=%s, subcategory=%s, confidence=%s, classification_source='llm'
                        WHERE txn_id=%s
                    """, (category, subcategory, confidence, txn["txn_id"]))
                classification_log.append({
                    "txn_id": txn["txn_id"],
                    "stage": "llm",
                    "prediction": f"{category}.{subcategory}" if subcategory else category,
                    "confidence": confidence,
                    "meta": meta or {}
                })
                if category and category not in ("PENDING", "UNCLEAR"):
                    metrics["llm_classified"] += 1
            conn.commit()
        metrics["timings"]["llm_s"] = time.time() - t0

        # Bulk insert collected logs (regex, heuristics, llm)
        t0 = time.time()
        try:
            bulk_insert_classification_log(conn, classification_log)
            metrics["timings"]["bulk_logs_s"] = time.time() - t0
        except Exception:
            logger.exception("[Worker] bulk log insertion failed")
            metrics["timings"]["bulk_logs_s"] = time.time() - t0

        # Update doc status
        try:
            update_document_status(conn, doc_id, "parsed")
        except Exception:
            logger.exception("[Worker] update_document_status failed for doc_id=%s", doc_id)

        metrics["timings"]["total_s"] = time.time() - start_time
        return filepath, metrics

    except Exception as e:
        logger.exception("[Worker] unexpected failure for file=%s : %s", filepath, e)
        return filepath, {"error": str(e), "trace": traceback.format_exc()}
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
# ---------------------------------------------------------------------
# Main orchestration: parallel across files
# ---------------------------------------------------------------------
def main():
    input_dir = Path("./data/input")
    pdf_files = sorted([str(p) for p in input_dir.glob("*.pdf")])

    if not pdf_files:
        logger.warning("[Main] No PDFs found in data/input.")
        return

    max_workers = min(MAX_WORKERS, len(pdf_files))
    logger.info("[Main] Starting pipeline with %d workers for %d files", max_workers, len(pdf_files))

    aggregated = {
        "total_inserted": 0,
        "total_regex_attempted": 0,
        "total_regex_classified": 0,
        "total_heur_attempted": 0,
        "total_heur_classified": 0,
        "total_mini_attempted": 0,
        "total_mini_classified": 0,
        "total_llm_attempted": 0,
        "total_llm_classified": 0,
        "files_processed": 0,
        "errors": 0,
        "per_file": {}
    }

    args_list = [(p, DEFAULT_USER_ID) for p in pdf_files]

    with ProcessPoolExecutor(max_workers=max_workers) as exe:
        future_to_path = {exe.submit(worker_process_file, args): args[0] for args in args_list}
        for fut in tqdm(as_completed(future_to_path), total=len(future_to_path), desc="Processing files"):
            path = future_to_path[fut]
            try:
                filepath, metrics = fut.result()
                aggregated["files_processed"] += 1
                aggregated["per_file"][filepath] = metrics
                if "error" in metrics:
                    aggregated["errors"] += 1
                else:
                    aggregated["total_inserted"] += metrics.get("inserted", 0)
                    aggregated["total_regex_attempted"] += metrics.get("regex_attempted", 0)
                    aggregated["total_regex_classified"] += metrics.get("regex_classified", 0)
                    aggregated["total_heur_attempted"] += metrics.get("heur_attempted", 0)
                    aggregated["total_heur_classified"] += metrics.get("heur_classified", 0)
                    aggregated["total_mini_attempted"] += metrics.get("mini_attempted", 0)
                    aggregated["total_mini_classified"] += metrics.get("mini_classified", 0)
                    aggregated["total_llm_attempted"] += metrics.get("llm_attempted", 0)
                    aggregated["total_llm_classified"] += metrics.get("llm_classified", 0)
                logger.info("[Main] finished %s inserted=%d regex=%d/%d heur=%d/%d mini=%d/%d llm=%d/%d",
                            path,
                            metrics.get("inserted", 0),
                            metrics.get("regex_classified", 0), metrics.get("regex_attempted", 0),
                            metrics.get("heur_classified", 0), metrics.get("heur_attempted", 0),
                            metrics.get("mini_classified", 0), metrics.get("mini_attempted", 0),
                            metrics.get("llm_classified", 0), metrics.get("llm_attempted", 0))
            except Exception as e:
                logger.exception("[Main] worker failed for %s : %s", path, e)
                aggregated["errors"] += 1

    # Summary
    logger.info("========= PIPELINE SUMMARY (Parallel) =========")
    logger.info("Files processed             : %d", aggregated["files_processed"])
    logger.info("Total transactions inserted : %d", aggregated["total_inserted"])
    logger.info("Regex: attempted=%d classified=%d", aggregated["total_regex_attempted"], aggregated["total_regex_classified"])
    logger.info("Heuristics: attempted=%d classified=%d", aggregated["total_heur_attempted"], aggregated["total_heur_classified"])
    logger.info("MiniLM: attempted=%d classified=%d", aggregated["total_mini_attempted"], aggregated["total_mini_classified"])
    logger.info("LLM: attempted=%d classified=%d", aggregated["total_llm_attempted"], aggregated["total_llm_classified"])
    logger.info("Errors: %d", aggregated["errors"])
    logger.info("===============================================")

    # save dashboard snapshot once (main process)
    if DEFAULT_USER_ID:
        try:
            period_label = "lifetime_till_today"
            from reports_dashboard import save_dashboard_snapshot
            report_id = save_dashboard_snapshot(user_id=DEFAULT_USER_ID, period=period_label, start_date=None, end_date=None)
            logger.info("[Reports] Dashboard snapshot saved (user=%s, report_id=%s)", DEFAULT_USER_ID, report_id)
        except Exception:
            logger.exception("[Reports] Failed to save dashboard snapshot")

    return aggregated

if __name__ == "__main__":
    main()
