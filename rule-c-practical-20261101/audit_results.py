"""Audit saved experiments and produce a descriptive report; never load new prices."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

baseline = ROOT.parent / 'v1-r2/out/LOCK.json'
baseline_metrics = read(baseline)['training_metrics']
audit = []
all_rows = []
for label, folder in [('รอบแรก', ROOT), ('เพิ่มเวลาถือ/เป้ากำไร', ROOT / 'exit_followup')]:
    out = folder / 'out'
    lock = read(out / 'LOCK.json')
    train = read(out / 'TRAINING.json')
    validation = read(out / 'VALIDATION.json')
    assert sha(out / 'LOCK.json') == (out / 'LOCK.sha256').read_text().strip()
    for path, expected in {**lock['sources'], **lock['training_data_hashes']}.items():
        assert sha(Path(path)) == expected, path
    assert sha(baseline) == lock['baseline_lock_sha256']
    assert train['ab_metrics'] == baseline_metrics
    assert len(train['rows']) == train['prefix_checks'] == 24
    assert [r['spec'] for r in train['rows']] == read(out / 'CANDIDATES.json')
    assert lock['selected'] == []
    assert validation == dict(status='NO_TRAINING_CANDIDATE', results=[], years_read=[])
    for r in train['rows']:
        m = r['metrics']
        assert m['net'] < 0 and not m['eligible']
        assert m['observed_sessions'] == m['traded_sessions'] + m['zero_trade_sessions']
        assert abs(m['trades']/m['observed_sessions']-m['trades_per_session']) < 1e-12
        assert abs(sum(y['net'] for y in r['yearly'].values()) - m['net']) < 1e-6
    record = dict(round=label, cells=24, prefix_checks=24, sources_and_data_hashes_match=True,
                  baseline_metrics_match=True, annual_net_reconciles=True,
                  positive_net=0, selected=0, validation_years_read=[],
                  cells_with_close_crossings=sum(r['metrics']['market_close_crossings']>0 for r in train['rows']))
    audit.append(record)
    all_rows.extend(train['rows'])

best = max(all_rows, key=lambda r:r['metrics']['net'])
best_overlap = max((r for r in all_rows if r['metrics']['overlap']<=.3), key=lambda r:r['metrics']['net'])
best_close = max((r for r in all_rows if r['metrics']['overlap']<=.3 and r['metrics']['market_close_crossings']==0 and r['metrics']['session_crossings']==0), key=lambda r:r['metrics']['net'])

lines = ['# ผลทดลองกฎ C: โอกาสที่เกิดเป็นประจำ โดยไม่กำหนดโควตาต่อวัน', '',
    'วันที่ 1 พฤศจิกายน 2026 — ยังไม่พบกฎ C ที่ผ่านเกณฑ์ในชุดทดลองนี้ และไม่มีการเปลี่ยน v1-r2 หรือสร้างรุ่นใหม่', '',
    '## ขอบเขตและผล', '',
    'ทดสอบ 48 สูตรบนปีออกแบบ 2010–2016: แรงวิ่งตามด้วยการย่อ 20–50% ทั้งตามแรงเดิมและสวนแรงเดิม 24 สูตร แล้วทดลองเพิ่มเวลาถือและเป้ากำไรของฝั่งตามแรงเดิมอีก 24 สูตร ทุกสูตรขาดทุนหลังต้นทุน จึงไม่มีสูตรเข้าสู่การทดสอบปี 2017–2019 และไม่ได้อ่านราคาปี 2020 เป็นต้นไปในงานชุดนี้', '',
    'ไม่มีการบังคับวันละหนึ่งไม้ และไม่มีการห้ามเข้าเพียงเพราะ A/B ถืออยู่เพื่อทำให้ตัวเลขซ้ำต่ำลง วัด overlap จากสัดส่วนไม้ C ที่เข้าขณะที่ A หรือ B ยังถือสถานะ ตามเกณฑ์ไม่เกิน 30%', '',
    'ตัวเลขด้านล่างเป็น C เดี่ยวที่ 0.1 lot (10 oz), เงินเริ่มต้น 100,000 บาท, USD/THB คงที่ 33.77 และ spread รวม 0.168 USD/oz; ต้นทุนเพิ่มสมมติรวม commission 0.01 และ slippage 0.02 USD/oz ต่อด้าน ยังไม่ใช่การจำลอง margin call หรือบัญชีจริง', '',
    '## ตัวอย่างที่ใช้วินิจฉัย — ทุกสูตรในตารางไม่ผ่าน', '',
    '| รายการ | สูตร | ไม้ใน 7 ปี | ไม้/วันตลาดที่มีข้อมูล | วันที่มีเข้า | ซ้ำ A/B | สุทธิหลัง spread (บาท) | สุทธิเมื่อเพิ่มต้นทุน (บาท) |',
    '|---|---|---:|---:|---:|---:|---:|---:|']
for label, r in [('ขาดทุนน้อยที่สุด', best), ('ขาดทุนน้อยที่สุดเมื่อซ้ำ ≤30%', best_overlap), ('ซ้ำ ≤30% และไม่พบข้ามตลาด/วัน', best_close)]:
    m=r['metrics']
    lines.append(f"| {label} | {r['spec']['id']} | {m['trades']:,} | {m['trades_per_session']:.2f} | {m['active_session_fraction']:.1%} | {m['overlap']:.2%} | {m['net']:,.2f} | {m['example_net']:,.2f} |")
lines += ['',
    'ความถี่หารด้วย 1,815 trading sessions ที่ปรากฏในข้อมูล รวมวันที่ระบบงดเทรดและวันที่ไม่มีไม้ ไม่ใช่ค่าเฉลี่ยเฉพาะวันที่เข้า จำนวน 1.08–12.66 ไม้ต่อ session ใน 48 สูตรนี้ไม่ได้แปลว่าได้กำไรหรือเข้าได้ทุกวัน สูตรที่ขาดทุนน้อยที่สุดมีเข้า 1,263 sessions และไม่มีเข้า 552 sessions', '',
    f"สูตรที่ขาดทุนน้อยที่สุดมี PF {best['metrics']['profit_factor']:.4f}, equity drawdown {best['metrics']['dd']:,.2f} บาท หรือ {best['metrics']['dd_pct']:.2f}% จากยอดสูงสุด และเฉพาะปี 2014–2016 ขาดทุน {abs(best['metrics']['net_2014_on']):,.2f} บาท จึงไม่มีเหตุผลรองรับการนำไปใช้จริงจากผลนี้", '',
    '## ข้อจำกัดการปิดสถานะและการประเมิน', '',
    'พบ 16 จาก 24 สูตรในแต่ละรอบมีอย่างน้อยหนึ่งไม้ปิดข้ามเวลาตลาดปิด/ข้าม session ตัวจำลองส่งปิดตามปฏิทินที่กำหนด ณ quote ที่มีอยู่ หากไม่มี quote ให้ปิดก่อนกำหนด จะไม่ย้อนกลับไปเลือก quote สุดท้ายโดยอาศัยอนาคต สูตรเหล่านี้ถูกตัดสิทธิ์ แต่ยังเก็บผลดิบไว้ ห้ามอ้างว่าทั้งชุดปิดก่อนตลาดได้ทุกไม้; ตารางผลทั้งหมดระบุจำนวน crossing ชัดเจน', '',
    'ปฏิทินปิดรายวันใช้เวลา New York 16:55 พร้อมการงดเทรดวันหยุดตามระบบเดิม ยังไม่ใช่เอกสารเวลาซื้อขายย้อนหลังครบถ้วนจากโบรกเกอร์ ส่วนคำสั่ง stop/target ตรวจจากราคาปิดนาทีแล้วออกที่ quote ถัดไป ไม่ใช่การรับประกัน fill ภายในนาที', '',
    'บางสูตรขาดทุนเกินเงินเริ่มต้น แต่ตัวจำลองยังคงคำนวณเพื่อวินิจฉัย ไม่ใช่เส้นทางบัญชีที่เทรดต่อได้จริง และถูกตัดสิทธิ์ด้วยเงื่อนไข equity ต้องเป็นบวก', '',
    '## การตรวจสอบและข้อสรุป', '',
    'ตรวจ source/data hashes และ lock ครบทั้งสองรอบ, ผล A/B ตรงกับ v1-r2 ที่ล็อกไว้ทุกช่อง, ผลสุทธิรายปีรวมตรงกับผลทั้งหมด และผลการตรวจตัดข้อมูลอนาคตแล้วเล่นซ้ำ (prefix) 24/24 สูตรต่อรอบผ่านตามบันทึกการรัน มีการตรวจสัญญาณสังเคราะห์ 96 prefixes และตัวจำลองคำสั่งด้วยกรณีสังเคราะห์ด้วย', '',
    'รอบที่สองออกแบบหลังเห็นผลรอบแรก จึงเป็นการค้นหาแบบปรับตามผลบนข้อมูลออกแบบ ไม่ใช่หลักฐานอิสระ สถิติรายรอบไม่ได้แก้ผลจากการค้นหาทั้งประวัติโปรเจค', '',
    'หมายเหตุแผนรอบแรกระบุจัดอันดับ net/DD ก่อน แต่โค้ดเดิมจัด daily t ก่อนแล้วจึง net/DD ไม่มีสูตรผ่านเกณฑ์ จึงไม่กระทบการเลือกหรือการเข้าถึงข้อมูลทดสอบ แผนรอบสองระบุลำดับจริงไว้แล้ว โดยไม่แก้หลักฐานที่ล็อกของรอบแรก', '',
    'ผลนี้แสดงว่าการเพิ่มจำนวนโอกาสด้วยโครงสร้างแรงวิ่ง–ย่อและการยืดทางออกชุดนี้ยังไม่ให้ edge หลังต้นทุน ไม่ใช่ข้อพิสูจน์ว่าไม่มี Rule C อื่นที่ทำได้ เกณฑ์เป้าหมายต่อไปยังเป็นกำไรหลังต้นทุน ความเสี่ยงที่ยอมรับได้ จำนวนตัวอย่างที่ประเมินได้ และ overlap ≤30% โดยไม่มีโควตาไม้ต่อวัน', '',
    '## ผลดิบทั้ง 48 สูตร', '',
    '| สูตร | ไม้ | ไม้/session | สุทธิบาท | PF | overlap | ข้ามตลาดปิด |',
    '|---|---:|---:|---:|---:|---:|---:|']
for r in all_rows:
    m=r['metrics']
    lines.append(f"| {r['spec']['id']} | {m['trades']} | {m['trades_per_session']:.2f} | {m['net']:,.2f} | {m['profit_factor']:.3f} | {m['overlap']:.2%} | {m['market_close_crossings']} |")
(ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
(ROOT/'VERIFICATION.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
print('Best no-crossing and overlap <=30%:',best_close['spec']['id'],best_close['metrics']['net'])
print('REPORT',ROOT/'RESULTS.md')
