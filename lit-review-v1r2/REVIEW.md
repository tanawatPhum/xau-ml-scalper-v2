# Literature review for improving v1-r2 (Consensus deep + Scite, 1 Nov 2026)

Owner (00:10 ICT): search Consensus and Scite in depth for research that could improve our swing strategy.

**Sources**
- **Consensus deep research thread:** 100 papers included out of 520 eligible; 62 are cited. https://consensus.app/search/i-run-a-short-horizon-counter-trend-mean-reversion/cVpRXjrpQ-agqN31E7j2HA/ The full report is at that link, and it was also sent in chat on 1 Nov 2026 as `CONSENSUS_DEEP_REPORT.md`.
- **Scite:** about 35 papers checked for title, DOI, Smart Citation tally and editorial notices. None of the papers used here has a retraction, concern or correction notice.
- **Not a repeat:** ideas already tested in this sandbox are excluded. That covers leg/bounce duration, σ60/σ1440, session, higher-scale swing, range position, three-leg patterns, volume and spread at the bounce, entry delays, stop multiples, TP extension and range TP, volatility sizing, the daily brake, the equity-curve filter, timeframes, ML, and rule C rounds 1-2.

## Correction (1 Nov 2026, 01:10 ICT)
The Consensus brief and sections 1-4 below described the entry direction backwards.

**What the strategy actually does.** The engine trades side = -(event direction).
- After a leg of at least L·θ and a θ counter-move, it enters in the direction of the prior leg. It fades the pullback; for example, it buys the dip after an up-leg.
- Profit is capped near +θ.
- The 2.5θ stop is hit when the pullback grows into a full reversal of the leg.

**Consequences for the findings below:**
- **Unchanged:**
  - deadline admission;
  - seasonal / jump-robust θ;
  - the volatility-surprise skip, because trending after a surprise hurts a pullback fade;
  - GVZ, since the trade still provides liquidity, now to the pullback;
  - flight to gold, defined by side: no short-gold trades after S&P drops.
- **Flipped or ambiguous:**
  - Moves driven by news continue, which is good for this trade. Jumps with no news reverse, which is bad.
  - Overreaction of large moves describes our stop-outs, not our edge.
  - Round numbers: a rejection at a round level threatens a pullback fade, while a clean break supports it.
- **Settlement window:** block trades whose side is against the day's move.

v1-r3's PLAN tests the ambiguous items in both directions. A corrected follow-up brief was sent to the same Consensus thread.

## What the evidence says, as it bears on v1-r2

**1. Reversal after large intraday moves is real but conditional.**
- **Precious metals overreact intraday more than other commodities** (Borgards et al. 2021).
  - Data: 20 futures at 1 minute to 1 hour, Nov 2019 to Jun 2020.
  - A 1-hour contrarian rule on the precious-metals index made +21.8% / +18.0%. It assumes 20% of the reversal range is captured and charges no costs.
- **Reversal profits rise with volatility.** Returns to liquidity provision grow with volatility (Nagel 2012). Higher volatility gives faster, initially stronger reversals (Dai, Medhat & Novy-Marx 2023).
  - This fits our finding that trades with larger θ$ earn more per unit of risk.
  - So de-risking when volatility is high (Moreira & Muir 2017) is the wrong direction for this strategy.
- **Moves with information continue; moves without information revert** (Chan 2003; Dyl, Yuksel & Zaynutdinova 2019; Baule & Tallau 2016).
  - Gold absorbs US macro news within about 90 seconds (Smales 2015).
  - The 08:30 ET releases dominate, especially payrolls and durable goods (Elder, Miao & Ramchander 2011).
- **But jumps are not the same as news.**
  - Jumps with no news reverse for at least 60 minutes, and negative jumps reverse more (Xiao, Yin & Zhao 2020, equity ETFs).
  - Only 1.5% of GLD jumps coincide with listed US releases (Jurdi 2020). About a third of futures jumps do (Evans 2011).
  - Extreme moves without news are common under price-contingent trading (Osler & Savaşer 2011).
- **Market intraday momentum.** The return in the last 30 minutes before the futures close is predicted by the day's return so far, driven by short-gamma hedging (Baltussen, Da & Lammers 2021).
  - Data: 60+ futures.
  - The effect is weaker in commodities, and gold on its own is not reported.
  - Gold shows same-day momentum on abnormal-return days (Caporale & Plastun 2021).

