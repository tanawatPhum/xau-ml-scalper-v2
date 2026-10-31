"""Read-only result reconciliation and report; no market-data reads."""
import json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=read(ROOT/'out/TRAINING.json');b=read(ROOT/'continuation/out/TRAINING.json')
val=read(ROOT/'continuation/out/VALIDATION.json')
original={x['spec']['id']:x for x in a['rows']}
for x in b['rows']:
    y=original[x['spec']['id'].removeprefix('opposite_')]
    n=x['metrics']['trades'];assert n==y['metrics']['trades']
    assert x['metrics']['overlap']==y['metrics']['overlap']
    np.testing.assert_allclose(x['metrics']['net'],-y['metrics']['net']-2*n*.168*10*33.77,atol=.001,rtol=0)
for folder in ('out','continuation/out'):
    p=ROOT/folder;lock=read(p/'LOCK.json')
    assert sha(p/'LOCK.json')==(p/'LOCK.sha256').read_text().strip()
    for path,h in lock['sources'].items():assert sha(Path(path))==h,path
    for path,h in lock['training_data_hashes'].items():assert sha(Path(path))==h,path
for path,h in val['data_hashes'].items():assert sha(Path(path))==h,path
baseline=read(ROOT.parent/'v1-r2/out/LOCK.json')['training_metrics']
for k in ('net','dd','trades','loss'):np.testing.assert_allclose(a['ab_metrics'][k],baseline[k],atol=1e-6,rtol=0)
chosen=val['results'][0];selected=next(r for r in b['rows'] if r['spec']['id']==chosen['spec']['id'])
for r in (selected,chosen):
    np.testing.assert_allclose(sum(y['net'] for y in r['yearly'].values()),r['metrics']['net'],atol=1e-6,rtol=0)
verify=dict(status='PASS',total_training_cells=48,training_signal_trade_equity_prefix_checks=48,
    validation_prefix_checks=1,opposite_net_cost_identities=24,baseline_reproduced=True,
    source_data_lock_hashes_verified=True,validation_status=val['status'],new_version_created=False,
    first_run_note='Initial training run aborted before lock because a signal module synthetic-test section changed concurrently. Reran unchanged candidates after files stabilized; no first-run selection or validation occurred.')
