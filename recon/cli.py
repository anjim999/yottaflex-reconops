"""Command line: python -m recon <command> --scale starter|full --seed 20261022"""
import argparse
import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from . import db, metrics, reports
from .config import DEFAULT_SEED, SCALES
from .engine.run import reconcile
from .export import ddl, read_tables, seed_sql, write_manifest, write_tables
from .generate.pipeline import generate
from .validate import validate

ROOT = Path(__file__).resolve().parent.parent


def paths(base: Path) -> dict:
    return {k: base / k for k in ("input", "output", "ground_truth", "sql", "reports")}


def cmd_generate(scale, seed, base: Path, sql=True):
    if base.exists():
        shutil.rmtree(base)
    p = paths(base)
    r = generate(scale, seed)
    write_tables(r["tables"], p["input"])
    write_tables({"ground_truth": r["ground_truth"]}, p["ground_truth"])
    reports.write_json(base / "run_config.json", r["run_config"])
    if sql:
        p["sql"].mkdir(parents=True, exist_ok=True)
        (p["sql"] / "schema.sql").write_text(ddl(), encoding="utf-8", newline="\n")
    print(f"generated {scale} (seed {seed}) -> {base}")
    return r


def load_run(base: Path):
    p = paths(base)
    return read_tables(p["input"]), json.loads((base / "run_config.json").read_text())


def cmd_reconcile(base: Path):
    t, cfg = load_run(base)
    out = reconcile(t, cfg)
    write_tables(out, paths(base)["output"])
    x = out["exceptions"]
    print(f"reconciled: {len(out['reconciliation_matches'])} matches, {len(x)} exceptions "
          f"({(x.status == 'RESOLVED').sum()} resolved)")
    return out


def all_tables(base: Path) -> dict:
    p = paths(base)
    t = read_tables(p["input"])
    t.update(read_tables(p["output"]))
    return t


def cmd_validate(base: Path):
    t, cfg = all_tables(base), json.loads((base / "run_config.json").read_text())
    gt = read_tables(paths(base)["ground_truth"])["ground_truth"]
    v = validate(t, gt, cfg)
    rp = paths(base)["reports"]
    rp.mkdir(parents=True, exist_ok=True)
    v.to_csv(rp / "validation_summary.csv", index=False, lineterminator="\n")
    (rp / "validation_summary.md").write_text(reports.validation_md(v), encoding="utf-8", newline="\n")
    fails = v[v.status == "FAIL"]
    from .profile import profile, profile_md
    (rp / "data_profile.md").write_text(profile_md(profile(t)), encoding="utf-8", newline="\n")
    print(f"validation: {len(v)} checks, {len(fails)} failed")
    if len(fails):
        print(fails.to_string())
    return v


def idempotency(base: Path) -> dict:
    t, cfg = load_run(base)
    a, b = reconcile(t, cfg), reconcile(t, cfg)
    same_run = all(a[k].equals(b[k]) for k in a)
    t2 = dict(t)
    d = t["webhook_deliveries"]
    t2["webhook_deliveries"] = pd.concat([d, d.assign(delivery_id=d.delivery_id.str.replace("DLV", "DLX"))])
    c = reconcile(t2, cfg)
    key = lambda o: set(zip(o["exceptions"].exception_type, o["exceptions"].entity_id))
    non_dup = lambda o: {k for k in key(o) if k[0] != "DUPLICATE_WEBHOOK"}
    m_cols = ["match_level", "match_type", "status", "left_amount_minor", "right_amount_minor"]
    return {
        "same_input_twice_identical_output": bool(same_run),
        "replayed_full_webhook_feed_canonical_events_unchanged": bool(a["canonical_events"].event_id.equals(c["canonical_events"].event_id)),
        "replayed_feed_matches_unchanged": bool(a["reconciliation_matches"][m_cols].equals(c["reconciliation_matches"][m_cols])),
        "replayed_feed_non_duplicate_exceptions_unchanged": non_dup(a) == non_dup(c),
        "replayed_feed_extra_duplicates_flagged": int((c["exceptions"].exception_type == "DUPLICATE_WEBHOOK").sum()
                                                      - (a["exceptions"].exception_type == "DUPLICATE_WEBHOOK").sum()),
    }


