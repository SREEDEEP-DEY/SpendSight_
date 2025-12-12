# nlp/miniLM_classifier.py
"""
Process-safe MiniLM classifier for SpendSight (upgraded).

Design goals:
 - Keep safe per-process initialization (SentenceTransformer).
 - Strong rule overrides for obvious cases (salary, emi, atm, refunds, NEFT/IMPS, etc).
 - Aggressive normalization to handle IDBI/ICICI tokens (IPAY, UPI/..., ID064111, BN..., REF\0319\ etc).
 - Vendor biasing & fallback to heuristics if similarity is low.
 - More informative meta for debugging and logging.

Outputs:
 - classify_single(text) -> (label_or_PENDING, confidence(float 0-1), meta:dict)
 - classify_batch_minilm(descriptions, pool) as before
"""

from typing import List, Tuple, Dict, Optional
import os
import re
import numpy as np
import traceback

# external deps (ensure installed)
from sentence_transformers import SentenceTransformer

# local imports
from .taxonomy import CATEGORIES        # dict: { "Category.Sub": ["example1","example2", ...], ... }
# optional vendor map (if present in repo)
try:
    from regex_engine.vendor_map import VENDOR_CATEGORY_MAP  # { "vendor_token": ("Category","Sub") }
except Exception:
    VENDOR_CATEGORY_MAP = {}

# fallback to heuristics when bert is uncertain
try:
    from heuristics.heuristics_classifier import classify_with_heuristics
except Exception:
    classify_with_heuristics = None

# ----------------------------
# Per-process globals (set by _worker_init)
# ----------------------------
_MODEL: Optional[SentenceTransformer] = None
_LABELS: Optional[List[str]] = None
_EMBS: Optional[np.ndarray] = None
_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

# ----------------------------
# Helpers
# ----------------------------
def normalize_desc(desc: str) -> str:
    """Aggressively normalize description text for better matching."""
    if not desc:
        return ""
    d = desc.upper()

    # common noisy tokens and glue fixes across Indian bank statements
    glue_fixes = {
        "SALARYCREDIT": "SALARY CREDIT",
        "SMSCHRG": "SMS CHRG",
        "ATMWDR": "ATM WDR",
        "ATMWDL": "ATM WDR",
        "ATMWDL-": "ATM WDR",
        "IPAY/ESHP": "IPAY",
        "IPAY/ESHP/": "IPAY",
        "IPAY/": "IPAY/",
        "IPAY/ESHP//": "IPAY/",
        "SBIEPAY": "SBIEPAY",
        "SBIPAY": "SBIPAY",
        "SBIPAY/": "SBIPAY/",
        "SBI EPAY": "SBIEPAY",
        "ID064111": "ID_REF",
        "ID058801": "ID_REF",
        "ID064101": "ID_REF",
        "BN135701": "BN_REF",
        "NEFT-": "NEFT ",
        "NEFT/": "NEFT ",
        "IMPS/": "IMPS ",
        "MMT/IMPS": "IMPS",
        "VISA-POS": "VISA POS",
        "VISA/": "VISA ",
        "VISA REF": "VISA REF",
        "UPI/": "UPI/",
        "UPI": "UPI",
        "U P I": "UPI"
    }
    
    # Apply simple string replacements first
    for bad, good in glue_fixes.items():
        d = d.replace(bad, good)
    
    # Then handle regex patterns separately
    d = re.sub(r'REF\\\d{3}', 'REF', d)  # REF\0319 etc - FIXED: proper escaping
    d = re.sub(r'REF\\', 'REF ', d)       # REF\ -> REF

    # remove long numeric ids that pollute similarity
    d = re.sub(r'\b\d{7,}\b', ' ', d)         # long numeric tokens
    d = re.sub(r'\b[A-Z0-9]{10,}\b', ' ', d)  # long alpha-numeric sequences likely refs
    # compress whitespace and punctuation
    d = re.sub(r'[_\t]+', ' ', d)
    d = re.sub(r'\s+', ' ', d).strip()
    return d

def _l2_normalize(x: np.ndarray) -> np.ndarray:
    """L2 normalize embeddings for cosine similarity."""
    norms = np.linalg.norm(x, axis=-1, keepdims=True) + 1e-12
    return x / norms