(ROOT/'VERIFICATION.json').write_text(json.dumps(verify,indent=2),encoding='utf-8')
m=selected['metrics'];v=chosen['metrics'];ab=val['ab_metrics']
lines=['# วิจัยกฎ C เพิ่มจาก v1-r2 — 1 พฤศจิกายน 2026','','**ผล: ยังไม่พบกฎ C ที่ผ่านการทดสอบหลังล็อกสูตร (NOT_CONFIRMED)**',
'ทดลองในโฟลเดอร์นี้เท่านั้น ไม่เปิดรุ่นใหม่ ไม่เปลี่ยน v1-r1/v1-r2 หรือทะเบียนรุ่น',
'','## เกณฑ์และขอบเขต',
'- ผู้ใช้กำหนด: กำไรมากกว่าขาดทุนหลังต้นทุน และ C เข้าในขณะที่ A หรือ B ถืออยู่ไม่เกิน30% ของไม้ C',
'- นับ A/B รวมกันไม่ซ้ำและไม่สนทิศทาง; เข้าพร้อมกันนับซ้ำ; A/B ปิดในนาทีเดียวกับ C เข้าไม่นับ เพราะใช้สถานะหลังประมวลผลราคานาทีนั้น',
'- ไม่ใช้ตัวกรองห้ามเข้าเมื่อ A/B ถือ เพื่อให้ overlap เป็นคุณสมบัติตามธรรมชาติของ setup',
'- ออกแบบ2010–2016; ล็อกก่อน2017–2019; รอบนี้ไม่อ่าน2020ขึ้นไป ปีทดสอบเคยใช้ในงานก่อน จึงไม่ใช่ข้อสอบใหม่',
'- 0.1lot=10ozต่อกฎ; FX33.77; สเปรด.168USD/oz; ทุน100,000บาท; ต้นทุนตัวอย่างเพิ่ม commission.01 และ slippage.02USD/oz/ข้าง',
'- เกณฑ์วิจัยเพิ่มเติมกำหนดก่อนรัน: >=100ไม้ช่วงออกแบบ/>=20ไม้ช่วงทดสอบ, ช่วง2014–2016บวก, เพิ่มต้นทุนแล้วยังบวก, ไม่มีไม้ข้ามวัน/เวลาปิดหรือค้างปลายข้อมูล',
'','## สองรอบการค้นหา',
'รอบแรก24ชุด: หลุดกรอบแล้วกลับเข้า, กลับเข้าช่วงรอบค่าเฉลี่ย, เบรกกรอบหลังบีบตัว อย่างละ8ชุด ทุกชุดขาดทุนหลังต้นทุน จึงไม่มีสูตรผ่านและไม่เปิดช่วงทดสอบในรอบแรก',
'','รอบสอง24ชุด: เห็นผลรอบแรกแล้วตั้งสมมติฐานกลับทิศสัญญาณทุกชุด โดยไม่เปลี่ยนเวลาเข้า ระยะStop/เป้ากำไร หรือเวลาถือ นี่เป็นการออกแบบต่อเนื่องบนข้อมูลฝึก ไม่ใช่สมมติฐานที่ตั้งไว้ก่อนเห็นผลทั้งหมด รวมค้นหา48ชุด',
'','สี่ชุดผ่านเกณฑ์ออกแบบ ทั้งหมดอยู่ในกลุ่มตามทิศเดิมหลังการย่อกลับเข้าช่วงรอบค่าเฉลี่ย เลือกหนึ่งชุดด้วย daily t สูงสุดตามกติกาที่เขียนไว้ก่อนรัน ไม่เลือกจากผล2017–2019',
'','## สูตรที่ล็อกไปทดสอบ',
f"รหัส `{chosen['spec']['id']}`",'',
'1. ใช้ค่าเฉลี่ยของราคาปิด60นาทีก่อนหน้า ต้องต่อเนื่องและอยู่ในsessionเดียวกัน',
'2. วัดระยะจากค่าเฉลี่ยด้วยความผันผวนที่รู้แล้ว; เมื่อราคาเคยอยู่นอกช่วง±2.5เท่าแล้วกลับเข้าช่วง ให้เข้าตามทิศของการเบี่ยงเดิม: กลับจากด้านล่างเข้า SELL, กลับจากด้านบนเข้า BUY',
'3. ส่งเข้าในนาทีถัดไปเท่านั้น ถ้าไม่มีราคานาทีนั้นยกเลิก ระยะStop/เป้ากำไร1.5เท่าของ scale ณ สัญญาณ (scale ขั้นต่ำ$0.50)',
'4. Stop/เป้าตรวจราคาปิดนาทีแล้วใช้ราคาถัดไปที่มีจริง; ตั้งปิดตามเวลา90นาทีหลังเข้า หรือเวลาปิดรายวัน16:55NY แล้วแต่มาถึงก่อน ไม่สร้างราคาก่อนช่องว่างย้อนหลัง',
'','สูตรนี้เปลี่ยนวิธีหาจุดเข้า แต่แนวคิดตามทิศเดิมหลังการย่อยังคล้าย A/B จึงไม่อ้างว่าเป็นแหล่งกำไรทางเศรษฐกิจคนละประเภท วัดความต่างของจังหวะเข้าจริงแยกต่างหาก',
'การกลับเข้าช่วงหมายถึงระยะที่ปรับด้วยความผันผวนกลับเข้าขอบ ไม่ได้ยืนยันว่าราคาย่อจริงทุกครั้ง เพราะค่าเฉลี่ยหรือความกว้างของช่วงเองก็เปลี่ยนได้',
'','| ตัวชี้วัด C | ออกแบบ2010–2016 | ทดสอบ2017–2019 |','|---|---:|---:|']
for label,key,fmt in [('กำไรสุทธิบาท','net',',.2f'),('รวมไม้กำไรบาท','gross_wins',',.2f'),('รวมไม้ขาดทุนบาท (ขนาดบวก)','gross_losses',',.2f'),('Profit factor','profit_factor','.3f'),('จำนวนไม้','trades',',d'),('Max equity DDบาท','dd',',.2f'),('กำไรเมื่อเพิ่มต้นทุนตัวอย่าง','example_net',',.2f'),('daily t','daily_t','.3f')]:
    lines.append(f'| {label} | {m[key]:{fmt}} | {v[key]:{fmt}} |')
lines += [f"| เข้าเมื่อ A/B ถืออยู่ | {m['overlap']:.2%} (5/{m['trades']}) | {v['overlap']:.2%} (2/{v['trades']}) |",
f"| ข้ามเวลาปิด/session | {m['market_close_crossings']}/{m['session_crossings']} | {v['market_close_crossings']}/{v['session_crossings']} |",
'',f"ทดสอบด้วย bid/askในข้อมูลได้ {v['historical_net']:,.2f}บาท ยังขาดทุน สัดส่วนเข้าซ้ำผ่าน30% แต่กำไรไม่ผ่าน",'',
'## รายปีของสูตรที่เลือก (0.1lot)',
'ช่วง2017–2019เริ่มทุนใหม่100,000บาท ไม่ใช่การนำกำไรสะสมช่วงออกแบบมาปิดบังผลทดสอบ',
'','| ปี | ช่วง | กำไรสุทธิบาท | DDภายในปีบาท |','|---|---|---:|---:|']
for r,label in ((selected,'ออกแบบ'),(chosen,'ทดสอบ')):
    for y,z in r['yearly'].items():lines.append(f"| {y} | {label} | {z['net']:,.2f} | {z['dd']:,.2f} |")