**2. Directional change (DC) and intrinsic time**
- **The average overshoot is about the size of the DC threshold** (E ≈ 1.04; Glattfelder, Dupuis & Olsen 2011).
  - A plain "enter at DC, exit at the next DC" rule therefore earns about zero gross.
  - Our edge has to come from requiring a leg of at least 2.5θ first. The XAU scaling constants have not been published.
- **Published DC strategies are weak evidence for us.**
  - Most leave out costs or slippage (Bakhach et al. 2016, 2018).
  - Others are GP/ML-optimised (Kampouridis & Otero 2017; Adegboye, Kampouridis & Otero 2023, the latter with 0.025% cost).
  - The Alpha Engine (Golub, Glattfelder & Olsen 2018) has no stop and adds to losing positions. Its performance figures are only reported second-hand.
- **Fill prices matter.** Theoretical versus actual DC confirmation prices can distort results (Ao & Li 2023). Our engine already fills at the next 1-minute close.

**3. Measuring volatility for θ**
- **A raw rolling σ is biased:**
  - by the time-of-day volatility pattern (Andersen & Bollerslev 1997);
  - by jumps (Boudt, Croux & Laurent 2011);
  - by the small sample: σ from 60 adjacent returns is biased down (Dette, Golosnoy & Kellermann 2022).
- **The intraday pattern moves with the volatility level** (Andersen, Thyrsgaard & Todorov 2019).
- **HAR-type blends** of 1-hour, 1-day and 1-week volatility forecast better than single windows (Corsi 2009).
- **Unexpected volatility goes with positive intraday serial correlation**, that is, trending (Bianco, Corsi & Renò 2008, S&P 500). In plain terms, fades should fail when volatility surprises upward. v1-r1's B filter (σ60/σ1440 ≤ 1.5) is a crude version of this.

**4. Round numbers**
- **FX orders cluster around round numbers** (Osler 2003, 2005).
  - Take-profit orders cluster at round numbers, which helps reversals.
  - Stop-loss orders cluster just beyond them; crossing sets off cascades that stay significant for hours.