# Regex rules (expanded)
SALARY_RE = re.compile(r"\bSALARY CREDIT\b|\bSALARYCREDIT\b|\bSALARY\b", re.I)
ATM_WDR_RE = re.compile(r"\bATM WDR\b|\bATMWDR\b|\bCASH WDL\b|\bCASH WITHDRAWAL\b", re.I)
SMS_CHG_RE = re.compile(r"\bSMS CHR|SMS CHRG|SMSCHRG|SMS CHARGE", re.I)
EMI_RE = re.compile(r"\bEMI\b|\bEMI PAYMENT\b|\bE M I\b", re.I)
ATM_DEP_RE = re.compile(r"\bATM DEP\b|\bATM DEPOSIT\b", re.I)
INT_PD_RE = re.compile(r"\bINT\.?PD\b|\bINTEREST\b|\bINT PAID\b", re.I)
QTR_CHG_RE = re.compile(r"QUARTERLY AVG BAL|QTRLY AVG BAL|AVG BALANCE CHARGE", re.I)
ELEC_RE = re.compile(r"ELECTRICITY BILL|ELECTRICITY CHARGE|BILL PAYMENT - ELECTRICITY", re.I)
GAS_RE = re.compile(r"\bGAS BILL\b|\bGAS CHARGE\b", re.I)
INS_RE = re.compile(r"PMSBY|PMJJBY|INSURANCE|PREMIUM", re.I)
NEFT_IMPS_RE = re.compile(r"\bNEFT\b|\bIMPS\b|\bRTGS\b|\bNFS\b|\bMMID\b", re.I)
REFUND_RE = re.compile(r"\bREFUND\b|\bREVERSAL\b|\bREVERSED\b|\bREF\b|\bCREDITED BACK\b", re.I)
UPI_RE = re.compile(r"\bUPI\b|\bIPAY\b|\bSBIEPAY\b|\bPAYTM\b|\bPHONEPE\b|\bGOOGLEPAY\b|\bGPAY\b", re.I)
CARD_RE = re.compile(r"\bDEBIT CARD\b|\bCREDIT CARD\b|\bVISA\b|\bMASTER\b|\bPOS\b|\bDEBITCARD\b", re.I)
FUEL_RE = re.compile(r"\bBPCL\b|\bIOCL\b|\bHPCL\b|\bPETROL\b|\bFUEL\b|\bPETROL PUMP\b", re.I)
UPI_MERCHANT_KEYWORDS = re.compile(r'UPI/|IPAY/|SBIEPAY|PAYTM|PHONEPE|GOOGLEPAY|GPAY', re.I)

# tuneable thresholds
MIN_SIM_FOR_CONFIDENT = 0.50   # become "trusted" starting here
LOWER_SIM_FOR_PENDING = 0.42   # below this -> try heuristics
HIGH_CONF_SIM = 0.80

