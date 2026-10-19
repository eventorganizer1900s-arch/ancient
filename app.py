from flask import Flask, request, render_template_string, send_file
import io, csv, secrets, string
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)
TEMPLATE = r"""
<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ancient Vibe Events — Ticket Generator</title>
<style>
:root{--gold:#c49a50;--ink:#141414}*{box-sizing:border-box}body{margin:0;background:#101010;color:#f7f3eb;font-family:Arial,sans-serif}
header{padding:26px 18px;text-align:center;border-bottom:1px solid #493b23;background:linear-gradient(135deg,#111,#241d12)}
.brand{letter-spacing:4px;color:#d8b56f;font-size:12px}h1{margin:10px 0 5px;font-family:Georgia,serif;font-size:clamp(27px,7vw,42px)}.sub{color:#c9c1b2;font-size:14px}
main{max-width:920px;margin:22px auto;padding:0 14px;display:grid;grid-template-columns:1fr;gap:18px}.panel{background:#1b1b1b;border:1px solid #393126;border-radius:16px;padding:18px}
label{display:block;color:#d9c8a5;font-size:13px;margin:12px 0 6px}input,select{width:100%;padding:13px;border-radius:9px;border:1px solid #4b453b;background:#101010;color:white;font-size:16px}
button,.btn{border:0;border-radius:10px;padding:13px 16px;background:#c49a50;color:#15110a;font-weight:bold;font-size:15px;display:inline-block;text-decoration:none;cursor:pointer;margin-top:14px}
button.secondary,.btn.secondary{background:#34312c;color:#fff;border:1px solid #5b5140}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.muted{color:#aaa;font-size:13px;line-height:1.5}.ticket{background:#fff;color:#171717;border-radius:14px;padding:20px;text-align:center;max-width:420px;margin:0 auto}.ticket h2{font-family:Georgia,serif;margin:0}.ticket img{width:220px;max-width:100%;margin:12px auto}.code{font-family:monospace;word-break:break-word;background:#eee;padding:8px;border-radius:7px}.result{margin-top:16px}.warning{font-size:12px;color:#d8c9a9;line-height:1.5}.foot{text-align:center;padding:24px;color:#8e877b;font-size:12px}
@media(min-width:760px){main{grid-template-columns:1fr 1fr}.full{grid-column:1/-1}}
</style></head><body>
<header><div class="brand">ANCIENT VIBE</div><h1>EVENT TICKET STUDIO</h1><div class="sub">Create • Generate • Verify</div></header>
<main>
<section class="panel"><h2>Create tickets</h2>
<form method="post">
<label>Event name</label><input name="event" required maxlength="90" value="{{ event or 'Ancient Vibe Events' }}">
<div class="grid"><div><label>Ticket quantity</label><input name="qty" type="number" min="1" max="1000" value="{{ qty or 10 }}" required></div><div><label>Price (ETB)</label><input name="price" type="number" min="0" value="{{ price or 0 }}" required></div></div>
<label>Ticket type</label><select name="kind"><option {{'selected' if kind=='General Admission' else ''}}>General Admission</option><option {{'selected' if kind=='VIP' else ''}}>VIP</option><option {{'selected' if kind=='Early Bird' else ''}}>Early Bird</option></select>
<label>Event date (optional)</label><input name="date" placeholder="e.g. 2026-12-20" value="{{ date or '' }}">
<button type="submit">Generate unique QR tickets</button></form>
<p class="muted">Generates separate QR codes and ticket IDs, plus a printable PDF and CSV list.</p>
</section>
<section class="panel"><h2>How it works</h2><p class="muted">1. Enter event details and quantity.<br>2. Generate the tickets.<br>3. Download the PDF to print, or CSV to manage IDs.<br>4. At the door, scan a ticket QR to read its ticket ID.</p><p class="warning">Demo note: this starter version creates unique ticket codes but does not provide a secure online check-in database. A code can be copied; prevent duplicate entry by adding a server-side verification/check-in system before selling tickets.</p></section>
{% if tickets %}<section class="panel full"><h2>Tickets generated</h2><p class="muted">{{ tickets|length }} ticket codes created for {{ event }}.</p>
<a class="btn" href="/download/pdf?batch={{ batch }}">Download printable PDF</a> <a class="btn secondary" href="/download/csv?batch={{ batch }}">Download CSV</a>
<div class="result ticket"><h2>{{ event }}</h2><p>{{ kind }} • {{ date or 'Date to be announced' }}</p><img src="/qr/{{ batch }}/{{ tickets[0].id }}" alt="Ticket QR"><div class="code">{{ tickets[0].id }}</div><p>ETB {{ price }}</p><small>Sample ticket — download PDF for all tickets</small></div>
{% endif %}
</section></main><div class="foot">ANCIENT VIBE EVENTS • GOOD VIBES, GREAT PEOPLE</div></body></html>"""
batches = {}

