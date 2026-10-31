"""Print v1-r3 design / evaluation / extension tables (0.1 lot per rule, THB)."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"


def r(x):
    return f"{x:+,.0f}" if isinstance(x, (int, float)) else str(x)


def main():
    if (OUT / "STAGE1_2010_2016.json").exists():
        s1 = json.loads((OUT / "STAGE1_2010_2016.json").read_text())
        print("STAGE 1 (2010-16 vs v1-r2):")
        for row in s1:
            m = row["metrics"]
            print(f"  {row['rule']} {row['family']:4s} {str(row['variant']):11s} net {m['net']:>10,.0f} dd {m['dd']:>8,.0f} "
                  f"trades {m['trades']:>5} t {row['t_diff']:+.2f} blocked {row['blocked']:>4} {'PICKABLE' if row['eligible_pick'] else ''}")
    for name in ("NULL_2010_2016.json", "DIAGNOSTICS_2010_2016.json"):
        if (OUT / name).exists():
            print(name, json.dumps(json.loads((OUT / name).read_text()), indent=1)[:4000])
    if (OUT / "LOCK.json").exists():
        lk = json.loads((OUT / "LOCK.json").read_text())
        print("LOCK", lk["status"], json.dumps(lk["filters"]), "picks", lk["stage1_picks"], "kept", lk["kept_after_null"])
        print("  train", {k: round(lk["training_metrics"][k]) for k in ("net", "dd", "trades", "recent")},
              "base", {k: round(lk["base_training_metrics"][k]) for k in ("net", "dd", "trades", "recent")})
    if (OUT / "EVALUATION.json").exists():
        ev = json.loads((OUT / "EVALUATION.json").read_text())
        print("VERDICT", ev["status"])
        for period in ("validation", "full"):
            for sc in ("fixed", "cost_example", "historical"):
                x = ev["results"][period][sc]
                a, b = x["v1-r2"], x["v1-r3"]
                print(f"  {period:10s} {sc:12s} v1-r2 {a['net']:>10,.0f} / {a['dd']:>8,.0f} ({a['trades']})  "
                      f"v1-r3 {b['net']:>10,.0f} / {b['dd']:>8,.0f} ({b['trades']})  t {x['t_diff']:+.2f}")
        x = ev["results"]["validation"]["fixed"]
        print("  LOO 2017-19:", {k: round(v) for k, v in x["leave_one_out_net_contribution"].items()})
        print("  stop theta ratio:", json.dumps(x["stop_theta_ratio"]))
    if (OUT / "EXTEND_2010_2022.json").exists():
        ex = json.loads((OUT / "EXTEND_2010_2022.json").read_text())
        for name in ("v1-r2", "v1-r3"):
            m = ex[name]["metrics"]
            print(name, "2010-22 net", r(m["net"]), "dd", round(m["dd"]), f"({m['dd_pct']:.2f}%)", "trades", m["trades"],
                  "lowest", round(m["lowest"]), "worst", round(m["worst"]), "by_rule", ex[name]["by_rule"])
        print("t_diff 2010-22", ex.get("t_diff_2010_2022"))
        print("year | v1-r2 net | v1-r3 net | v1-r3 wins | v1-r3 losses | v1-r3 end | dd r2 | dd r3 | trades r2/r3")
        for y in ex["v1-r3"]["yearly"]:
            a, b = ex["v1-r2"]["yearly"][y], ex["v1-r3"]["yearly"][y]
            print(y, r(a["net"]), r(b["net"]), r(b["wins"]), r(b["losses"]), f"{b['end']:,.0f}", round(a["dd"]), round(b["dd"]),
                  f"{a['trades']}/{b['trades']}")
        for name in ("v1-r2", "v1-r3"):
            print(name, "sessions", json.dumps({k: (v["trades"], round(v["win"], 3), round(v["net"])) for k, v in ex[name]["sessions"].items()}))


if __name__ == "__main__":
    main()