lines+=['','## ผลต่อ A/B เมื่อเพิ่ม C ในช่วง2017–2019',
'| ตัวชี้วัด | A/Bเดิม | A/B+C |','|---|---:|---:|',
f"| กำไรสุทธิบาท | {ab['net']:,.2f} | {v['combined_net']:,.2f} |",
f"| Max equity DDบาท | {ab['dd']:,.2f} | {v['combined_dd']:,.2f} |",
'','เมื่อเพิ่ม C กำไรลดและ DD เพิ่ม จึงไม่ผ่านการนำไปเพิ่มในรุ่นถัดไป',
'','## ข้อจำกัดและหลักฐาน',
'- ค่า sign-flip max-t p ของสูตรที่เลือกในรอบสองประมาณ0.045 เป็นการตรวจเฉพาะ24ชุดของรอบนั้น ไม่ได้ครอบคลุมกระบวนการออกแบบซ้ำ48ชุดและงานเก่าทั้งหมด จึงไม่อ้างนัยสำคัญโดยรวม',
'- เนื่องจากStop/เป้ากำไรสมมาตร การกลับทิศทำให้เวลาเข้าออกและoverlapเหมือนเดิม ตรวจสมการ netกลับทิศ = -netเดิม -2×ต้นทุนรวม ครบ24คู่แล้ว',
'- ตรวจprefixสัญญาณ/รายการเทรด/Equityจริง48ชุดฝึกและ1ชุดทดสอบ ผลอดีตไม่เปลี่ยนเมื่อเอาข้อมูลอนาคตออก',
'- ทดสอบสังเคราะห์เรื่องต้นทุน ฝั่งBUY/SELL ราคาขาดช่วง เวลาออก และผู้ตรวจอิสระตรวจโค้ดแล้ว; ผล A/Bช่วงฝึกตรงกับv1-r2เดิม',
'- ต้นทุน/ขนาดล็อตคงที่ ไม่มีmargin callหรือswap; ชุดที่Equityติดลบเป็นเส้นผลตอบแทนทางคณิตศาสตร์ ไม่ใช่บัญชีที่เทรดต่อได้จริง',
'- ปฏิทินวันหยุดเป็นนโยบายอนุรักษนิยม ไม่ใช่ประกาศย้อนหลังโบรกเกอร์ที่ยืนยันครบ; บางชุดที่ไม่ผ่านมีไม้คร่อมราคาขาดช่วงและถูกตัดสิทธิ์อย่างเปิดเผย',
'- overlap_exposure_fraction ในJSONวัดเฉพาะนาทีที่มีราคา ไม่ใช่ระยะเวลาจริงทั้งหมด และไม่ใช่ตัวเกณฑ์30%ที่ผู้ใช้กำหนด',
'','## ไฟล์ผล',
'- `out/TRAINING.json`: ครบ24ชุดรอบแรก; `continuation/out/TRAINING.json`: ครบ24ชุดรอบสอง',
'- `continuation/out/LOCK.json`: สูตรที่ล็อกก่อนทดสอบ; `continuation/out/VALIDATION.json`: ผลทดสอบ',
'- `VERIFICATION.json`: ผลกระทบยอดและตรวจความคงเดิม; `PLAN.md` และ `continuation/PLAN.md`: กรอบการค้นหา',
'- `out/design_log.txt`, `continuation/out/design_log.txt`: รายละเอียดการรัน',
'','สถานะสุดท้าย: จังหวะเข้าใหม่ที่ซ้ำกับ A/Bต่ำมีจริง แต่ยังไม่พบกำไรหลังต้นทุนที่ยืนยันได้ในช่วงทดสอบของการค้นหานี้']
(ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(ROOT/'README.md').write_text('# Rule C research — 2026-11-01\n\nStatus: NOT_CONFIRMED. No version promoted.\n\nSee [results](RESULTS.md), [initial plan](PLAN.md), [adaptive follow-up](continuation/PLAN.md), and VERIFICATION.json.\n\nDesign2010–2016; reused validation2017–2019; 2020+ not read. All24 initial and24 opposite-direction candidates retained.\n',encoding='utf-8')
print(json.dumps(verify,indent=2));print('Report:',ROOT/'RESULTS.md')