def cmd_evaluate(base: Path):
    t = all_tables(base)
    gt = read_tables(paths(base)["ground_truth"])["ground_truth"]
    out = {k: t[k] for k in ("reconciliation_matches", "match_items", "exceptions", "resolutions", "item_status")}
    scores, decisions, kpi = metrics.detection_scores(t["exceptions"], gt), metrics.decision_accuracy(out, gt), metrics.kpis(t, out)
    idem = idempotency(base)
    rp = paths(base)["reports"]
    reports.write_json(rp / "metrics.json", {"detection": scores.to_dict("records"),
                                             "normal_case_decisions": decisions.to_dict("records"),
                                             "idempotency": idem, "kpis": kpi})
    (rp / "metrics.md").write_text(reports.metrics_md(scores, decisions, kpi, idem), encoding="utf-8", newline="\n")
    tot = scores.iloc[-1]
    print(f"detection: precision {tot.precision}, recall {tot.recall}, f1 {tot.f1}; idempotency {idem}")
    return scores, decisions, kpi, idem


def cmd_sql(base: Path):
    t = all_tables(base)
    (paths(base)["sql"] / "seed.sql").write_text(seed_sql(t), encoding="utf-8", newline="\n")
    print("wrote sql/seed.sql")


def cmd_load(base: Path):
    target = db.load(all_tables(base), base / "recon.sqlite")
    print(f"loaded into {target}")


def cmd_reproduce(scale, seed, base: Path):
    sums = []
    for i in (1, 2):
        d = Path(tempfile.mkdtemp(prefix=f"recon_repro{i}_"))
        cmd_generate(scale, seed, d)
        cmd_reconcile(d)
        m = write_manifest(d, json.loads((d / "run_config.json").read_text()), "reproduce")
        sums.append({f["path"]: (f["rows"], f["sha256"]) for f in m["files"]})
        shutil.rmtree(d)
    diff = sorted(k for k in sums[0].keys() | sums[1].keys() if sums[0].get(k) != sums[1].get(k))
    report = {"scale": scale, "seed": seed, "runs": 2, "files_compared": len(sums[0]), "identical": not diff,
              "differences": diff,
              "files": [{"path": k, "rows": v[0], "sha256_run1": v[1], "sha256_run2": sums[1].get(k, (None, None))[1]}
                        for k, v in sorted(sums[0].items())]}
    reports.write_json(paths(base)["reports"] / "reproducibility_report.json", report)
    print(f"reproducibility: {len(sums[0])} files compared, identical={not diff}")
    return report


def main(argv=None):
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser(prog="recon", description="Payment reconciliation: generate, reconcile, validate, evaluate")
    ap.add_argument("command", choices=["all", "generate", "reconcile", "validate", "evaluate", "sql", "load-db", "reproduce", "docs"])
    ap.add_argument("--scale", choices=list(SCALES), default="starter")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--out", type=Path, default=None, help="dataset folder (default data/<scale>)")
    ap.add_argument("--skip-repro", action="store_true", help="'all' without the double-generation check")
    a = ap.parse_args(argv)
    base = a.out or ROOT / "data" / a.scale
    cmd = f"python -m recon {a.command} --scale {a.scale} --seed {a.seed}"

    if a.command in ("all", "docs"):
        from . import docs
        docs.write(ROOT)
        print("wrote docs/data_dictionary.md")
    if a.command == "docs":
        return
    if a.command in ("all", "generate"):
        cmd_generate(a.scale, a.seed, base)
    if a.command in ("all", "reconcile"):
        cmd_reconcile(base)
    if a.command in ("all", "validate"):
        cmd_validate(base)
    if a.command in ("all", "evaluate"):
        cmd_evaluate(base)
    if a.command in ("all", "sql"):
        cmd_sql(base)
    if a.command in ("all", "load-db"):
        cmd_load(base)
    if a.command == "reproduce" or (a.command == "all" and not a.skip_repro):
        cmd_reproduce(a.scale, a.seed, base)
    if a.command in ("all", "generate", "reconcile", "sql"):
        write_manifest(base, json.loads((base / "run_config.json").read_text()), cmd)


if __name__ == "__main__":
    main()