def make_qr(data):
    q = qrcode.QRCode(box_size=8, border=4, error_correction=qrcode.constants.ERROR_CORRECT_H)
    q.add_data(data); q.make(fit=True)
    im = q.make_image(fill_color="black", back_color="white").convert("RGB")
    bio = io.BytesIO(); im.save(bio, format="PNG"); bio.seek(0); return bio

@app.route("/", methods=["GET","POST"])
def home():
    ctx = dict(event="Ancient Vibe Events", qty=10, price=0, kind="General Admission", date="", tickets=None, batch=None)
    if request.method == "POST":
        event = request.form.get("event","Ancient Vibe Events").strip()[:90] or "Ancient Vibe Events"
        qty = max(1, min(1000, int(request.form.get("qty",10))))
        price = max(0, int(request.form.get("price",0)))
        kind = request.form.get("kind","General Admission")
        date = request.form.get("date","").strip()[:40]
        batch = secrets.token_urlsafe(8)
        tickets = []
        for _ in range(qty):
            tid = "AV-" + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            tickets.append({"id":tid, "event":event, "price":price, "kind":kind, "date":date})
        batches[batch] = {"event":event,"price":price,"kind":kind,"date":date,"tickets":tickets}
        ctx = dict(event=event,qty=qty,price=price,kind=kind,date=date,tickets=tickets,batch=batch)
    return render_template_string(TEMPLATE, **ctx)

@app.route("/qr/<batch>/<ticket_id>")
def qr(batch,ticket_id):
    data = batches.get(batch)
    if not data or not any(t["id"]==ticket_id for t in data["tickets"]): return "Ticket not found",404
    return send_file(make_qr("ANCIENT VIBE TICKET|"+ticket_id), mimetype="image/png")

@app.route("/download/csv")
def download_csv():
    data = batches.get(request.args.get("batch"))
    if not data: return "Batch not found. Generate tickets again after server restart.",404
    out=io.StringIO(); w=csv.writer(out); w.writerow(["ticket_id","event","ticket_type","price_etb","event_date"])
    for t in data["tickets"]: w.writerow([t["id"],t["event"],t["kind"],t["price"],t["date"]])
    return send_file(io.BytesIO(out.getvalue().encode("utf-8-sig")),mimetype="text/csv",as_attachment=True,download_name="ancient_vibe_tickets.csv")

@app.route("/download/pdf")
def download_pdf():
    data = batches.get(request.args.get("batch"))
    if not data: return "Batch not found. Generate tickets again after server restart.",404
    out=io.BytesIO(); c=canvas.Canvas(out,pagesize=A4); W,H=A4
    for i,t in enumerate(data["tickets"]):
        if i and i%4==0: c.showPage()
        slot=i%4; top=H-35-slot*195
        c.setStrokeColorRGB(.72,.55,.25); c.roundRect(35,top-165,W-70,160,10,stroke=1,fill=0)
        c.setFillColorRGB(.08,.08,.08); c.setFont("Helvetica-Bold",16); c.drawString(52,top-30,"ANCIENT VIBE EVENTS")
        c.setFont("Helvetica",10); c.drawString(52,top-49,t["event"][:55])
        c.drawString(52,top-66,t["kind"]+" | ETB "+str(t["price"]))
        c.drawString(52,top-82,t["date"] or "Date to be announced")
        img=ImageReader(make_qr("ANCIENT VIBE TICKET|"+t["id"]))
        c.drawImage(img,W-170,top-145,width=92,height=92,mask="auto")
        c.setFont("Helvetica-Bold",11); c.drawString(52,top-115,t["id"])
        c.setFont("Helvetica",8); c.drawString(52,top-132,"Keep this ticket. Each ticket has a unique QR code.")
    c.save(); out.seek(0)
    return send_file(out,mimetype="application/pdf",as_attachment=True,download_name="ancient_vibe_tickets.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
