"""Generate the final report from frozen evaluations; does not tune or trade."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import study

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def money(x):return f'{x:,.0f}'
def signed(x):return f'{x:+,.0f}'


def main():
    original=study.read_lock(OUT/'LOCK.json');locked=study.read_lock(OUT/'balanced/LOCK.json')
    study.verify_hashes(locked['source_hashes']);study.verify_hashes(locked['input_report_hashes'])
    evaluation=read(OUT/'balanced/EVALUATION.json')
    first=read(OUT/'EVALUATION.json')
    assert evaluation['input_hashes']==first['input_hashes']==locked['comparison_data_hashes']
    assert (ROOT/'baseline_engine.py').read_bytes()==(ROOT.parent/'swing-causal-execution/engine.py').read_bytes()
    folders={'v1':OUT/'evaluation/full/fixed/baseline','rx':OUT/'balanced/evaluation/full/fixed/rx'}
    reports={k:read(p/'REPORT.json') for k,p in folders.items()}
    extras={};curves={}
    for name,p in folders.items():
        rep=reports[name];t=pd.read_csv(p/'TRADES.private.csv');n=t.net_thb.to_numpy()
        with np.load(p/'EQUITY.private.npz',allow_pickle=False) as z:
            times=z['t_minute'];equity=z['equity']
        assert np.isclose(sum(r['equity_change'] for r in rep['yearly'].values()),rep['metrics']['net'],atol=1e-7,rtol=0)
        assert np.isclose(n.sum(),rep['summary']['closed_trade_net_thb'],atol=1e-7,rtol=0)
        design=original['baseline_metrics'] if name=='v1' else locked['selected_metrics']
        assert np.isclose(rep['yearly']['2016']['end_equity']-100000,design['net'],atol=1e-7,rtol=0)
        e5=100000+5*(equity-100000);peak=np.maximum.accumulate(np.r_[100000.,e5])[1:]
        extras[name]=dict(profit_factor=float(n[n>0].sum()/-n[n<0].sum()),win_pct=float(100*(n>0).mean()),
            losing_trades=int((n<0).sum()),mean_losing_trade=float(n[n<0].mean()),
            lot05=dict(net=float(e5[-1]-100000),end=float(e5[-1]),dd=float((peak-e5).max()),
                       dd_pct=float((100*(peak-e5)/peak).max()),lowest=float(min(100000,e5.min()))))
        peaks=np.maximum.accumulate(np.r_[100000.,equity])[1:]
        daily=pd.DataFrame(dict(day=times//1440,equity=equity,dd=peaks-equity)).groupby('day').agg(equity=('equity','last'),dd=('dd','max'))
        curves[name]=daily
    b=reports['v1']['metrics'];r=reports['rx']['metrics']
    assert np.isclose(b['net'],359209.294949708,atol=1e-7,rtol=0)
    assert np.isclose(b['dd'],68462.93410005042,atol=1e-7,rtol=0)
    checks=read(ROOT/'research/FINAL_CAUSAL_CHECKS.json')
    assert checks['status']=='PASS'
    study.write_json(OUT/'REPORT_CHECKS.json',dict(status='PASS',source_hashes_verified=True,
        baseline_engine_identical=True,comparison_data_identical=True,baseline_reproduced=True,
        yearly_equity_reconciles=True,closed_trades_reconcile=True,training_prefix_reconciles=True,
        actual_prefix_checks='research/FINAL_CAUSAL_CHECKS.json',extras=extras,
        report_generator_sha256=study.sha(__file__)))

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True,gridspec_kw={'height_ratios':[2,1]})
    for name,label,color in [('v1','v1 causal baseline','#64748b'),('rx','v1-rx P20','#0f766e')]:
        q=curves[name];x=q.index.to_numpy().astype('datetime64[D]')
        axes[0].plot(x,q.equity/1000,label=label,color=color,linewidth=1.4)
        axes[1].plot(x,-q.dd/1000,color=color,linewidth=1.0)
    for ax in axes:
        ax.axvline(np.datetime64('2017-01-01'),color='#b45309',linestyle='--',linewidth=1)
        ax.grid(alpha=.2)
    axes[0].set_title('v1-rx: less drawdown, but no confirmed profit improvement',loc='left',fontsize=14)
    axes[0].set_ylabel('Equity (thousand THB)');axes[0].legend(loc='upper left')
    axes[1].set_ylabel('Drawdown (thousand THB)');axes[1].set_xlabel('UTC year; dashed line = start of reused validation')
    fig.text(.09,.01,'0.1 lot per rule | 100,000 THB initial | fixed $0.168 spread | daily close equity / daily worst drawdown',fontsize=9,color='#475569')
    fig.tight_layout(rect=(0,.035,1,1));fig.savefig(ROOT/'equity_comparison.png',dpi=150);plt.close(fig)

    def period_row(label,base,rx):
        return f'| {label} | {signed(base["net"])} | {signed(rx["net"])} | {money(base["dd"])} | {money(rx["dd"])} |'
    lines=[
    '# ผลการปรับจูน v1-rx — 2010–2019',
    '',
    '**ข้อสรุป: ลด Drawdown และขาดทุนรวมได้ แต่ยังไม่ยืนยันว่ากำไรดีขึ้นนอกช่วงออกแบบ จึงยังไม่ให้แทน v1 เดิมโดยอัตโนมัติ**',
    '',
    'ชุด P20 ที่พัฒนาในโฟลเดอร์นี้ ใช้ข้อมูลเฉลยปี 2010–2016 เพื่อออกแบบตามที่ได้รับอนุญาต แล้วล็อกกฎก่อนทดสอบชุดนี้ในปี 2017–2019 ไม่มีการแก้ค่าหลังเห็นผลของ P20 และไม่ได้อ่านข้อมูลราคาปี 2020 ขึ้นไปในการทดลองนี้',
    '',
    f'ผลหลักที่สเปรดคงที่: กำไรรวมลด {100*(1-r["net"]/b["net"]):.2f}% แต่ Max Drawdown เป็นบาทลด {100*(1-r["dd"]/b["dd"]):.2f}% และขาดทุนรวมเฉพาะไม้แพ้ลด {100*(1-r["loss"]/b["loss"]):.2f}%',
    '',
    '## สมมติฐานเดียวกันทั้งสองรุ่น',
    '',
    '- ทุนเริ่ม 100,000 บาท; ขนาดคงที่ 0.1 lot = 10 oz **ต่อกฎ**; A และ B อาจซ้อนกัน รวมสูงสุด 0.2 lot',
    '- FX คงที่ 33.77 บาท/USD; สเปรดหลัก 0.168 USD/oz; กรณีหลักยังไม่บวก commission/slippage เพิ่ม',
    '- กำไร = การเปลี่ยนแปลง Equity รวมสถานะค้าง; DD = การลดจากจุดสูงสุดของ Equity โดยนับมูลค่าปิดสถานะทุกนาทีและต้นทุน',
    '- ขาดทุนรวมเฉพาะไม้แพ้ คือผลรวมขนาดขาดทุนของไม้ที่ปิดลบ ไม่ใช่การขาดทุนสะสมของบัญชีและไม่ใช่ Drawdown',
    '- เปรียบเทียบกับ v1 บนเครื่องจำลองที่แก้เรื่องข้อมูลอนาคตแล้ว ไม่ใช้ผลจากเครื่องจำลอง v1 เก่า',
    '',
    '## ผลแยกช่วง',
    '',
    '| ช่วง | กำไร v1 (บาท) | กำไร P20 (บาท) | Max DD v1 (บาท) | Max DD P20 (บาท) |',
    '|---|---:|---:|---:|---:|',
    period_row('2010–2016: ใช้ออกแบบ',locked['baseline_metrics'],locked['selected_metrics']),
    period_row('2017–2019: เริ่มใหม่ด้วยทุน 100,000',evaluation['results']['validation']['fixed']['baseline'],evaluation['results']['validation']['fixed']['rx']),
    period_row('2010–2019: รันต่อเนื่อง',b,r),
    '',
    'ผล 2017–2019 แบบเริ่มใหม่ต่างจากการหักยอดปี 2016 จากการรันเต็ม เพราะเริ่มสถานะและประวัติคำนวณใหม่ ไม่ได้บังคับปิดหรือรีเซ็ตระบบตรงปี 2017 ในการรันเต็ม',
    '',
    '## รายละเอียดทั้งสิบปี',
    '',
    '| ตัวชี้วัด | v1 | P20 |',
    '|---|---:|---:|',
    f'| กำไรสุทธิ (บาท) | {signed(b["net"])} | {signed(r["net"])} |',
    f'| Equity สิ้นงวด (บาท) | {money(100000+b["net"])} | {money(100000+r["net"])} |',
    f'| Max Equity DD (บาท) | {money(b["dd"])} | {money(r["dd"])} |',
    f'| Max Equity DD (%) | {b["dd_pct"]:.2f}% | {r["dd_pct"]:.2f}% |',
    f'| ขาดทุนรวมเฉพาะไม้แพ้ (บาท) | {money(b["loss"])} | {money(r["loss"])} |',
    f'| ขาดทุนหนักที่สุดเมื่อปิดหนึ่งไม้ (บาท) | {signed(b["worst"])} | {signed(r["worst"])} |',
    f'| จำนวนไม้ที่ปิด | {b["trades"]:,} | {r["trades"]:,} |',
    f'| อัตราชนะ | {extras["v1"]["win_pct"]:.2f}% | {extras["rx"]["win_pct"]:.2f}% |',
    f'| Profit factor | {extras["v1"]["profit_factor"]:.3f} | {extras["rx"]["profit_factor"]:.3f} |',
    f'| ขาดทุนเฉลี่ยต่อไม้แพ้ (บาท) | {signed(extras["v1"]["mean_losing_trade"])} | {signed(extras["rx"]["mean_losing_trade"])} |',
    '',
    'DD เป็นบาทและ DD เป็นเปอร์เซ็นต์อาจเกิดคนละเวลา เปอร์เซ็นต์หารด้วยยอด Equity สูงสุดก่อนการลดลง ไม่ใช่หารทุนเริ่มต้น และขาดทุนเมื่อปิดหนึ่งไม้ไม่ใช่ขาดทุนลอยตัวสูงสุดระหว่างถือไม้นั้น',
    '',
    '**ความเสี่ยงไม่ได้ลดทุกมิติ:** ในช่วงทดสอบ 2017–2019 แบบเริ่มใหม่ P20 มี DD 24.85% เทียบ v1 24.30% และไม้ที่ปิดขาดทุนหนักสุด −7,501 เทียบ −5,337 บาท แม้ DD เป็นบาทลดลง จำนวนไม้ทั้งสิบปีลดมากกว่าครึ่ง จึงอธิบายการลดขาดทุนรวมได้ส่วนใหญ่',
    '',
    '## กำไรและ Drawdown รายปี',
    '',
    'รันต่อเนื่อง ไม่เติมเงินหรือรีเซ็ตทุนเมื่อขึ้นปีใหม่ กำไรรายปีรวมการเปลี่ยนแปลงสถานะค้าง ส่วน DD รายปีเริ่มวัดจาก Equity ต้นปี จึงไม่เท่ากับ DD ตลอดช่วงที่อาจข้ามปี',
    '',
    '| ปี | กำไร v1 | กำไร P20 | ส่วนต่าง P20−v1 | DD v1 | DD P20 | ไม้ P20 |',
    '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for year,x in reports['v1']['yearly'].items():
        y=reports['rx']['yearly'][year]
        lines.append(f'| {year} | {signed(x["equity_change"])} | {signed(y["equity_change"])} | {signed(y["equity_change"]-x["equity_change"])} | {money(x["dd"])} | {money(y["dd"])} | {y["trades"]:,} |')
    lines += ['', 'หน่วยเงินเป็นบาท ช่วง 2014–2016 ยังขาดทุน: P20 −11,138 บาท เทียบ v1 −33,225 บาท จึงยังแก้ช่วงตลาดที่ระบบทำงานไม่ดีได้ไม่หมด', '',
    '### ขาดทุนรายปี', '', '| ปี | ขาดทุนรวมไม้แพ้ v1 | ขาดทุนรวมไม้แพ้ P20 | ไม้ปิดแย่สุด v1 | ไม้ปิดแย่สุด P20 |', '|---|---:|---:|---:|---:|']
    for year,x in reports['v1']['yearly'].items():
        y=reports['rx']['yearly'][year]
        lines.append(f'| {year} | {money(x["loss"])} | {money(y["loss"])} | {signed(x["worst"])} | {signed(y["worst"])} |')
    lines += ['',f'![Equity and drawdown comparison]({(ROOT/"equity_comparison.png").as_posix()})','',
    '## ผลเมื่อเปลี่ยนต้นทุน โดยใช้กฎที่ล็อกไว้เดิม','',
    'ค่าคอมมิชชันตัวอย่าง 0.01 USD/oz/ข้าง และ slippage 0.02 USD/oz/ข้าง เพิ่มต้นทุนรวม 20.262 บาทต่อไม้ที่ 0.1 lot กรณีสเปรดในข้อมูลใช้ bid/ask ของแต่ละนาทีโดยไม่บวกสองรายการนี้ ค่าตัวอย่างไม่ใช่เงื่อนไขโบรกเกอร์ที่ยืนยันแล้ว','',
    '| ช่วง | ต้นทุน | กำไร v1 | กำไร P20 | DD v1 | DD P20 |','|---|---|---:|---:|---:|---:|']
    labels={'fixed':'สเปรดคงที่','cost_example':'สเปรดคงที่ + ค่าตัวอย่าง','historical':'สเปรด bid/ask ในข้อมูล'}
    for period,label in [('full','2010–2019'),('validation','2017–2019 เริ่มใหม่')]:
        for scenario,m in evaluation['results'][period].items():
            x,y=m['baseline'],m['rx']
            lines.append(f'| {label} | {labels[scenario]} | {signed(x["net"])} | {signed(y["net"])} | {money(x["dd"])} | {money(y["dd"])} |')
    lines += ['',
    'P20 ได้เปรียบด้านต้นทุนในผลรวมสิบปีเพราะเข้าเทรดน้อยกว่า แต่กำไรช่วง 2017–2019 ยังต่ำกว่า v1 ทุกสมมติฐานต้นทุน จึงไม่เปลี่ยนข้อสรุปจากผลรวมที่ดูดีขึ้นบางกรณี', '',
    'กรณี bid/ask ในข้อมูล v1 มี Equity ต่ำสุด −86,944 บาท เครื่องจำลองไม่มี margin call/stop-out จึงเป็นเส้นทางคำนวณที่ไม่จำกัดเงินทุน ผลหลังบัญชีติดลบไม่ใช่สิ่งที่บัญชีจริงสามารถเทรดต่อได้ตามนี้ ส่วน P20 ต่ำสุด 93,066 บาทในกรณีเดียวกัน', '',
    '## ถ้าขนาด 0.5 lot ต่อกฎ', '',
    'คำนวณต่อจากคำถามเรื่องขนาดล็อตเดิม: เท่ากับ 50 oz ต่อกฎ รวมสูงสุด 1.0 lot หาก A/B ถือพร้อมกัน ใช้ทุนเริ่ม 100,000 บาทเท่าเดิมและสเปรดคงที่ กำไร/ขาดทุนเป็นบาทคูณห้า แต่ DD% คำนวณใหม่จากเส้น Equity ไม่ได้คูณห้า', '',
    '| ตัวชี้วัด 2010–2019 | v1 | P20 |','|---|---:|---:|']
    for label,key,percent in [('กำไรสุทธิ (บาท)','net',False),('Equity สิ้นงวด (บาท)','end',False),('Max DD (บาท)','dd',False),('Max DD (%)','dd_pct',True),('Equity ต่ำสุด (บาท)','lowest',False)]:
        x,y=extras['v1']['lot05'][key],extras['rx']['lot05'][key]
        lines.append(f'| {label} | '+(f'{x:.2f}% | {y:.2f}% |' if percent else f'{money(x)} | {money(y)} |'))
    lines += ['', '| ปี | กำไร v1 ที่ 0.5 lot | กำไร P20 ที่ 0.5 lot | DD รายปี v1 | DD รายปี P20 |', '|---|---:|---:|---:|---:|']
    for year,x in reports['v1']['yearly'].items():
        y=reports['rx']['yearly'][year]
        lines.append(f'| {year} | {signed(5*x["equity_change"])} | {signed(5*y["equity_change"])} | {money(5*x["dd"])} | {money(5*y["dd"])} |')
    lines += ['',
    'นี่เป็นการขยายผลเชิงคณิตศาสตร์ ไม่มีการคำนวณ margin, swap, funding หรือความลื่นไถลที่เพิ่มตามขนาดคำสั่ง จึงยังไม่ใช่การยืนยันว่าทุน 100,000 บาทรองรับขนาดนี้จริง', '',
    '## กฎที่เปลี่ยน', '',
    '| กฎ | v1 | P20 |','|---|---|---|',
    '| A | k=1 × max(sigma60,sigma1440), ขั้นต่ำ $2.162693444, leg ≥2.5theta, ซื้อ/ขาย | เกณฑ์เดิม แต่เปิดเฉพาะซื้อ |',
    '| B | k=1.5 × sigma60, ขั้นต่ำ $0, leg ≥3.5theta | k=2 × sigma60, ขั้นต่ำ $3, leg ≥3.5theta และ sigma60/sigma1440 ≤1.5 ณ นาทีสัญญาณ |',
    '| การออกและขนาด | stop 3theta, ออกตาม swing, ขนาด 10oz ต่อกฎ | เหมือนเดิม |', '',
    'ไม่ได้เพิ่มกำไรด้วยการเพิ่มล็อต และไม่ได้ใช้เหตุการณ์หลังเปิดไม้เป็นตัวกรองเข้า สัญญาณที่ไม่ผ่านตัวกรองเข้ายังคงใช้เป็นสัญญาณออกของสถานะที่ถืออยู่', '',
    '## การคัดเลือกและข้อจำกัดของหลักฐาน', '',
    'ค้นหา 176 ชุดกฎเดี่ยว แล้วเทียบ 36 พอร์ตจากข้อมูล 2010–2016 เท่านั้น เกณฑ์เดิมกำหนดกำไรเพิ่มอย่างน้อย 5%, DD ลดอย่างน้อย 10%, ขาดทุนรวมไม่เพิ่ม, Equity ไม่ติดลบ, ช่วง 2014–2016 ดีขึ้น และจำนวนไม้ไม่น้อยกว่า 50% ของ v1', '',
    'ไม่มีชุดผ่านครบ เก็บผลเดิมไว้โดยไม่ลบ: P01 เป็นชุดสำรองที่อัตรากำไร/DD สูงสุด แต่กำไรรวมสิบปีเหลือ 112,580 บาท และปี 2017–2019 ได้ 7,509 บาท จึงไม่ใช่การเพิ่มกำไรที่สำเร็จ', '',
    'จากนั้นเปิดเผยการแก้เกณฑ์หนึ่งข้อ: เอาขั้นต่ำจำนวนไม้ออก เนื่องจาก P20 ทำกำไรเพิ่ม 15.27%, DD ลด 49.93%, ขาดทุนรวมลด 54.29% ในช่วงออกแบบ แต่เหลือ 2,705 ไม้ หรือ 46.06% ของเดิม จึงตกเพียงเงื่อนไขจำนวนไม้ที่ตั้งเพิ่มเอง มี P20/P21/P22 ผ่านเกณฑ์ที่เหลือและ P20 ได้อันดับแรกตามวิธีจัดอันดับเดิม ไม่ได้ค้นหาชุดกฎเพิ่ม', '',
    'P20 เป็นการทดลองเพิ่มเติมหลังแก้เกณฑ์จากผลที่เห็นแล้ว ไม่ใช่ผู้ชนะตามแผนเดิม ช่วง 2017–2019 เคยถูกเห็นในงานก่อนหน้า และตอนบันทึกการทดลองเพิ่มเติม ผลชุดสำรอง P01 ก็มีแล้ว จึงเรียกผลนี้ว่า exploratory/reused validation ไม่ใช่ holdout ใหม่ที่ไม่เคยถูกแตะ การเลือก P20 ใช้เฉพาะตารางผล 2010–2016 และไม่มีการปรับหลังเห็นผล P20', '',
    'ตัวกรองอัตราส่วนความผันผวนของ P20 ตัดออกจาก P21 เพียงหนึ่งไม้ในช่วงออกแบบ จึงยังมีหลักฐานรองรับตัวกรองนี้น้อย อีกทั้งความได้เปรียบด้านกำไรไม่ต่อเนื่องถึงปี 2017–2019 ไม่ควรประกาศว่าเหนือกว่า v1 โดยรวม', '',
    '## การป้องกันข้อมูลอนาคตและการตรวจสอบ', '',
    '- ความผันผวนใช้ผลตอบแทนในอดีตจากคู่ราคาที่ห่างหนึ่งนาที; ชั่วโมงและตัวกรองอ่าน ณ นาทีสัญญาณ',
    '- รอปิดแท่งเพื่อยืนยันแล้วค่อยส่งคำสั่ง นาทีถัดไปเป็นราคาเติม; ถ้านาทีเข้าหาย ยกเลิกคำสั่งเข้า',
    '- Stop ที่ตรวจจากราคาปิดเติมในราคาถัดไปที่มีจริง ไม่ใช้ราคา stop ในอดีต; ช่องว่างข้อมูลปิดได้เมื่อมีราคาใหม่หลังช่องว่างแล้วเท่านั้น',
    '- ไม่บังคับปิดสถานะย้อนหลังตรงปลายชุดข้อมูล; Equity คิดราคาที่ปิดได้จริงและต้นทุนระหว่างถือสถานะ',
    '- ทดสอบอัตโนมัติที่เกี่ยวข้อง 105 ข้อผ่าน; ตรวจ prefix ข้อมูลจริง 66 กรณีผ่าน และตรวจ P20 เพิ่มทั้งสัญญาณ Equity และไม้ที่ปิดแล้วตรงกันทุกค่าที่สองจุดตัด รวมจุดที่มีสถานะค้าง',
    '- Snapshot เครื่องจำลองตรงกับต้นฉบับทุกไบต์; ตรวจแฮชโค้ดและข้อมูลก่อน/หลัง; ผล baseline ทำซ้ำตรงกับผล causal เดิม',
    '- ยอดรายปีรวมตรงกับยอดทั้งช่วง และยอด Equity ปลายปี 2016 ตรงกับช่วงออกแบบ; การตรวจอิสระแก้ข้อบกพร่องด้าน provenance ก่อนล็อกแต่ละรอบ', '',
    f'Original LOCK: `{original["locked_utc"]}`; P20 LOCK: `{locked["locked_utc"]}`; P20 evaluation finish: `{evaluation["finished_utc"]}`', '',
    '## ไฟล์หลัก', '',
    '- `out/balanced/LOCK.json`, `out/balanced/EVALUATION.json`: กฎและผล P20 ที่ล็อกไว้',
    '- `out/LOCK.json`, `out/EVALUATION.json`: การเลือกชุดแรกและผลที่ไม่ผ่าน เก็บไว้ครบ',
    '- `out/PORTFOLIO_TRAIN.json`, `out/SINGLE_RULE_TRAIN.json`: ผลทุกชุดที่ค้นหาในช่วงออกแบบ',
    '- `out/REPORT_CHECKS.json`: การกระทบยอดและตัวเลข 0.5 lot',
    '- `research/CAUSAL_CHECKS.json`, `research/FINAL_CAUSAL_CHECKS.json`: การตรวจไม่มีข้อมูลอนาคต',
    '- `out/**/REPORT.json`: ตัวเลขรายปีทุกสมมติฐานต้นทุน; รายการเทรดและ Equity เก็บเป็นไฟล์ `.private.*` ในเครื่อง', '',
    '**สถานะสุดท้าย: NOT_CONFIRMED — มีรุ่นที่เสี่ยงรวมลดลง แต่ยังไม่ผ่านเป้าหมายกำไรเพิ่มพร้อมขาดทุนลดในช่วงทดสอบ 2017–2019**', '']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Report, chart and accounting checks written; NOT_CONFIRMED.')


if __name__=='__main__':main()
