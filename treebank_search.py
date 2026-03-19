import streamlit as st
import json
import os
from collections import Counter
from pathlib import Path

st.set_page_config(page_title="Treebank Search", page_icon="🌲", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .card {
    border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 8px; background: white;
  }
  .card:hover { border-color: #94a3b8; }

  .sent { font-size: 14px; color: #374151; line-height: 1.6; margin-bottom: 8px; }
  .hl { background: #fef3c7; border-radius: 3px; padding: 1px 3px;
        font-weight: 700; color: #92400e; }

  .info-line {
    display: flex; align-items: center; gap: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
  }
  .word  { font-weight: 700; color: #1e293b; }
  .arrow { color: #9ca3af; }
  .upos  { background: #ede9fe; color: #6d28d9; font-weight: 700;
           padding: 1px 6px; border-radius: 4px; }
  .dep   { background: #dbeafe; color: #1d4ed8; font-weight: 700;
           padding: 1px 6px; border-radius: 4px; }
  .head  { color: #374151; font-style: italic; }
  .root-tag { background: #dcfce7; color: #166534; font-weight: 700;
              padding: 1px 6px; border-radius: 4px; }

  .badge {
    display: inline-block; font-size: 11px; font-weight: 600;
    padding: 2px 7px; border-radius: 4px; margin: 2px;
  }
  .b-upos  { background: #ede9fe; color: #6d28d9; }
  .b-dep   { background: #dbeafe; color: #1d4ed8; }
  .b-feats { background: #fce7f3; color: #9d174d; font-size: 10px; }
</style>
""", unsafe_allow_html=True)


# ── Load treebank (treebank_data.json must sit next to this script) ───────────
@st.cache_data(show_spinner="Loading treebank…")
def load_data():
    here = Path(__file__).parent
    data_path = here / "treebank_data.json"
    if not data_path.exists():
        return None, f"treebank_data.json not found in {here}"
    with open(data_path, encoding="utf-8") as f:
        return json.load(f), None

sentences, load_error = load_data()

if load_error:
    st.error(load_error)
    st.stop()


# ── Helpers ───────────────────────────────────────────────────────────────────
def find_hits(word: str):
    w = word.lower().strip()
    hits = []
    for sent in sentences:
        for tok in sent["tokens"]:
            if tok["form"].lower() == w or tok["lemma"].lower() == w:
                hits.append((sent, tok))
    return hits


def rank_hits(hits, query: str):
    if not query.strip():
        return hits

    q = query.strip()
    q_words = q.lower().split()
    q_is_question = q.endswith("?")
    q_starts_wh = q_words[0] in {"who","what","when","where","why","how","which","whom","whose"} if q_words else False

    def score(item):
        sent, tok = item
        s = 0
        text = sent["text"]
        forms = [t["form"].lower() for t in sent["tokens"]]

        is_q = text.strip().endswith("?")
        if q_is_question and is_q:      s += 40
        if q_is_question and not is_q:  s -= 15
        if not q_is_question and not is_q: s += 10

        starts_wh = forms[0] in {"who","what","when","where","why","how","which","whom","whose"}
        if q_starts_wh and starts_wh:     s += 20
        if q_starts_wh and not starts_wh: s -= 10

        tok_pos = int(tok["id"]) - 1
        if tok_pos <= 2: s += 10

        n = len(sent["tokens"])
        if n <= 12:   s += 8
        elif n <= 20: s += 3
        elif n >= 40: s -= 8

        return s

    return sorted(hits, key=score, reverse=True)


def highlight_sentence(tokens, highlight_id):
    """Reconstruct sentence text with the target word highlighted."""
    parts = []
    for t in tokens:
        form = t["form"]
        if t["id"] == highlight_id:
            form = f'<span class="hl">{form}</span>'
        parts.append(form)
    # Simple reconstruction: join with spaces, fix spacing before punctuation
    text = " ".join(parts)
    import re
    text = re.sub(r' ([.,!?;:\)\]\}])', r'\1', text)
    text = re.sub(r'([\(\[\{]) ', r'\1', text)
    return text


def info_line(tok, tokens):
    """Build the key info: word → POS · deprel → head_word (or ROOT)."""
    word_html = f'<span class="word">{tok["form"]}</span>'
    upos_html = f'<span class="upos">{tok["upos"]}</span>'

    if tok["deprel"] == "root" or tok["head"] == "0":
        dep_html = f'<span class="root-tag">root</span>'
        return f'<div class="info-line">{word_html} <span class="arrow">→</span> {upos_html} {dep_html}</div>'
    else:
        # Find the head token's form
        head_tok = next((t for t in tokens if t["id"] == tok["head"]), None)
        head_form = head_tok["form"] if head_tok else f'[{tok["head"]}]'
        dep_html  = f'<span class="dep">{tok["deprel"]}</span>'
        head_html = f'<span class="head">← {head_form}</span>'
        return f'<div class="info-line">{word_html} <span class="arrow">→</span> {upos_html} · {dep_html} {head_html}</div>'


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌲 Treebank Search")
    st.markdown(f"**EWT UD treebank** · {len(sentences):,} sentences")
    st.markdown("---")
    st.markdown("**Optional:** upload an additional `.conllu` file to search instead.")
    uploaded = st.file_uploader("Upload .conllu", type=["conllu", "txt"])

    if uploaded:
        @st.cache_data(show_spinner="Parsing uploaded file…")
        def parse_upload(raw: bytes):
            sents = []
            cur = {"sent_id": "", "text": "", "tokens": []}
            for line in raw.decode("utf-8").splitlines():
                line = line.rstrip()
                if line.startswith("# sent_id"):
                    cur["sent_id"] = line.split("=", 1)[1].strip()
                elif line.startswith("# text"):
                    cur["text"] = line.split("=", 1)[1].strip()
                elif line == "":
                    if cur["tokens"]:
                        sents.append(cur)
                    cur = {"sent_id": "", "text": "", "tokens": []}
                elif line.startswith("#"):
                    continue
                else:
                    parts = line.split("\t")
                    if len(parts) >= 8 and "-" not in parts[0] and "." not in parts[0]:
                        cur["tokens"].append({
                            "id": parts[0], "form": parts[1], "lemma": parts[2],
                            "upos": parts[3], "xpos": parts[4], "feats": parts[5],
                            "head": parts[6], "deprel": parts[7],
                        })
            if cur["tokens"]:
                sents.append(cur)
            return sents

        sentences = parse_upload(uploaded.read())
        st.success(f"Using uploaded file: {len(sentences):,} sentences")

    st.markdown("---")
    st.markdown("**How ranking works**")
    st.markdown(
        "Paste the sentence you're annotating in the ranking box. "
        "If it's a question, questions in the treebank rise to the top. "
        "If it's a subordinate clause, those appear first instead."
    )


# ── Main UI ───────────────────────────────────────────────────────────────────
st.title("🌲 Treebank Lookup")

col1, col2 = st.columns([1, 2])
with col1:
    word = st.text_input("🔍 Word", placeholder="e.g.  when", label_visibility="visible")
with col2:
    query = st.text_input(
        "📝 Your sentence (optional — for ranking)",
        placeholder="e.g.  When is she eating?  →  questions ranked first"
    )

if not word.strip():
    st.markdown("""
    <div style="text-align:center;padding:60px 0;color:#9ca3af">
      <div style="font-size:48px">🌲</div>
      <div style="font-size:18px;font-weight:600;margin-top:12px">Type a word to search</div>
      <div style="font-size:14px;margin-top:6px">Try <em>when</em>, <em>which</em>, <em>because</em>, <em>although</em>…</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# Search + rank
hits = find_hits(word)
if not hits:
    st.warning(f"No results for **{word}**.")
    st.stop()

hits = rank_hits(hits, query)

# Filters
all_upos = Counter(tok["upos"]   for _, tok in hits)
all_dep  = Counter(tok["deprel"] for _, tok in hits)

fc1, fc2, fc3 = st.columns([1, 1, 1])
with fc1:
    upos_opts = ["All"] + [f"{u}  ({c})" for u, c in all_upos.most_common()]
    upos_sel  = st.selectbox("Filter UPOS", upos_opts)
    upos_f = upos_sel.split("  (")[0] if upos_sel != "All" else None
with fc2:
    dep_opts = ["All"] + [f"{d}  ({c})" for d, c in all_dep.most_common()]
    dep_sel  = st.selectbox("Filter DEPREL", dep_opts)
    dep_f = dep_sel.split("  (")[0] if dep_sel != "All" else None
with fc3:
    max_show = st.slider("Show up to", 5, 100, 25)

if upos_f:
    hits = [(s, t) for s, t in hits if t["upos"] == upos_f]
if dep_f:
    hits = [(s, t) for s, t in hits if t["deprel"] == dep_f]

st.markdown("---")
total = len(hits)
ranked_note = "ranked by similarity to your sentence" if query.strip() else "paste a sentence above to rank by context"
st.markdown(f"**{total}** match{'es' if total != 1 else ''} for **{word}** · {ranked_note}")

# Tag summary
with st.expander("📊 Tag distribution across all matches"):
    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        st.markdown("**UPOS**")
        for u, c in Counter(t["upos"] for _, t in hits).most_common():
            st.markdown(f'<span class="badge b-upos">{u}</span> {c}×', unsafe_allow_html=True)
    with ec2:
        st.markdown("**DEPREL**")
        for d, c in Counter(t["deprel"] for _, t in hits).most_common():
            st.markdown(f'<span class="badge b-dep">{d}</span> {c}×', unsafe_allow_html=True)
    with ec3:
        st.markdown("**Features**")
        for feat, c in Counter(t["feats"] for _, t in hits if t["feats"] != "_").most_common(12):
            st.markdown(f'<span class="badge b-feats">{feat}</span> {c}×', unsafe_allow_html=True)

# Results
for sent, tok in hits[:max_show]:
    sent_html = highlight_sentence(sent["tokens"], tok["id"])
    key_info  = info_line(tok, sent["tokens"])

    card = f"""
    <div class="card">
      <div class="sent">{sent_html}</div>
      {key_info}
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)