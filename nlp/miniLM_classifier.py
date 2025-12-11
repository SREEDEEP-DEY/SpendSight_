# nlp/miniLM_classifier.py
"""
Process-safe MiniLM classifier for SpendSight.

Design:
 - Worker initializer _worker_init loads SentenceTransformer and builds prototype index.
 - classify_single() uses the per-process globals (MODEL, LABELS, EMBS).
 - classify_batch_minilm() is a small helper that submits many classify_single jobs
   to a ProcessPoolExecutor and returns results in input order.
"""

from typing import List, Tuple, Dict, Optional
import os
import re
import numpy as np
import traceback

# external deps (ensure installed)
from sentence_transformers import SentenceTransformer

# project imports (your taxonomy / vendor map)
from .taxonomy import CATEGORIES        # dict: { "Category.Sub": ["example1","example2", ...], ... }
from regex_engine.vendor_map import VENDOR_CATEGORY_MAP  # optional vendor-based bias

# ----------------------------
# Per-process globals (set by _worker_init)
# ----------------------------
_MODEL: Optional[SentenceTransformer] = None
_LABELS: Optional[List[str]] = None
_EMBS: Optional[np.ndarray] = None
_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

# ----------------------------
# Helpers (copied/adapted from your original class)
# ----------------------------
def normalize_desc(desc: str) -> str:
    if not desc:
        return ""
    d = desc.upper()
    d = re.sub(r"\s+", " ", d)
    glue_fixes = {
        "SALARYCREDIT": "SALARY CREDIT",
        "SMSCHRG": "SMS CHRG",
        "ATMWDR": "ATM WDR",
        "INTERNETBANGALORE": "INTERNET BANGALORE",
        "MOBILERECHARGE": "MOBILE RECHARGE",
        "LATEFINEFEES": "LATE FINE FEES",
        "VLPCHARGES": "VLP CHARGES",
        "TRANSFERTOANIL": "TRANSFER TO ANIL",
    }
    for bad, good in glue_fixes.items():
        d = d.replace(bad, good)
    d = re.sub(r"UPI/DR/[\w\d/.\-]+/", "UPI/", d)
    d = re.sub(r"UPI/\d+/", "UPI/", d)
    d = re.sub(r"\d{10,}", " ", d)
    d = re.sub(r"\s{2,}", " ", d).strip()
    return d

def _l2_normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=-1, keepdims=True) + 1e-12
    return x / norms

# Regex rules (same semantics as your class)
SALARY_RE = re.compile(r"\bSALARY CREDIT\b|\bSALARYCREDIT\b", re.I)
ATM_WDR_RE = re.compile(r"\bATM WDR\b|\bATMWDR\b", re.I)
SMS_CHG_RE = re.compile(r"SMS CHRG|SMSCHRG|SMS CHARGES", re.I)
EMI_RE = re.compile(r"\bEMI PAYMENT\b", re.I)
ATM_DEP_RE = re.compile(r"\bATM DEP\b", re.I)
INT_PD_RE = re.compile(r"\bINT\.?PD\b|\bINTEREST\b", re.I)
QTR_CHG_RE = re.compile(r"QUARTERLY AVG BAL|QTRLY AVG BAL", re.I)
ELEC_RE = re.compile(r"ELECTRICITY BILL", re.I)
GAS_RE = re.compile(r"\bGAS BILL\b", re.I)
INS_RE = re.compile(r"PMSBY|PMJJBY", re.I)

def _apply_rule_overrides(text_norm: str) -> Optional[Tuple[str, str, float, str]]:
    """
    Return (category, subcategory, confidence, rule_name) for a matched strong rule,
    or None if no rule matched.
    """
    if SALARY_RE.search(text_norm):
        return "Income", "Salary", 0.98, "salary_rule"
    if EMI_RE.search(text_norm):
        return "Debt", "LoanEMI", 0.95, "emi_rule"
    if ATM_WDR_RE.search(text_norm):
        return "Cash", "ATMWithdrawal", 0.85, "atm_wdr_rule"
    if ATM_DEP_RE.search(text_norm):
        return "Cash", "ATMDeposit", 0.85, "atm_dep_rule"
    if INT_PD_RE.search(text_norm):
        return "Income", "Interest", 0.92, "interest_rule"
    if QTR_CHG_RE.search(text_norm):
        return "BankCharges", "BalanceCharge", 0.80, "qtr_charge_rule"
    if SMS_CHG_RE.search(text_norm):
        return "BankCharges", "SMS", 0.80, "sms_charge_rule"
    if ELEC_RE.search(text_norm):
        return "Utilities", "Electricity", 0.90, "electricity_rule"
    if GAS_RE.search(text_norm):
        return "Utilities", "Gas", 0.88, "gas_rule"
    if INS_RE.search(text_norm):
        return "Insurance", "GovtScheme", 0.90, "govt_insurance_rule"
    return None

