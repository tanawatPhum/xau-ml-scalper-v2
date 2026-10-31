"""Report the immutable daily RX experiment without tuning or overwriting it."""
import json
import numpy as np
import pandas as pd
import run_study as d


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def f(x):return f'{x:,.0f}'
def sign(x):return f'{x:+,.0f}'


def main():
    lock=d.study.read_lock(d.OUT/'LOCK.json');ev=read(d.OUT/'EVALUATION.json')
    d.study.verify_hashes(lock['source_hashes'])
    assert read(d.OUT/'VERIFICATION.json')['status']=='PASS'
    selected=lock['selected'];m=ev['results']['full']['fixed'];val=ev['results']['validation']['fixed']
    names={'baseline':'v1 ปิดรายวัน','old_rx':'RX เดิม + ปิดรายวัน','rx':'RX ใหม่ D058'}
    reports={};extra={};curves={}
    for name in names:
        folder=d.OUT/'evaluation/full/fixed'/name
        rep=read(folder/'REPORT.json');reports[name]=rep
        t=pd.read_csv(folder/'TRADES.private.csv');p=t.net_thb.to_numpy()
        with np.load(folder/'EQUITY.private.npz',allow_pickle=False) as z:
            e=z['equity'];mins=z['t_minute']
        e5=100000+5*(e-100000);pk5=np.maximum.accumulate(np.r_[100000,e5])[1:]
        peak=np.maximum.accumulate(np.r_[100000,e])[1:]
        extra[name]=dict(profit_factor=float(p[p>0].sum()/-p[p<0].sum()),win_pct=float(100*(p>0).mean()),
            lot05=dict(net=float(e5[-1]-100000),end=float(e5[-1]),dd=float((pk5-e5).max()),
                       dd_pct=float((100*(pk5-e5)/pk5).max()),lowest=float(min(100000,e5.min()))))
        curves[name]=pd.DataFrame(dict(day=mins//1440,equity=e,dd=peak-e)).groupby('day').agg(equity=('equity','last'),dd=('dd','max'))
    d.study.write_json(d.OUT/'REPORT_EXTRAS.json',extra)
    b,o,r=[m[k] for k in names]
    lines=['# v1-rx รุ่นปิดรายวัน — ผลจูนและทดสอบ 2010–2019','',
    '**แก้การปิดสถานะแล้ว:** RX ใหม่มี 0 ไม้ข้ามเวลาปิดตลาด และ 0 ไม้ข้ามวันซื้อขาย จาก 2,802 ไม้ ตามตารางที่ประกาศไว้ก่อนทดสอบ ไม่มีการใช้ช่องว่างข้อมูลในอนาคตเพื่อย้อนปิดไม้', '',
    f'**ผลจูน:** เทียบ RX เดิมที่นำมาปิดรายวันเหมือนกัน กำไรเพิ่ม {100*(r["net"]/o["net"]-1):.2f}% และ Max DD ลด {100*(1-r["dd"]/o["dd"]):.2f}% แต่ขาดทุนรวมเฉพาะไม้แพ้เพิ่ม {100*(r["loss"]/o["loss"]-1):.2f}% และไม้ที่เสียหนักที่สุดแย่ลง จึงไม่ได้ดีขึ้นทุกมิติ', '',
    f'เทียบ v1 ภายใต้เวลา/ปฏิทินเดียวกัน กำไรลด {100*(1-r["net"]/b["net"]):.2f}% และ DD ลด {100*(1-r["dd"]/b["dd"]):.2f}% สถานะการเพิ่มกำไรพร้อมลดความเสี่ยงเหนือ v1 ในช่วงทดสอบยังเป็น **NOT_CONFIRMED**', '',
    '## ฐานเปรียบเทียบและต้นทุน', '',
    'ทุกชุดเริ่ม 100,000 บาท ขนาดคงที่ 0.1 lot =10oz **ต่อกฎ** สูงสุดสองกฎพร้อมกัน =0.2lot; FX33.77บาท/USD; กรณีหลักสเปรดคงที่0.168USD/oz ไม่มี commission/slippage เพิ่ม ไม่ทบล็อตตามกำไร', '',
    'v1 ในรายงานนี้เป็นกฎ A/B เดิมบนเครื่องจำลองปิดรายวันที่แก้การรู้อนาคตแล้ว ส่วน RX เดิมหมายถึง P20 จากรอบก่อนที่นำมารันด้วยกติกาปิดรายวันเดียวกัน ไม่ใช้ตัวเลขเก่าที่อนุญาตถือข้ามคืนมาเทียบตรง ๆ', '',
    '## ผลรวมสิบปี', '',
    '| ตัวชี้วัด | v1 ปิดรายวัน | RX เดิม + ปิดรายวัน | RX ใหม่ |','|---|---:|---:|---:|']
    for label,key,percent in [('กำไรสุทธิ (บาท)','net',False),('Max Equity DD (บาท)','dd',False),('Max Equity DD (%)','dd_pct',True),
        ('ขาดทุนรวมเฉพาะไม้แพ้ (บาท)','loss',False),('ขาดทุนเมื่อปิดไม้ที่หนักที่สุด (บาท)','worst',False),('จำนวนไม้','trades',False),
        ('ไม้ข้ามเวลาปิดตลาด','market_close_crossings',False),('ไม้ข้ามวันซื้อขาย','session_crossings',False)]:
        vals=[m[n][key] for n in names]
        lines.append('| '+label+' | '+' | '.join(f'{x:.2f}%' if percent else f(x) for x in vals)+' |')
    lines += ['',
    'กำไรคือการเปลี่ยนแปลง Equity; DD รวมมูลค่าปิดสถานะและต้นทุนทุกนาทีที่มีราคาซื้อขายได้ ขาดทุนรวมเฉพาะไม้แพ้ไม่ใช่ Drawdown และขาดทุนเมื่อปิดไม้ไม่ใช่ขาดทุนลอยตัวสูงสุดระหว่างถือ เปอร์เซ็นต์ DD หารยอด Equity สูงสุดก่อนลดลง ไม่ใช่ทุนตั้งต้น', '',
    '## แยกช่วงออกแบบและทดสอบ', '',
    '| ช่วง | กำไร v1 | กำไร RX เดิม | กำไร RX ใหม่ | DD v1 | DD RX ใหม่ |','|---|---:|---:|---:|---:|---:|']
    train=[lock['baseline_metrics'],lock['old_rx_metrics'],selected['metrics']]
    for label,vals in [('2010–2016 ใช้ออกแบบ',train),('2017–2019 เริ่มใหม่ด้วยทุน100k',[val[n] for n in names]),('2010–2019 ต่อเนื่อง',[m[n] for n in names])]:
        x,y,z=vals
        lines.append(f'| {label} | {sign(x["net"])} | {sign(y["net"])} | {sign(z["net"])} | {f(x["dd"])} | {f(z["dd"])} |')
    lines += ['',
    'ช่วงออกแบบ RX ใหม่ทำกำไรสูงกว่า v1 และ DD ต่ำกว่า แต่ช่วง 2017–2019 กำไรยังต่ำกว่า v1 แม้ดีขึ้นจาก RX เดิม จึงไม่ยืนยันว่าเหนือกว่า v1 นอกช่วงออกแบบ ผลทดสอบนี้เป็นการใช้ปีที่เคยเห็นในงานก่อนหน้า ไม่ใช่ holdout ใหม่ที่ไม่เคยถูกใช้', '',
    '## รายปี: รันต่อเนื่อง ไม่รีเซ็ตทุน', '',
    '| ปี | กำไร v1 | กำไร RX เดิม | กำไร RX ใหม่ | DD RX ใหม่ | ไม้เสียหนักสุด RX ใหม่ | จำนวนไม้ RX ใหม่ |',
    '|---|---:|---:|---:|---:|---:|---:|']
    for year in reports['rx']['yearly']:
        x,y,z=[reports[n]['yearly'][year] for n in names]
        lines.append(f'| {year} | {sign(x["equity_change"])} | {sign(y["equity_change"])} | {sign(z["equity_change"])} | {f(z["dd"])} | {sign(z["worst"])} | {z["trades"]:,} |')
    lines += ['',
    'หน่วยเงินเป็นบาท DD รายปีวัดจาก Equity ต้นปีและจุดสูงสุดในปีนั้น; DD รวมอาจข้ามปีได้ ยอดรายปีรวมกระทบกับผลรวมทั้งช่วงแล้ว', '',
    '## ปิดก่อนตลาด: สิ่งที่ทำและตรวจพบ', '',
    '- ใช้เวลา America/New_York พร้อม DST: ตั้งปิด16:55 ก่อนเวลาปิดที่กำหนด16:58 เปิดใหม่18:01; วันอาทิตย์18:05; ไม่เปิดช่วงสุดสัปดาห์',
    '- ตารางขึ้นกับวันและเวลาปัจจุบันเท่านั้น ไม่มีการหาจุดที่ราคาจะหายในอนาคตและไม่มีการปิดเพียงเพราะข้อมูลจบ',
    '- วันหยุดใช้นโยบายงดเข้าเทรดทั้ง session แบบอนุรักษนิยม: วันหยุดรัฐบาลสหรัฐตามปีนั้น, Good Friday, วันหลัง Thanksgiving, July3/วันทำการก่อนวันชดเชย July4 และ Dec24–Jan2 เริ่มงดตั้งแต่ช่วงเปิดของ session ในเย็นก่อนหน้า',
    '- วันหยุดยังเก็บราคาที่พบในช่วงตลาดปกติไว้สำหรับปิดฉุกเฉิน/คำนวณสัญญาณ การงดเข้าไม่ได้ห้ามปิดไม้ค้าง',
    '- กรองราคานอกช่วงตลาดที่กำหนด ไม่จำลองการส่งคำสั่งด้วยราคาของผู้ให้ข้อมูลในเวลาที่กำหนดว่าโบรกเกอร์ปิด',
    '- RX ใหม่:0ไม้ข้ามเวลาปิด/ข้ามวัน/คร่อมช่องว่างข้อมูลเกิน30นาที; ปิดตามตาราง482ไม้; ไม่มีสถานะค้างปลายข้อมูล',
    '- มี3ไม้พลาดนาทีเป้าหมาย16:55เพราะไม่มีราคา แต่ยังปิดก่อน16:58: วันที่2010-09-03 กฎBปิด16:57 และวันที่2013-09-25 กฎA/Bปิด16:56',
    '- v1 ฐานยังมี2ไม้ที่ข้อมูลหายก่อนถึงเวลาปิดและปิดได้หลังเปิดรอบถัดไป: วันที่2010-10-08 และ2013-05-31 ไม่ลบหรือย้ายราคาปิดย้อนหลังให้ดูเหมือนผ่าน', '',
    '**ขอบเขตคำว่า “ก่อนตลาดปิดทุกครั้ง”: ผ่านครบในรายการ RX ที่ทดสอบภายใต้ตารางนี้ ไม่ใช่การรับประกันกรณีโบรกเกอร์/เครือข่ายขัดข้องหรือปิดฉุกเฉินโดยไม่แจ้งล่วงหน้า โปรแกรมจะใช้ราคาซื้อขายได้แรกที่พบและบันทึกข้อยกเว้น ไม่สร้างราคาที่ไม่มีจริง**', '',
    'ประกาศวันหยุด Exness ย้อนหลัง2010–2019ยังมีไม่ครบ จึงใช้ blackout ที่ระบุข้างต้นเป็นนโยบายของกลยุทธ์ ไม่อ้างว่าเป็นปฏิทินโบรกเกอร์ย้อนหลังที่ยืนยันครบ [Exness ระบุว่าการเปลี่ยนเวลาวันหยุดแจ้งทางอีเมล](https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours); [คู่มือ CME2019](https://www.cmegroup.com/education/files/metals-prod_guide_2019.pdf) ใช้ประกอบความเข้าใจ session ทอง ไม่ใช้แทนประกาศ Exness', '',
    '## ค่าที่เลือกและวิธีจูน', '',
    '| รายการ | RX ใหม่ |','|---|---|',
    '| A | theta=1×max(sigma60,sigma1440), theta$ขั้นต่ำ3, leg≥2.5theta; งดสัญญาณเข้าเวลา21:00–23:59UTC |',
    '| B | theta=2×sigma60, theta$ขั้นต่ำ3, leg≥3.5theta; sigma60/sigma1440≤1.5 ณ เวลาสัญญาณ |',
    '| Stop | 2.5theta ตรวจเมื่อปิดนาที แล้วเติมราคาถัดไปที่มีจริง |',
    '| อื่น ๆ | สัญญาณเข้า/ออกหน่วงหนึ่งนาที; หนึ่งสถานะต่อกฎ; ตัวกรองเข้าไม่ลบสัญญาณออก |', '',
    f'ค้นหา{lock["single_rule_cells"]}ชุดกฎเดี่ยวและ{lock["portfolio_cells"]}พอร์ต/ค่าStop จากปี2010–2016 เลือก{selected["id"]}ตามเกณฑ์กำไรสูงขึ้น, DDต่ำลง, ขาดทุนรวมไม่เพิ่ม, ช่วง2014–2016ไม่แย่ลง, Equityเป็นบวก, ≥500ไม้ และไม่มีไม้ข้ามเวลาปิดหรือข้ามsession จากนั้นจัดอันดับกำไร/DD ไม่มีการแก้เกณฑ์หลังล็อก', '',
    f'ล็อกเมื่อ `{lock["locked_utc"]}`; สิ้นสุดประเมิน `{ev["finished_utc"]}` หลังล็อกไม่ปรับค่าตามผล2017–2019หรือสมมติฐานต้นทุน และไม่อ่านข้อมูลราคาปี2020ขึ้นไป', '',
    '## ความไวต่อต้นทุน', '',
    'ค่าตัวอย่างเพิ่ม commission0.01 และ slippage0.02 USD/oz/ข้าง รวม20.262บาทต่อไม้ที่0.1lot กรณี historicalใช้bid/askที่มีในข้อมูล ไม่บวกสองรายการนี้อีก ค่าตัวอย่างไม่ใช่ค่าบัญชีจริงที่ยืนยันแล้ว', '',
    '| ช่วง | ต้นทุน | กำไร v1 | กำไร RX เดิม | กำไร RX ใหม่ | DD RX ใหม่ |','|---|---|---:|---:|---:|---:|']
    labels={'fixed':'สเปรดคงที่','cost_example':'สเปรดคงที่+ค่าตัวอย่าง','historical':'bid/askในข้อมูล'}
    for period,label in [('full','2010–2019'),('validation','2017–2019เริ่มใหม่')]:
        for scenario,vals in ev['results'][period].items():
            x,y,z=[vals[n] for n in names]
            lines.append(f'| {label} | {labels[scenario]} | {sign(x["net"])} | {sign(y["net"])} | {sign(z["net"])} | {f(z["dd"])} |')
    lines += ['',
    'การเทรดน้อยลงช่วยลดต้นทุน: RXใหม่เหนือกว่า v1 ด้านกำไรรวมสิบปีในสองสมมติฐานต้นทุนที่สูงขึ้น แต่ผลหลักสเปรดคงที่และกำไรช่วง2017–2019ยังไม่ผ่านเป้าหมายเหนือv1 จึงไม่เปลี่ยนข้อสรุปโดยเลือกเฉพาะต้นทุนที่ให้ผลดี', '',
    'กรณี historical v1มีEquityต่ำสุด−10,172บาท เครื่องจำลองไม่มีmargin call/stop-out ผลหลังติดลบจึงเป็นทางคณิตศาสตร์ ไม่ใช่บัญชีจริงที่สามารถเทรดต่อได้เช่นนั้น', '',
    '## ขนาด0.5lotต่อกฎ', '',
    'สูงสุดรวม1.0lotเมื่อสองกฎถือพร้อมกัน ทุนตั้งต้น100,000บาทเหมือนเดิม เงินกำไร/ขาดทุนคูณ5 ส่วนDD%คำนวณใหม่จากEquity ไม่มีmargin,swap,fundingหรือผลขนาดคำสั่งต่อslippage จึงเป็นภาพจำลอง ไม่ยืนยันว่าทุนรองรับการเทรดจริง', '',
    '| ตัวชี้วัดสิบปี สเปรดคงที่ | v1 | RX เดิมปิดรายวัน | RX ใหม่ |','|---|---:|---:|---:|']
    for label,key in [('กำไรสุทธิ','net'),('Equityสิ้นงวด','end'),('Max DDบาท','dd'),('Max DD%','dd_pct'),('Equityต่ำสุด','lowest')]:
        vals=[extra[n]['lot05'][key] for n in names]
        lines.append('| '+label+' | '+' | '.join(f'{x:.2f}%' if key=='dd_pct' else f(x) for x in vals)+' |')
    lines += ['', '| ปี | กำไร RX ใหม่0.5lot | DDรายปี RX ใหม่0.5lot |','|---|---:|---:|']
    for year,z in reports['rx']['yearly'].items():lines.append(f'| {year} | {sign(5*z["equity_change"])} | {f(5*z["dd"])} |')
    lines += ['',f'ไม้ที่ปิดขาดทุนหนักที่สุดของRXใหม่ที่0.5lot = {sign(5*r["worst"])}บาท ไม่ใช่ขาดทุนลอยตัวสูงสุดระหว่างถือ', '',
    '## การตรวจสอบ', '',
    '- 121การทดสอบผ่าน ครอบคลุมเวลา/DST/วันหยุด/ปลายข้อมูล/ราคาหาย/ต้นทุน/การเลือกพารามิเตอร์ และชุดทดสอบเดิม',
    '- หลังล็อกตรวจข้อมูลจริง6prefix: v1, RXเดิม, RXใหม่ อย่างละ2จุด รวมจุดที่ถือสถานะค้าง สัญญาณ/รายการเทรด/Equityตรงกับช่วงเดียวกันในข้อมูลเต็มทุกค่า',
    '- กระทบยอดรายปี รายการเทรด Equity และนับไม้ข้ามเวลาปิดซ้ำจาก18รายงานแล้ว; รายการข้อยกเว้นอยู่ในCLOSE_EXCEPTIONS.private.jsonของแต่ละชุด',
    '- โค้ด/data/calendarก่อนและหลังตรงตามแฮช; ล็อกและโค้ดรอบเดิมไม่ถูกแก้; มีการตรวจโค้ดอิสระก่อนล็อก', '',
    '## จุดเริ่มใช้งานในโปรเจกต์', '',
    '- `../current_rx.py` โหลดกฎที่ล็อกและใช้เครื่องจำลองปิดรายวันเป็นค่าเริ่มต้น',
    '- `out/LOCK.json:selected` เก็บค่ากฎและstop; `out/EVALUATION.json` เก็บผลทุกช่วง/ต้นทุน',
    '- `out/CALENDAR.json` เก็บวันงดเข้าและสมมติฐานเวลา; `out/VERIFICATION.json` เก็บหลักฐานตรวจ',
    '- `execution.py`, `calendar_rules.py`, `run_study.py` เป็นโค้ดรุ่นนี้; รายงานเก่าในโฟลเดอร์แม่เป็นประวัติ', '',
    '**สถานะสุดท้าย:** แก้เงื่อนไขปิดตลาดของRXและทดสอบผ่านในข้อมูลที่ใช้; จูนแล้วกำไร/Drawdownดีขึ้นจากRXเดิมภายใต้กติกาเดียวกัน แต่ยังไม่ยืนยันว่าเหนือกว่าv1ทั้งกำไรและความเสี่ยงนอกช่วงออกแบบ', '']
    (d.ROOT/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(2,1,figsize=(12,7),sharex=True,gridspec_kw={'height_ratios':[2,1]})
    for name,label,color in [('baseline','v1 / daily close','#64748b'),('old_rx','Old RX / daily close','#c98c31'),('rx','Tuned RX / daily close','#0f766e')]:
        q=curves[name];x=q.index.to_numpy().astype('datetime64[D]')
        ax[0].plot(x,q.equity/1000,label=label,color=color,lw=1.25)
        ax[1].plot(x,-q.dd/1000,color=color,lw=.9)
    for a in ax:a.grid(alpha=.2);a.axvline(np.datetime64('2017-01-01'),color='#334155',ls='--',lw=1)
    ax[0].legend(loc='upper left');ax[0].set_ylabel('Equity (thousand THB)')
    ax[0].set_title('RX daily-close revision: same calendar and execution for all variants',loc='left')
    ax[1].set_ylabel('Drawdown (thousand THB)');ax[1].set_xlabel('UTC year | dashed line: reused validation starts')
    fig.text(.09,.01,'0.1 lot per rule; 100,000 THB initial; fixed $0.168 spread; daily equity / daily worst drawdown',fontsize=9)
    fig.tight_layout(rect=(0,.035,1,1));fig.savefig(d.ROOT/'equity_comparison.png',dpi=150);plt.close(fig)
    print('Daily report + chart written.',json.dumps(extra['rx']['lot05']))


if __name__=='__main__':main()