- **Gold evidence is weaker.**
  - Barriers exist at the 100s, and at prices ending in 0 and 00 (Aggarwal & Lucey 2007; Lucey & O'Connor 2016).
  - This is mainly in daily data, mostly as effects on variance rather than direction, and weaker intraday.

**5. Exits and stops**
- **Stops cut expected return unless prices trend** (Kaminski & Lo 2014).
- **No stop and no take-profit was the best combination** in a cost-aware 2014-24 reversal study (Turquet, Bajgrowicz & Scaillet 2025).
- **Stop and take-profit levels must be set together** (Leung & Li 2015).
- **Deadlines change optimal entry timing** (Kitapbayev & Leung 2018).
- All of this is consistent with our ext-stop result that tighter stops lose.

**6. Regime filters**
- An estimated Hurst exponent or variance-ratio inefficiency does not imply tradable predictability (Pernagallo 2025; Brouty & Garcin 2024).
- Daily gold efficiency findings are mixed (Ntim et al. 2015; Shahid, Jehanzeb & Abbas 2019).
- Priority: low.

## Ranked experiments: price-only, base = v1-r2

| # | Idea | Rule to test | Loss bucket it targets | Evidence | Free params |
|---|---|---|---|---|---|
| 1 | Deadline admission and settlement window | (a) No new entry within N ∈ {15, 30, 60} min before the 16:55 NY flatten (and holiday early closes). (b) No fade of a leg that runs with the day's move during 13:00-13:30 NY (COMEX settlement). | Forced exits: 758 trades, average -556 THB, total -421k THB in 2010-22 at 0.1 lot. Late-day momentum. | Kitapbayev & Leung 2018; Baltussen et al. 2021; Caporale & Plastun 2021; rule C round 2 (fading into scheduled times, including 13:30 NY, did not pay) | 1 + 0 |
| 2 | Jump-concentration filter | J = max r² / Σ r² over the leg's 1-min returns, and a Lee-Mykland-type max \|r\| / local bipower σ. Skip the top quintile, with cut-offs from the prior 60 days only. Report up-legs and down-legs separately. | Stop-outs where the move continued (wrong direction) | Lee & Mykland 2008; Barndorff-Nielsen & Shephard 2006; Chan 2003; Smales 2015; Nagel 2012. Against: Xiao et al. 2020; Jurdi 2020 | 1 |
| 3 | Seasonal, jump-robust θ plus a volatility-surprise skip | σ from deseasonalised 1-min returns, using 15-min time-of-week bins from the prior 60 days, rescaled to the current bin (bipower variant). Skip when σ60 / expected σ for the bin > q. This could replace the per-session overrides with one rule. | Mis-scaled θ around session transitions; trending under volatility shocks | Andersen & Bollerslev 1997; Boudt et al. 2011; Andersen et al. 2019; Dette et al. 2022; Corsi 2009; Bianco, Corsi & Renò 2008 | 1-2 |
| 4 | Round-number rejection vs. break | Tag legs whose extreme crossed a $10 (and $50) level by ≤ 0.5θ and came back (rejection), versus crossings by more (break). Skip fades after breaks. | Continuation after stop cascades | Osler 2003, 2005; Aggarwal & Lucey 2007; Lucey & O'Connor 2016. Intraday gold evidence is weak. | 1 |
| 5 | Time exit by volatility state | Exit at T ∈ {15, 30, 60} min if no swing exit has happened, with shorter T in high σ. | Long losing holds | Dai et al. 2023; Zawadowski, Kertész & Andor 2004 (overreaction plays out in 10-30 min). Risk: it acts like a tighter stop, which lost before. | 1-2 |

**Diagnostic (no selection):** measure θ at exit against θ at entry for stop-outs. Our θ is recomputed every minute, so an adverse volatility burst widens the exit threshold and lets the loss run to the 2.5θ stop. The DC literature uses a fixed threshold.

## Needs new data (owner approval)
- **Economic calendar:** block entries from 5 min before to 15 min after NFP, CPI, GDP and FOMC (Elder et al. 2011; Cai, Cheung & Wong 2001; Smales 2015; Awartani, Hussain & Virk 2024). Expected to cut tail losses; the effect on net is unclear because announcement reversals also exist.
- **GVZ (gold implied volatility):** stratify trades by lagged GVZ (Nagel 2012; Xu, Bouri & Saeed 2020).
- **S&P 500 intraday:** no short-gold fades after extreme 5-min equity drops, which trigger the flight to gold (Baur & Kuck 2020).

## Not worth testing now
- Hurst / variance-ratio gates.
- OU-optimal thresholds: outright gold is not a stationary spread.
- GP/ML DC strategies: ML is parked by the owner.
- Alpha-Engine-style averaging down with no stop.
- Volatility-managed (de-risking) sizing.
- A dynamic cost ratio: already covered by the θ$ floor, and the Exness spread is fixed in our model.

## Protocol for v1-r3
- Same as v1-r2:
  - plan written before outcomes;
  - select on 2010-16 and lock;
  - check on 2017-19, with PASS only if net AND DD both beat v1-r2 at the fixed spread;
  - 2020-22 descriptive.
- 2017-19 has been reused many times and has only about 300 trades. Run the top 2-3 ideas as one pre-registered batch with a multiple-testing ledger, rather than one round per idea.
- A clean final check needs unseen data: 2023-26, which is locked, or a forward demo.

## References (DOIs)
- Andersen & Bollerslev (1997) J. Empirical Finance, 10.1016/s0927-5398(97)00004-2
- Andersen, Thyrsgaard & Todorov (2019) JASA, 10.1080/01621459.2018.1512864
- Aggarwal & Lucey (2007) Rev. Financial Econ., 10.1016/j.rfe.2006.04.001
- Ao & Li (2023) Finance Res. Letters, 10.1016/j.frl.2023.104936
- Awartani, Hussain & Virk (2024) IRFA, 10.1016/j.irfa.2024.103486
- Adegboye, Kampouridis & Otero (2023) Artif. Intell. Review, 10.1007/s10462-022-10307-0
- Bakhach, Chinthalapati & Tsang (2018) Algorithms, 10.3390/a11110171
- Bakhach, Tsang & Ng (2016) IEEE SSCI, 10.1109/ssci.2016.7850004
- Baltussen, Da & Lammers (2021) JFE, 10.1016/j.jfineco.2021.04.029
- Barndorff-Nielsen & Shephard (2006) J. Fin. Econometrics, 10.1093/jjfinec/nbi022
- Baule & Tallau (2016) Credit & Capital Markets, 10.3790/ccm.49.1.57
- Baur & Kuck (2020) Finance Res. Letters, 10.1016/j.frl.2019.05.005
- Bianco, Corsi & Renò (2008) arXiv, 10.48550/arxiv.0810.4912
- Borgards, Czudaj & Hoang (2021) Resources Policy, 10.1016/j.resourpol.2020.101966
- Boudt, Croux & Laurent (2011) J. Empirical Finance, 10.1016/j.jempfin.2010.11.005
- Brouty & Garcin (2024) Chaos Solitons Fractals, 10.1016/j.chaos.2024.114543
- Cai, Cheung & Wong (2001) J. Futures Markets, 10.1002/1096-9934(200103)21:3<257::aid-fut4>3.0.co;2-w
- Caporale & Plastun (2021) Fin. Markets & Portfolio Mgmt, 10.1007/s11408-021-00380-w
- Chan (2003) JFE, 10.1016/s0304-405x(03)00146-6
- Corsi (2009) J. Fin. Econometrics, 10.1093/jjfinec/nbp001
- Dai, Medhat & Novy-Marx (2023) Financial Analysts J., 10.1080/0015198x.2023.2292534
- Dette, Golosnoy & Kellermann (2022) Econometrics & Statistics, 10.1016/j.ecosta.2021.03.002
- Dyl, Yuksel & Zaynutdinova (2019) J. Business Research, 10.1016/j.jbusres.2018.08.036
- Elder, Miao & Ramchander (2011) J. Banking & Finance, 10.1016/j.jbankfin.2011.06.007
- Evans (2011) J. Banking & Finance, 10.1016/j.jbankfin.2011.02.018
- Glattfelder, Dupuis & Olsen (2011) Quantitative Finance, 10.1080/14697688.2010.481632
- Golub, Glattfelder & Olsen (2018) The Alpha Engine, 10.1201/9781315372006-3
- Jurdi (2020) JRFM, 10.3390/jrfm13060118
- Kaminski & Lo (2014) J. Financial Markets, 10.1016/j.finmar.2013.07.001
- Kampouridis & Otero (2017) Expert Syst. Appl., 10.1016/j.eswa.2016.12.032
- Kitapbayev & Leung (2018) IJTAF, 10.1142/s0219024918500048
- Lee & Mykland (2008) RFS, 10.1093/rfs/hhm056
- Leung & Li (2015) IJTAF, 10.1142/s021902491550020x
- Lucey & O'Connor (2016) Finance Res. Letters, 10.1016/j.frl.2016.03.009
- Moreira & Muir (2017) J. Finance, 10.1111/jofi.12513
- Nagel (2012) RFS, 10.1093/rfs/hhs066
- Ntim et al. (2015) IRFA, 10.1016/j.irfa.2015.03.013
- Osler (2003) J. Finance, 10.1111/1540-6261.00588
- Osler (2005) J. Int. Money & Finance, 10.1016/j.jimonfin.2004.12.002
- Osler & Savaşer (2011) J. Banking & Finance, 10.1016/j.jbankfin.2011.03.016
- Pernagallo (2025) Quality & Quantity, 10.1007/s11135-025-02052-7
- Shahid, Jehanzeb & Abbas (2019) Int. J. Emerging Markets, 10.1108/ijoem-07-2018-0404
- Smales (2015) IRFA, 10.1016/j.irfa.2015.01.017
- Turquet, Bajgrowicz & Scaillet (2025) Energy Economics, ETH repository 10.3929/ethz-b-000743880
- Xiao, Yin & Zhao (2020) J. Financial Research, 10.1111/jfir.12223
- Xu, Bouri & Saeed (2020) Resources Policy, 10.1016/j.resourpol.2020.101830
- Zawadowski, Kertész & Andor (2004) Physica A, 10.1016/j.physa.2004.06.121