# ----------------------------
# Worker initializer (call inside each process)
# ----------------------------
def _worker_init(model_name: str = _MODEL_NAME):
    """
    Initialize per-process model & index.
    Pass this as ProcessPoolExecutor(initializer=_worker_init, initargs=(model_name,))
    """
    global _MODEL, _LABELS, _EMBS, _MODEL_NAME
    if _MODEL is not None:
        return
    _MODEL_NAME = model_name
    print(f"[MiniLM worker] pid={os.getpid()} loading model {_MODEL_NAME} ...")
    _MODEL = SentenceTransformer(_MODEL_NAME)
    # Build prototype index from taxonomy
    phrases: List[str] = []
    labels: List[str] = []
    for cat_label, examples in CATEGORIES.items():
        for phrase in examples:
            labels.append(cat_label)
            phrases.append(phrase)
    emb = _MODEL.encode(phrases, convert_to_numpy=True, show_progress_bar=False)
    _EMBS = _l2_normalize(emb)
    _LABELS = labels
    print(f"[MiniLM worker] pid={os.getpid()} ready. prototypes={len(_LABELS)}")

# ----------------------------
# classify_single: core worker function
# ----------------------------
def classify_single(text: str) -> Tuple[str, float, Dict]:
    """
    Classify a single description string using per-process globals.
    Returns (label_or_PENDING, confidence, meta).
    Safe: returns PENDING on unexpected errors.
    """
    global _MODEL, _LABELS, _EMBS
    try:
        if _MODEL is None:
            # allow single-process usage (lazy init)
            _worker_init()

        if not text or not text.strip():
            return "PENDING", 0.0, {"reason": "empty_text"}

        text_norm = normalize_desc(text)

        # 1) Hard rule overrides
        rule = _apply_rule_overrides(text_norm)
        if rule:
            cat, subcat, conf, rule_name = rule
            return f"{cat}.{subcat}", conf, {
                "source": "rule_override",
                "rule": rule_name,
                "normalized_text": text_norm,
            }

        # 2) Vendor biasing (optional)
        vendor_hit = None
        for key in VENDOR_CATEGORY_MAP:
            if key in text_norm:
                vendor_hit = key
                break
        vendor_bias = VENDOR_CATEGORY_MAP[vendor_hit] if vendor_hit else None

        # 3) Embed & nearest-prototype search
        q_emb = _MODEL.encode([text_norm], convert_to_numpy=True, show_progress_bar=False)
        q_emb = _l2_normalize(q_emb)
        sims = np.dot(q_emb, _EMBS.T)[0]
        top_idx = sims.argsort()[::-1][:5]
        top = [( _LABELS[i], float(sims[i]) ) for i in top_idx]

        best_label, best_sim = top[0]
        second_sim = top[1][1] if len(top) > 1 else 0.0
        raw_conf = best_sim

        # Confidence mapping (tuned)
        if raw_conf < 0.45:
            confidence = 0.0
        elif raw_conf >= 0.80:
            confidence = 1.0
        else:
            confidence = (raw_conf - 0.45) / 0.35
            confidence = round(max(0.0, min(confidence, 1.0)), 3)

        # Vendor bias strengthening
        if vendor_bias:
            vendor_cat, vendor_sub = vendor_bias
            if vendor_cat in best_label:
                confidence = max(confidence, 0.70)

        # Low-sim threshold
        if raw_conf < 0.50:
            return "PENDING", confidence, {
                "source": "bert",
                "reason": "low_similarity",
                "raw_conf": raw_conf,
                "top_5": top,
                "normalized_text": text_norm,
                "vendor_bias": vendor_bias,
            }

        return best_label, confidence, {
            "source": "bert",
            "raw_conf": raw_conf,
            "margin": raw_conf - second_sim,
            "top_5": top,
            "normalized_text": text_norm,
            "vendor_bias": vendor_bias,
        }

    except Exception as e:
        # NEVER let a worker crash the pool — return a safe PENDING result
        tb = traceback.format_exc()
        print(f"[MiniLM worker][ERROR] pid={os.getpid()} error: {e}\n{tb}")
        return "PENDING", 0.0, {"reason": "exception", "error": str(e)}

# ----------------------------
# classify_batch_minilm helper
# ----------------------------
def classify_batch_minilm(descriptions: List[str], pool) -> List[Tuple[str, float, Dict]]:
    """
    Submit descriptions to the provided executor (ProcessPoolExecutor) and return list of results.
    `pool` must implement .submit(callable, *args) and return futures with .result().
    This function preserves input order.
    """
    if not descriptions:
        return []

    # Submit tasks
    futures = [pool.submit(classify_single, desc) for desc in descriptions]
    # Gather results preserving order
    results = [f.result() for f in futures]
    return results

# End of file
