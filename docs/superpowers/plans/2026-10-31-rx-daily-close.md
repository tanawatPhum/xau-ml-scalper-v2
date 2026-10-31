# RX Daily Close Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement causal scheduled exits and re-tune RX against the same daily-flat baseline.
**Architecture:** New daily revision imports immutable price/signal helpers and
adds an independent timestamp-only calendar and scheduled replay. Freeze the
training selection before evaluating the reused validation period.
**Tech Stack:** Existing Python, NumPy, pandas, Numba, pytest; no new dependency.
**Spec:** v1-rx/daily/DESIGN.md

## Global constraints
Design2010-2016; evaluate2010-2019; no2020+price access.0.1lot per rule,
100kTHB, FX33.77, fixed.168spread. Preserve oldlocks/source files. No future-gap
or dataset-end closures. Calendar safety parameters are not tuned for profit.

## Review focus
- Missing cutoff quote: delayed real fill plus explicit violation count.
- Holiday session starts previous evening: no position opened in blackout.
- DST/weekend and dataset truncation: past behavior remains identical.
- Stale pending entry at scheduled close: cancel, never reopen during closure.
- Selection/validation source or data changes: reject before comparison.

## Tasks
- [x] Calendar: failing boundary/prefix tests, timestamp-only implementation,
      green tests and deterministic manifest.
- [x] Execution: failing scheduled/missing-quote/EOF/cost tests, delayed replay,
      green tests and actual2010prefix comparison.
- [x] Study: selection/lock tests, bounded training, save immutablelock.
- [x] Evaluate full/validation and sensitivities, verify session violations and
      accounting, write annual report/plot and update current RX entrypoint/docs.
- [x] Fresh tests and final source/data/lock checks; report qualifications.

No Git repository exists; isolated new directory provides separation.