# ----------------------------
# Strong rule overrides
# ----------------------------
def _apply_rule_overrides(text_norm: str) -> Optional[Tuple[str, str, float, str]]:
    """
    Return (category, subcategory, confidence, rule_name) for a matched strong rule,
    or None if no rule matched.
    """
    if SALARY_RE.search(text_norm):
        return "Income", "Salary", 0.99, "salary_rule"
    if EMI_RE.search(text_norm):
        return "Debt", "LoanEMI", 0.96, "emi_rule"
    if ATM_WDR_RE.search(text_norm):
        return "Cash", "ATMWithdrawal", 0.88, "atm_wdr_rule"
    if ATM_DEP_RE.search(text_norm):
        return "Cash", "ATMDeposit", 0.85, "atm_dep_rule"
    if INT_PD_RE.search(text_norm):
        return "Income", "Interest", 0.93, "interest_rule"
    if QTR_CHG_RE.search(text_norm):
        return "BankCharges", "BalanceCharge", 0.85, "qtr_charge_rule"
    if SMS_CHG_RE.search(text_norm):
        return "BankCharges", "SMS", 0.82, "sms_charge_rule"
    if ELEC_RE.search(text_norm):
        return "Utilities", "Electricity", 0.92, "electricity_rule"
    if GAS_RE.search(text_norm):
        return "Utilities", "Gas", 0.90, "gas_rule"
    if INS_RE.search(text_norm):
        return "Insurance", "GovtScheme", 0.90, "govt_insurance_rule"
    if REFUND_RE.search(text_norm):
        return "Transfers", "Refund", 0.86, "refund_rule"
    if NEFT_IMPS_RE.search(text_norm):
        return "Transfers", "BankTransfer", 0.88, "bank_transfer_rule"
    if FUEL_RE.search(text_norm):
        return "Transport", "Fuel", 0.88, "fuel_rule"
    if CARD_RE.search(text_norm) and FUEL_RE.search(text_norm):
        return "Transport", "Fuel", 0.88, "card_fuel_rule"
    # bank fee patterns
    if re.search(r'ANNUAL.*CARD.*FEE|ANNUAL CARD FEE|BANK CHARGES|SERVICE CHARGE|MAINTENANCE CHARGE', text_norm, re.I):
        return "BankCharges", "Fees", 0.86, "bank_fee_rule"
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

    # If taxonomy is tiny, add a few common phrases to improve prototypes
    if len(phrases) < 50:
        extra = [
            "Salary credit", "EMI payment", "ATM withdrawal", "UPI payment", "NEFT transfer",
            "Amazon purchase", "Zomato order", "Uber ride", "BPCL petrol", "Electricity bill"
        ]
        for p in extra:
            labels.append("Misc.Misc")
            phrases.append(p)

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
    Always safe: returns PENDING on unexpected errors.
    """
    global _MODEL, _LABELS, _EMBS
    try:
        if _MODEL is None:
            # allow single-process usage (lazy init)
            _worker_init()

        if not text or not text.strip():
            return "PENDING", 0.0, {"reason": "empty_text"}

        # normalize / clean text heavily (IDBI/ICICI logs are messy)
        text_norm = normalize_desc(text)

        # 1) Strong rule overrides (very high confidence)
        rule = _apply_rule_overrides(text_norm)
        if rule:
            cat, subcat, conf, rule_name = rule
            return f"{cat}.{subcat}", conf, {
                "source": "rule_override",
                "rule": rule_name,
                "normalized_text": text_norm,
            }

        # 2) Vendor biasing (exact token match)
        vendor_hit = None
        vendor_bias = None
        for key, val in VENDOR_CATEGORY_MAP.items():
            if key.upper() in text_norm:
                vendor_hit = key
                vendor_bias = val
                break

        # 3) Compute embedding and similarity to prototypes
        q_emb = _MODEL.encode([text_norm], convert_to_numpy=True, show_progress_bar=False)
        q_emb = _l2_normalize(q_emb)
        sims = np.dot(q_emb, _EMBS.T)[0]
        top_idx = sims.argsort()[::-1][:8]
        top = [(_LABELS[i], float(sims[i])) for i in top_idx]

        best_label, best_sim = top[0]
        second_sim = top[1][1] if len(top) > 1 else 0.0
        raw_conf = float(best_sim)

        # compute a margin-aware confidence
        margin = raw_conf - second_sim
        if raw_conf >= HIGH_CONF_SIM and margin > 0.03:
            confidence = 1.0
        elif raw_conf >= MIN_SIM_FOR_CONFIDENT:
            # scale between MIN_SIM_FOR_CONFIDENT and HIGH_CONF_SIM, boost by margin
            base = (raw_conf - MIN_SIM_FOR_CONFIDENT) / (HIGH_CONF_SIM - MIN_SIM_FOR_CONFIDENT)
            confidence = min(1.0, max(0.0, base + margin * 0.5))
        else:
            confidence = max(0.0, (raw_conf - LOWER_SIM_FOR_PENDING) / (MIN_SIM_FOR_CONFIDENT - LOWER_SIM_FOR_PENDING))

        # vendor bias strengthening: if vendor suggested category matches, raise confidence
        if vendor_bias:
            # vendor_bias like ("Shopping","Online")
            vb_combined = f"{vendor_bias[0]}.{vendor_bias[1]}"
            if vendor_bias[0] in best_label or vb_combined == best_label:
                confidence = max(confidence, 0.70)

        meta = {
            "source": "bert_similarity",
            "raw_conf": raw_conf,
            "margin": margin,
            "top_5": top[:5],
            "normalized_text": text_norm,
            "vendor_hit": vendor_hit,
            "vendor_bias": vendor_bias,
        }

        # 4) Low-similarity fallback: try heuristics classifier if available
        if raw_conf < MIN_SIM_FOR_CONFIDENT:
            if classify_with_heuristics:
                try:
                    h_cat, h_sub, h_conf, h_meta = classify_with_heuristics(text)
                    # heuristics returns category (string), subcategory, confidence float
                    if h_cat and h_cat != "PENDING":
                        # pick heuristic result with moderate confidence
                        return (
                            f"{h_cat}.{h_sub}" if h_sub else h_cat, 
                            max(confidence, min(0.9, h_conf)), 
                            {
                                "source": "heuristics_fallback",
                                "heuristics_meta": h_meta,
                                "normalized_text": text_norm,
                                "bert_top": top[:3],
                            }
                        )
                except Exception as heur_err:
                    # ignore heuristics failure, continue to PENDING below
                    meta["heuristics_error"] = str(heur_err)

            # If still low similarity, return PENDING with helpful meta for LLM stage
            return "PENDING", round(float(confidence), 3), meta

        # 5) If confidence computed is reasonable, return best_label
        return best_label, round(float(confidence), 3), meta

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