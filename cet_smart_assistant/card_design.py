"""Scoped, offline reviewer styling; no collection or scheduling writes."""

STYLE = """<style>
.cet-card{--ink:#203530;--muted:#64756f;--paper:#fff;--soft:#f2f6f3;--line:#dce6df;--accent:#28664e;box-sizing:border-box;max-width:860px;margin:28px auto;padding:36px;text-align:left;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:24px;box-shadow:0 12px 40px #183b2810;font:16px/1.75 'Segoe UI','Microsoft YaHei',sans-serif;overflow-wrap:anywhere}
.cet-card *{box-sizing:border-box}.cet-card .cet-eyebrow{font-size:11px;letter-spacing:2px;font-weight:700;color:var(--muted)}
.cet-card .cet-word{font-size:clamp(32px,6vw,54px);line-height:1.2;font-weight:650;letter-spacing:-1px;margin:16px 0 24px}
.cet-card .cet-meaning{font-size:20px;padding:20px 0;border-top:1px solid var(--line);margin-bottom:12px}
.cet-card .cet-recall{color:var(--muted);padding-top:24px;border-top:1px solid var(--line)}
.cet-card .cet-focus{display:inline-block;background:var(--soft);color:var(--accent);padding:5px 12px;border-radius:100px;font-size:13px;font-weight:600}
.cet-card p{margin:10px 0}.cet-card .cet-reason{color:var(--muted);font-size:14px;margin:12px 0 22px}
.cet-card .cet-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.cet-card .cet-panel{padding:20px;background:var(--soft);border-radius:16px;min-width:0}
.cet-card h3{font-size:14px;margin:0 0 14px;color:var(--accent)}
.cet-card .cet-example{font-size:18px;line-height:1.6;font-weight:500}
.cet-card .cet-note{font-size:14px;color:var(--muted)}
.cet-card .cet-alternative{margin-top:18px;padding:18px 20px;border:1px solid var(--line);border-radius:16px}
.cet-card .cet-caution{font-size:13px;color:var(--muted);margin:18px 0}
.cet-card details{font-size:12px;color:var(--muted)}.cet-card summary{cursor:pointer}
.cet-card .cet-footer{margin-top:24px;padding-top:20px;border-top:1px solid var(--line)}
.cet-card button{font:600 14px/1.5 'Segoe UI','Microsoft YaHei',sans-serif;color:var(--accent);background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:11px 18px;cursor:pointer;white-space:normal}
.cet-card button:hover{filter:brightness(.94)}.cet-card button:focus-visible,.cet-card summary:focus-visible{outline:3px solid #549778;outline-offset:3px}
.nightMode .cet-card,.night_mode .cet-card{--ink:#e3eee8;--muted:#a6b9ae;--paper:#202b26;--soft:#2a3830;--line:#405348;--accent:#9bdbb7;box-shadow:none}
@media(max-width:560px){.cet-card{margin:12px auto;padding:22px 18px;border-radius:18px}.cet-card .cet-grid{grid-template-columns:1fr}.cet-card .cet-word{margin-bottom:20px}.cet-card .cet-panel{padding:16px}}
</style>"""


def render_card(front, back=None, guidance=""):
    """Fields are already Anki-rendered HTML, preserving media and formatting."""
    body = ('<div class="cet-recall">先回想词义，再显示答案</div>' if back is None else
            f'<div id="answer" class="cet-meaning">{back}</div>{guidance}')
    return (STYLE + '<article class="cet-card"><div class="cet-eyebrow">CET · VOCABULARY</div>'
            f'<div class="cet-word">{front}</div>{body}</article>')
