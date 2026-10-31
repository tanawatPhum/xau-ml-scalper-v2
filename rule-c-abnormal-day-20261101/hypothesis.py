"""One fixed prior-abnormal-day hypothesis; daily aggregates finalize only on date transition."""
import numpy as np

SPEC=dict(id='C_prior_abnormal_day',paper_doi='10.1007/s11408-021-00380-w',
          timezone='UTC+03:00',reference_valid_days=60,z_threshold=2.,minimum_daily_quotes=1000,
          first_minute_max=120,last_minute_min=1320,expiry_minute=360,minimum_scale=.5,
          direction='opposite previous calendar day return',stop='disabled',target='disabled')

def signals(c, history=None):
    """history is feature-only completed days from 2016 for fresh 2017 validation.

    A daily return is not admitted to the history until a later calendar date is
    actually observed. Candidate date must have the immediately preceding date
    in the valid-day set. Current-day future quote count never gates an entry.
    """
    mins=np.asarray(c['mins'],np.int64);mid=np.asarray(c['mid'],float);n=len(mins)
    side=np.zeros(n,np.int8);scale=np.zeros(n);expiry=np.zeros(n,np.int64);zvalues=np.zeros(n)
    counts=dict(completed_observed_days=0,valid_days=0,invalid_quote_count=0,
                invalid_start_coverage=0,invalid_end_coverage=0,missing_calendar_days=0,
                previous_date_invalid_or_missing=0,warmup_under_60=0,zero_reference_sd=0,
                nonabnormal_days=0,no_eligible_quote_before_06=0,invalid_signal_scale=0,
                signals=0,unfinalized_last_day=1 if n else 0,history_days=len(history or []))
    records=list(history or []);previous=None
    if not n:return dict(side=side,scale=scale,expiry=expiry,z=zvalues,counts=counts,completed_days=records)
    days=(mins+180)//1440;mods=(mins+180)%1440
    starts=np.r_[0,np.flatnonzero(days[1:]!=days[:-1])+1];ends=np.r_[starts[1:],n]
    for a,b in zip(starts,ends):
        a=int(a);b=int(b);current=int(days[a]);prior_z=None;prior_r=None
        if previous is not None:
            pa,pb=previous;pd=int(days[pa]);cnt=pb-pa
            counts['completed_observed_days']+=1
            counts['missing_calendar_days']+=max(0,current-pd-1)
            badcount=cnt<1000;badstart=mods[pa]>120;badend=mods[pb-1]<1320
            counts['invalid_quote_count']+=int(badcount)
            counts['invalid_start_coverage']+=int(badstart)
            counts['invalid_end_coverage']+=int(badend)
            if not (badcount or badstart or badend):
                r=float(np.log(mid[pb-1]/mid[pa]));counts['valid_days']+=1
                records.append(dict(day=pd,r=r,quotes=cnt,first_minute=int(mods[pa]),last_minute=int(mods[pb-1])))
        # The reference explicitly excludes current-1, even though it has now finalized.
        prev=[r for r in records if r['day']==current-1]
        ref=[r['r'] for r in records if r['day']<current-1][-60:]
        if not prev:counts['previous_date_invalid_or_missing']+=1
        elif len(ref)<60:counts['warmup_under_60']+=1
        else:
            sd=float(np.std(ref,ddof=1));prior_r=prev[-1]['r']
            if not np.isfinite(sd) or sd<=0:counts['zero_reference_sd']+=1
            else:
                prior_z=(prior_r-float(np.mean(ref)))/sd
                if abs(prior_z)<=2 or prior_r==0:counts['nonabnormal_days']+=1;prior_z=None
        if prior_z is not None:
            eligible=np.flatnonzero((mods[a:b]<360)&~c['calendar'].blocked[a:b]&(mins[a:b]<c['calendar'].deadline[a:b]))
            if not len(eligible):counts['no_eligible_quote_before_06']+=1
            else:
                i=a+int(eligible[0]);eff=float(c['eff'][i])
                if not np.isfinite(eff) or eff<=0:counts['invalid_signal_scale']+=1
                else:
                    side[i]=-1 if prior_r>0 else 1
                    scale[i]=max(eff*mid[i]/10000.,.5)
                    expiry[i]=current*1440+360-180;zvalues[i]=prior_z;counts['signals']+=1
        previous=(a,b)
    return dict(side=side,scale=scale,expiry=expiry,z=zvalues,counts=counts,completed_days=records)
