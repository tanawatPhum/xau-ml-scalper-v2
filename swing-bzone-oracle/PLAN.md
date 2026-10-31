# SELL on the bounce after a zone-to-zone run down: find the ratios on 2011-16, lock, test 2017-19
(v2, written before any run; supersedes v1 fixed-dollar oracle, which never ran)

Owner 17:36-17:41 ICT, 31 Oct: price runs from one B zone toward another, bounces a little, then
pushes on - the bounce is the entry; zone touches need not be exact. The owner's drawings show the
idea only; Claude must find the ratios and the factors. SELL side first. Examples (2017, outside
the search years): 01-18 / 01-20 / 01-24 London wins, 01-23 London loss (back up to the upper zone).

Years: 2011-2016 = answer key (search the ratios, see everything); 2017-2019 = blind test, run once
with the locked choice; 2020+ untouched.

## Data and units
E68 A2 ISSUED sessions, window [lock, lock+240); delivered zones (4, $0.50 wide). Dukascopy BID
1-minute high/low/close. Unit u = sigma60 in dollars = close x sqrt(60 x mean of the last 60
squared 1-minute log returns), from closes strictly before the minute (>= 30 returns; 120-minute
prefix before lock). Every distance is a ratio: of u, or of the run P - T.

## Tradable state machine (no hindsight), one position at a time per session
1. Peak: running max high H*. Confirmed when a later bar's low <= H* - rho*u (that bar not making a
   new high). P = H*; trough T = running min low since then.
2. While waiting: a bar with high > P cancels the setup (new peak candidate). Otherwise, the bar
   fills a SELL when run = P - T (T through the previous bar) >= m*u_P and high >= T + r*run, and
   the bar makes no new low. Fill price = max(level, previous close).
3. After fill: TP = T + q*run (q = 0 is a re-test of the trough, q < 0 a new low); SL = P + s*run.
   High >= SL is a loss (the fill bar counts; a bar that does both is a loss); low <= TP is a win;
   session end closes at the last close. Then the machine restarts after the exit bar.
4. Net = (fill - exit) - $0.168. Random-walk baseline per trade: p0 = (SL - X) / (SL - TP);
   expected gross 0.

Grid (180 cells): rho {0.5, 1.0}; m {1.5, 2.5, 4}; r {0.236, 0.382, 0.5, 0.618};
q {0.25, 0, -0.25, -0.5} (q < r only); s {0, 0.25}. Day = broker day (UTC+3) for clustering.

## Selection on 2011-2016 (automatic, written to out/LOCK.json before 2017-19 is touched)
- Cell: highest day-clustered t of net among cells with n >= 300 in 2011-16.
- Multiplicity: rerun the whole grid on 5 bar-permuted copies (each session's bars - high, low,
  close relative to the previous close - shuffled; zones fixed). Report where the real best t sits
  against the null best t.
- Factors, pre-listed, all known at the fill: zone Z (P within [A.lower - 0.5, A.upper + 0.5] for
  a zone A, T <= B.upper + 0.5 for a zone B below A); run size in u (terciles); run speed (u per
  minute, terciles); bounce time T to fill (terciles); session (asia / london / new_york).
  A factor is kept as a filter only if, inside the chosen cell, the better group beats the rest
  with t >= 2 over 2011-16 and has the same sign in 2011-13 and 2014-16. At most 2 filters.
- If no cell reaches t >= 2 or the real best t is not above every null best t: report "no edge
  found" and still lock the best cell for a descriptive 2017-19 check.

## Blind test 2017-2019 (once)
Locked cell + filters. Pass = net > 0 with day-clustered t >= 2 over 2017-19 and at least 2 of 3
years positive. Money: 0.1 lot, at the time's price, USD/THB 33.77; trades per day; max DD.
