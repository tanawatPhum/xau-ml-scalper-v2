# Rules A + B: cut the trade when the bounce extends too far (written before outcomes)

Owner 20:06 ICT, 31 Oct: "ทดสอบทางที่ 1" = a stop based on how far the bounce extends after the
entry (the earlier "tight SL ~0.5 theta" stays parked; this tests 1-2.5 theta).
Reason (swing-entry-timing): the bounce's mean remaining extension grows with how far it has gone
(A 0.91 -> 1.29 theta, B 1.06 -> 2.10), so a bounce that extends tends to keep going.

## Base (unchanged except the stop)
Locked portfolio: A (theta = 1 x max(sigma60, sigma1440)) only when theta >= $2.16; B (theta =
1.5 x sigma60) only when the leg >= 3.5 theta. Immediate entry, exit at the next swing
confirmation + 1 minute, base stop 3 theta from the entry at a minute close. 0.1 lot per rule,
mid at the time, $0.168 per trade, 33.77 THB/USD.

## Variants (per rule)
Stop at s x theta from the entry, checked at minute closes (as the base), exit at that close:
s {1.0, 1.25, 1.5, 2.0, 2.5} (base = 3.0). 5 cells per rule.
Sensitivity for the chosen s only: the stop checked on the minute's mid high/low and filled at
the stop level (a resting stop order).

## Selection (2010-2016 only), as in swing-entry-timing
Paired gain per signal (variant P&L - base P&L), day-clustered t, total in THB. Candidate: t >= 2
and gain > 0 in both 2010-13 and 2014-16. Family-wise null: 500 day sign flips over the 5 cells.
Per rule pick the candidate with the largest total gain; none = keep 3 theta. out/LOCK.json.

## Check 2017-2019 (once)
Per rule: PASS = total gain > 0 with t >= 2 and gain > 0 in >= 2 of 3 years; PARTIAL = gain > 0
in total and in 2 of 3 years, t < 2; else FAIL. A + B money table 2010-19 from 100,000 THB:
end capital, max DD, stop rate, average win / loss. 2020-22 sealed; 2023+ closed.
