import streamlit as st
import json
import re
from collections import Counter
from pathlib import Path

st.set_page_config(page_title="Treebank Search", page_icon="🌲", layout="wide")

# Detect Streamlit's theme setting
try:
    _theme = st.get_option("theme.base") or "light"
except:
    _theme = "light"
_is_dark = _theme == "dark"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {{
    --bg:         {'#1c1b19' if _is_dark else '#faf9f7'};
    --bg-card:    {'#252320' if _is_dark else '#ffffff'};
    --bg-sidebar: {'#252320' if _is_dark else '#f3f1ee'};
    --border:     {'#3a3732' if _is_dark else '#e0dcd6'};
    --border-sub: {'#2e2b28' if _is_dark else '#f0ede8'};
    --text:       {'#e8e4de' if _is_dark else '#1a1a1a'};
    --text-muted: {'#a09890' if _is_dark else '#555555'};
    --text-dim:   {'#6b6560' if _is_dark else '#999999'};
    --hl-bg:      {'#5a3520' if _is_dark else '#f5e6d3'};
    --hl-text:    {'#e8a87c' if _is_dark else '#8b4513'};
    --hl-row:     {'#3a2510' if _is_dark else '#fdf3e8'};
    --hover-row:  {'#2e2b28' if _is_dark else '#faf9f7'};
    --upos-bg:    {'#2d1f5e' if _is_dark else '#ede9fe'};
    --upos-text:  {'#c4b5fd' if _is_dark else '#5b21b6'};
    --dep-bg:     {'#1e2d5e' if _is_dark else '#dbeafe'};
    --dep-text:   {'#93c5fd' if _is_dark else '#1e40af'};
    --root-bg:    {'#14382a' if _is_dark else '#dcfce7'};
    --root-text:  {'#86efac' if _is_dark else '#166534'};
    --feat-bg:    {'#4a1533' if _is_dark else '#fce7f3'};
    --feat-text:  {'#f9a8d4' if _is_dark else '#9d174d'};
    --accent:     #c97b4b;
  }}

  /* ── Global font override ── */
  html, body, [class*="css"], .stApp,
  .stTextInput input, .stSelectbox, label,
  .stMarkdown, p, div, span, button,
  [data-testid="stSidebar"] * {{
    font-family: 'Lora', Georgia, serif !important;
  }}
  .mono, .info-line, .tok-table, .badge {{
    font-family: 'JetBrains Mono', monospace !important;
  }}

  html, body, .stApp {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
  }}

  h1 {{
    font-family: 'Lora', Georgia, serif !important;
    font-weight: 600 !important; font-size: 28px !important;
    color: var(--text) !important;
    letter-spacing: -0.01em; margin-bottom: 4px !important;
  }}
  h2, h3 {{ font-family: 'Lora', Georgia, serif !important; font-weight: 600 !important; color: var(--text) !important; }}

  [data-testid="stSidebar"] {{
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
  }}

  [data-testid="collapsedControl"] span,
  [data-testid="stSidebarCollapseButton"] span,
  button[kind="headerNoPadding"] span {{
    font-size: 0 !important; visibility: hidden !important;
  }}

  .stTextInput input {{
    font-family: 'Lora', Georgia, serif !important;
    font-size: 15px !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    background: var(--bg-card) !important;
    color: var(--text) !important;
  }}
  .stTextInput input:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(201,123,75,0.15) !important;
  }}
  .stTextInput label, .stSelectbox label, .stSlider label {{
    font-family: 'Lora', Georgia, serif !important;
    font-size: 13px !important;
    color: var(--text-muted) !important;
  }}

  .card {{
    border: 1px solid var(--border);
    border-radius: 4px; padding: 14px 18px;
    margin-bottom: 4px; background: var(--bg-card);
  }}
  .card:hover {{ border-color: var(--accent); }}

  .sent {{
    font-family: 'Lora', Georgia, serif !important;
    font-size: 15px; color: var(--text);
    line-height: 1.75; margin-bottom: 10px;
  }}
  .hl {{
    background: var(--hl-bg); border-radius: 2px;
    padding: 1px 3px; font-weight: 600; color: var(--hl-text);
  }}

  .info-line {{
    display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px; color: var(--text-muted); margin-top: 2px;
  }}
  .iword    {{ font-weight: 600; color: var(--text); }}
  .arrow    {{ color: var(--border); }}
  .sep      {{ color: var(--border); }}
  .upos     {{ background: var(--upos-bg); color: var(--upos-text); font-weight: 600;
              padding: 1px 7px; border-radius: 3px; font-size: 11px; }}
  .dep      {{ background: var(--dep-bg); color: var(--dep-text); font-weight: 600;
              padding: 1px 7px; border-radius: 3px; font-size: 11px; }}
  .ihead    {{ color: var(--text-dim); font-style: italic; }}
  .root-tag {{ background: var(--root-bg); color: var(--root-text); font-weight: 600;
              padding: 1px 7px; border-radius: 3px; font-size: 11px; }}

  .tok-table {{
    width: 100%; border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace !important; font-size: 12px;
  }}
  .tok-table th {{
    text-align: left; color: var(--text-dim); font-weight: 500; font-size: 11px;
    padding: 5px 10px; border-bottom: 1px solid var(--border);
    text-transform: uppercase; letter-spacing: 0.06em;
  }}
  .tok-table td {{ padding: 5px 10px; border-bottom: 1px solid var(--border-sub); color: var(--text); }}
  .tok-table tr.hl-row td {{ background: var(--hl-row); }}
  .tok-table tr:hover td  {{ background: var(--hover-row); }}
  .t-upos  {{ color: var(--upos-text); font-weight: 500; }}
  .t-dep   {{ color: var(--dep-text); font-weight: 500; }}
  .t-feats {{ color: var(--feat-text); font-size: 11px; }}

  .badge {{
    display: inline-block; font-size: 11px; font-weight: 500;
    font-family: 'JetBrains Mono', monospace !important;
    padding: 2px 8px; border-radius: 3px; margin: 2px;
  }}
  .b-upos  {{ background: var(--upos-bg); color: var(--upos-text); }}
  .b-dep   {{ background: var(--dep-bg);  color: var(--dep-text);  }}
  .b-feats {{ background: var(--feat-bg); color: var(--feat-text); }}

  .stButton button {{
    font-family: 'Lora', Georgia, serif !important;
    font-size: 12px !important; color: var(--text-dim) !important;
    background: none !important; border: none !important;
    padding: 2px 0 !important; cursor: pointer !important;
    text-decoration: underline !important;
    text-underline-offset: 3px !important;
    text-decoration-color: var(--border) !important;
  }}
  .stButton button:hover {{ color: var(--accent) !important; text-decoration-color: var(--accent) !important; }}

  hr {{ border: none; border-top: 1px solid var(--border); margin: 16px 0; }}
</style>
""", unsafe_allow_html=True)


# ── Load treebank ─────────────────────────────────────────────────────────────
CONLLU_URL = (
    "https://raw.githubusercontent.com/UniversalDependencies/"
    "UD_English-EWT/master/en_ewt-ud-train.conllu"
)

def parse_conllu(lines):
    sentences = []
    current = {"sent_id": "", "text": "", "tokens": []}
    for line in lines:
        line = line.rstrip()
        if line.startswith("# sent_id"):
            current["sent_id"] = line.split("=", 1)[1].strip()
        elif line.startswith("# text"):
            current["text"] = line.split("=", 1)[1].strip()
        elif line == "":
            if current["tokens"]:
                sentences.append(current)
            current = {"sent_id": "", "text": "", "tokens": []}
        elif not line.startswith("#"):
            parts = line.split("\t")
            if len(parts) >= 8 and "-" not in parts[0] and "." not in parts[0]:
                current["tokens"].append({
                    "id": parts[0], "form": parts[1], "lemma": parts[2],
                    "upos": parts[3], "xpos": parts[4], "feats": parts[5],
                    "head": parts[6], "deprel": parts[7],
                })
    if current["tokens"]:
        sentences.append(current)
    return sentences


@st.cache_data(show_spinner="Downloading treebank from Universal Dependencies…")
def load_data():
    import urllib.request, tempfile, os

    here = Path(__file__).parent

    # 1. Prefer a local .conllu file if it exists (for offline / local use)
    for name in ["en_ewt-ud-train.conllu", "treebank.conllu", "train.conllu"]:
        p = here / name
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return parse_conllu(f), None

    # 2. Download from the official UD GitHub repository
    try:
        with urllib.request.urlopen(CONLLU_URL, timeout=30) as resp:
            content = resp.read().decode("utf-8")
        return parse_conllu(content.splitlines()), None
    except Exception as e:
        return None, (
            f"Could not load treebank: {e}\n\n"
            "Place `en_ewt-ud-train.conllu` in the same folder as this script "
            "for offline use."
        )

sentences, load_error = load_data()
if load_error:
    st.error(load_error)
    st.stop()


# ── Load spaCy ────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading parser…")
def load_spacy():
    try:
        import spacy
        return spacy.load("en_core_web_sm"), None
    except ImportError:
        return None, "not_installed"
    except OSError:
        return None, "model_missing"

nlp, spacy_status = load_spacy()


# ── Search: exact word/phrase match ──────────────────────────────────────────
def is_phrase(q: str) -> bool:
    return len(q.strip().split()) > 1

def find_hits(query: str):
    """
    Single word  → match on form or lemma (case-insensitive).
    Multi-word   → consecutive token form match (case-insensitive).
    Collects ALL matching tokens (a sentence with 'what' twice gives 2 hits).
    Deduplication to one-per-sentence happens after ranking, so the best-
    matching token from each sentence is kept rather than an arbitrary one.
    Returns [(sentence, [matched_token_ids]), ...]
    """
    q = query.strip().lower()
    words = q.split()
    hits = []

    if len(words) == 1:
        for sent in sentences:
            for tok in sent["tokens"]:
                if tok["form"].lower() == q or tok["lemma"].lower() == q:
                    hits.append((sent, [tok["id"]]))
    else:
        for sent in sentences:
            toks  = sent["tokens"]
            forms = [t["form"].lower() for t in toks]
            for i in range(len(forms) - len(words) + 1):
                if forms[i:i + len(words)] == words:
                    hits.append((sent, [toks[i+j]["id"] for j in range(len(words))]))
    return hits


def deduplicate(hits):
    """Keep only the first (highest-scoring) hit per unique sentence text."""
    seen = set()
    result = []
    for sent, matched_ids in hits:
        key = sent["text"].strip().lower()
        if key not in seen:
            seen.add(key)
            result.append((sent, matched_ids))
    return result


# ── Ranking ───────────────────────────────────────────────────────────────────
def parse_query_word(query: str, search_word: str):
    """
    Parse the query sentence with spaCy and extract rich structural signals
    for the target word:

      dep        — the word's own dependency relation (e.g. "nsubj", "advmod")
      head_pos   — POS of the word it attaches to (e.g. VERB, NOUN)
      head_dep   — dep relation of the head itself (e.g. "ccomp", "relcl")
                   This is the key signal for embedded vs. root clauses:
                   in "tell me what you think", what's head is "think" whose
                   dep is "ccomp" — very different from "what did you eat?"
                   where what's head is "eat" whose dep is "ROOT"
      grandhead_pos — POS of the head's head (one more level up)
      is_embedded — True if the word sits inside a subordinate/embedded clause
                    (head's dep is ccomp, relcl, advcl, acl, etc.)

    Returns a dict, or None if spaCy unavailable or word not found.
    """
    if nlp is None:
        return None
    doc = nlp(query.strip())
    w   = search_word.strip().lower()

    EMBEDDED_DEPS = {"ccomp","xcomp","relcl","acl","advcl","parataxis","dep"}

    for token in doc:
        if token.text.lower() == w or token.lemma_.lower() == w:
            head      = token.head
            grandhead = head.head if head != token else None
            return {
                "dep":          token.dep_,
                "head_pos":     head.pos_,
                "head_dep":     head.dep_,
                "grandhead_pos": grandhead.pos_ if grandhead and grandhead != head else "",
                "is_embedded":  head.dep_ in EMBEDDED_DEPS,
            }
    return None


def rank_hits(hits, query: str, search_word: str = ""):
    """
    Rank hits by how closely the target word's structural role in each
    treebank sentence matches its role in the user's query sentence.

    Scoring priority (high → low):
      1. Exact deprel match                        (+60)
      2. Head's deprel matches                     (+40)  ← key for embedded vs root
      3. Head POS matches                          (+20)
      4. Grandhead POS matches                     (+10)
      5. Embedded/non-embedded agreement           (+15 / -20)
      6. Length preference (shorter = cleaner)

    The question-mark heuristic is intentionally removed — it was the source
    of the wrong ranking. Whether a sentence ends with ? is a surface feature
    that doesn't capture the actual syntactic role difference between
    interrogative and embedded uses of words like "what", "when", "where".
    """
    if not query.strip():
        return hits

    signals = parse_query_word(query, search_word) if search_word else None

    EMBEDDED_DEPS = {"ccomp","xcomp","relcl","acl","advcl","parataxis","dep"}
    UPOS_MAP = {"VERB":"VERB","AUX":"AUX","NOUN":"NOUN","PROPN":"PROPN",
                "ADJ":"ADJ","ADV":"ADV","ADP":"ADP","DET":"DET",
                "PRON":"PRON","SCONJ":"SCONJ","CCONJ":"CCONJ"}

    if signals:
        q_dep         = signals["dep"]
        q_head_pos    = signals["head_pos"]
        q_head_dep    = signals["head_dep"]
        q_ghead_pos   = signals["grandhead_pos"]
        q_is_embedded = signals["is_embedded"]

        def score_spacy(item):
            sent, matched_ids = item
            tok      = next(t for t in sent["tokens"] if t["id"] == matched_ids[0])
            head_tok = next((t for t in sent["tokens"] if t["id"] == tok["head"]), None)
            ghead_tok = next((t for t in sent["tokens"] if t["id"] == head_tok["head"]), None) if head_tok else None

            s = 0
            # 1. Target word's own dep
            if tok["deprel"] == q_dep:              s += 60
            elif tok["deprel"][:4] == q_dep[:4]:    s += 20

            # 2. Head's dep relation — most discriminating signal
            #    e.g. head dep=ccomp means embedded; head dep=root means main clause
            if head_tok:
                if head_tok["deprel"] == q_head_dep:            s += 40
                elif head_tok["deprel"][:4] == q_head_dep[:4]:  s += 15

            # 3. Head POS
            tb_head_pos = UPOS_MAP.get(head_tok["upos"], "") if head_tok else ""
            if tb_head_pos == q_head_pos:           s += 20

            # 4. Grandhead POS
            if ghead_tok and q_ghead_pos:
                tb_ghead_pos = UPOS_MAP.get(ghead_tok["upos"], "")
                if tb_ghead_pos == q_ghead_pos:     s += 10

            # 5. Embedded vs. root-level agreement
            tb_is_embedded = head_tok and head_tok["deprel"] in EMBEDDED_DEPS
            if q_is_embedded and tb_is_embedded:    s += 15
            elif q_is_embedded and not tb_is_embedded: s -= 20
            elif not q_is_embedded and tb_is_embedded: s -= 20

            # 6. Prefer shorter sentences
            n = len(sent["tokens"])
            if n <= 12:   s += 8
            elif n <= 20: s += 3
            elif n >= 40: s -= 8

            return s

        return sorted(hits, key=score_spacy, reverse=True)

    else:
        # Fallback with no spaCy: sort by sentence length only
        return sorted(hits, key=lambda item: len(item[0]["tokens"]))


# ── Rendering helpers ─────────────────────────────────────────────────────────
def highlight_sentence(tokens, highlight_ids: set):
    parts = []
    for t in tokens:
        form = t["form"]
        if t["id"] in highlight_ids:
            form = f'<span class="hl">{form}</span>'
        parts.append(form)
    text = " ".join(parts)
    text = re.sub(r' ([.,!?;:\)\]\}\'"])', r'\1', text)
    text = re.sub(r'([\(\[\{"\']) ', r'\1', text)
    return text


def info_line_single(tok, tokens):
    word = f'<span class="iword">{tok["form"]}</span>'
    upos = f'<span class="upos">{tok["upos"]}</span>'
    if tok["deprel"] == "root" or tok["head"] == "0":
        return (f'<div class="info-line">{word}'
                f' <span class="arrow">→</span> {upos}'
                f' <span class="root-tag">root</span></div>')
    head_tok  = next((t for t in tokens if t["id"] == tok["head"]), None)
    head_form = head_tok["form"] if head_tok else f'[{tok["head"]}]'
    dep  = f'<span class="dep">{tok["deprel"]}</span>'
    head = f'<span class="ihead">← {head_form}</span>'
    return (f'<div class="info-line">{word}'
            f' <span class="arrow">→</span> {upos}'
            f' <span class="sep">·</span> {dep} {head}</div>')


def info_line_phrase(matched_ids, tokens):
    return "\n".join(
        info_line_single(next(t for t in tokens if t["id"] == tid), tokens)
        for tid in matched_ids
    )


def token_detail_table(tokens, highlight_ids: set):
    rows = []
    for t in tokens:
        hl       = ' class="hl-row"' if t["id"] in highlight_ids else ""
        head_tok = next((x for x in tokens if x["id"] == t["head"]), None)
        head_str = (f'{t["head"]} ({head_tok["form"]})' if head_tok
                    else ("root" if t["head"] == "0" else t["head"]))
        feats    = t["feats"] if t["feats"] != "_" else ""
        rows.append(
            f'<tr{hl}>'
            f'<td>{t["id"]}</td><td><strong>{t["form"]}</strong></td>'
            f'<td>{t["lemma"]}</td><td class="t-upos">{t["upos"]}</td>'
            f'<td class="t-dep">{t["deprel"]}</td>'
            f'<td>{head_str}</td><td class="t-feats">{feats}</td></tr>'
        )
    return (
        '<table class="tok-table"><thead><tr>'
        '<th>#</th><th>Form</th><th>Lemma</th>'
        '<th>UPOS</th><th>DEPREL</th><th>Head</th><th>Feats</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌲 Treebank Search")
    st.markdown(f"EWT UD · {len(sentences):,} sentences")
    st.markdown('<a href="#top" style="font-family:\'Lora\',Georgia,serif; font-size:13px; color:#999; text-decoration:none;">↑ back to top</a>', unsafe_allow_html=True)
    st.markdown("---")

    if spacy_status is None:
        st.markdown("🟢 **spaCy active**")
        st.caption("Ranking uses real dependency parsing.")
    elif spacy_status == "not_installed":
        st.markdown("⚪ **spaCy not installed**")
        st.caption("Install for better ranking:\n```\npip install spacy\npython -m spacy download en_core_web_sm\n```")
    elif spacy_status == "model_missing":
        st.markdown("🟡 **spaCy installed, model missing**")
        st.caption("```\npython -m spacy download en_core_web_sm\n```")

    st.markdown("---")
    uploaded = st.file_uploader("Use a different .conllu file", type=["conllu", "txt"])
    if uploaded:
        @st.cache_data(show_spinner="Parsing…")
        def parse_upload(raw: bytes):
            return parse_conllu(raw.decode("utf-8").splitlines()), None
        sentences, _ = parse_upload(uploaded.read())
        st.success(f"{len(sentences):,} sentences loaded")

    st.markdown("---")
    st.markdown("**Data source & attribution**")
    st.markdown(
        "Treebank data sourced from the "
        "[Universal Dependencies English EWT corpus]"
        "(https://github.com/UniversalDependencies/UD_English-EWT), "
        "fetched directly at runtime from the official repository."
    )
    st.markdown(
        "**Corpus:** English Web Treebank (EWT)  \n"
        "**Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)  \n"
        "**Source:** Universal Dependencies  \n"
        "**Repository:** [UniversalDependencies/UD_English-EWT]"
        "(https://github.com/UniversalDependencies/UD_English-EWT)"
    )
    st.markdown(
        "**Original treebank reference:**  \n"
        "Silveira et al. (2014). *A Gold Standard Dependency Corpus for English.* "
        "LREC 2014."
    )
    st.caption(
        "This app does not redistribute the treebank data. "
        "Data is fetched at runtime from the official Universal Dependencies "
        "GitHub repository and used in accordance with the CC BY-SA 4.0 licence."
    )
    st.markdown("---")
    st.markdown("**Credits**")
    st.caption(
        "Developed with AI assistance from "
        "[Claude](https://claude.ai) (Anthropic).  \n"
        "Powered by [Streamlit](https://streamlit.io) · "
        "Dependency ranking via [spaCy](https://spacy.io)."
    )


# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown('<a name="top"></a>', unsafe_allow_html=True)
# When navigating pages, scroll to top
if "t" in st.query_params:
    st.markdown(
        '<script>window.parent.document.querySelector(".main") && '
        'window.parent.document.querySelector(".main").scrollTo(0,0);</script>',
        unsafe_allow_html=True
    )
st.title("Treebank Lookup")
st.caption("Tip — apostrophes are split into separate tokens in the treebank: type  that 's  not  that's")
st.markdown(
    '<p style="font-family:\'Lora\',Georgia,serif; font-size:12px; color:#aaa; margin-top:-8px;">'
    'Data: <a href="https://github.com/UniversalDependencies/UD_English-EWT" '
    'style="color:#aaa;">Universal Dependencies English EWT</a> · '
    'Silveira et al. (2014) · '
    '<a href="https://creativecommons.org/licenses/by-sa/4.0/" style="color:#aaa;">CC BY-SA 4.0</a>'
    '</p>',
    unsafe_allow_html=True
)

# Initialise session state keys for inputs
if "word_input" not in st.session_state:
    st.session_state["word_input"] = ""
if "query_input" not in st.session_state:
    st.session_state["query_input"] = ""

def clear_inputs():
    st.session_state["word_input"]  = ""
    st.session_state["query_input"] = ""

col1, col2, col3 = st.columns([1, 2, 0.15])
with col1:
    word = st.text_input("Word or phrase", key="word_input", placeholder="")
with col2:
    query = st.text_input("Your sentence — optional, used to rank results", key="query_input", placeholder="")
with col3:
    st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
    st.button("✕", on_click=clear_inputs, help="Clear both fields")
    st.markdown("</div>", unsafe_allow_html=True)

word_given  = bool(word.strip())
query_given = bool(query.strip())

if not word_given:
    st.stop()

# ── Word/phrase search ────────────────────────────────────────────────────────
hits = find_hits(word)
if not hits:
    hint = ""
    if "'" in word or "'" in word:
        hint = " — remember apostrophes are 2 tokens, try e.g.  that 's  instead of  that's"
    st.warning(f"No results for **{word}**{hint}.")
    st.stop()

hits = rank_hits(hits, query, word)
hits = deduplicate(hits)

phrase_mode = is_phrase(word)

def get_first_tok(sent, ids):
    return next(t for t in sent["tokens"] if t["id"] == ids[0])

# Filters + per page (single word only)
if not phrase_mode:
    all_upos = Counter(get_first_tok(s, ids)["upos"]   for s, ids in hits)
    all_dep  = Counter(get_first_tok(s, ids)["deprel"] for s, ids in hits)
    fc1, fc2, fc3 = st.columns([1, 1, 1])
    with fc1:
        upos_opts = ["All"] + [f"{u}  ({c})" for u, c in all_upos.most_common()]
        upos_sel  = st.selectbox("Filter UPOS", upos_opts)
        upos_f    = upos_sel.split("  (")[0] if upos_sel != "All" else None
    with fc2:
        dep_opts = ["All"] + [f"{d}  ({c})" for d, c in all_dep.most_common()]
        dep_sel  = st.selectbox("Filter DEPREL", dep_opts)
        dep_f    = dep_sel.split("  (")[0] if dep_sel != "All" else None
    with fc3:
        PAGE_SIZE = st.slider("Per page", 5, 100, 25)
    if upos_f:
        hits = [(s, ids) for s, ids in hits if get_first_tok(s, ids)["upos"] == upos_f]
    if dep_f:
        hits = [(s, ids) for s, ids in hits if get_first_tok(s, ids)["deprel"] == dep_f]
else:
    PAGE_SIZE = 25

# Reset page when search changes
search_key = f"{word}|{query}"
if st.session_state.get("_search_key") != search_key:
    st.session_state["_search_key"] = search_key
    st.session_state["_page"] = 0
if "_page" not in st.session_state:
    st.session_state["_page"] = 0

total      = len(hits)
total_pages = max(1, -(-total // PAGE_SIZE))  # ceiling division
page        = min(st.session_state["_page"], total_pages - 1)
st.session_state["_page"] = page

start = page * PAGE_SIZE
end   = min(start + PAGE_SIZE, total)

st.markdown("---")
ranked_note = (
    "ranked by dependency match" if (query_given and spacy_status is None)
    else "ranked by sentence structure" if query_given
    else "paste a sentence to rank by structural similarity"
)
st.caption(f"{total} match{'es' if total != 1 else ''} for \"{word}\" · {ranked_note}")

# Tag summary (single word only)
if not phrase_mode:
    tag_key = "show_tag_dist"
    if tag_key not in st.session_state:
        st.session_state[tag_key] = False
    if st.button("show tag distribution", key="btn_tag_dist"):
        st.session_state[tag_key] = not st.session_state[tag_key]
    if st.session_state[tag_key]:
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.markdown("**UPOS**")
            for u, c in Counter(get_first_tok(s, ids)["upos"] for s, ids in hits).most_common():
                st.markdown(f'<span class="badge b-upos">{u}</span> {c}×', unsafe_allow_html=True)
        with ec2:
            st.markdown("**DEPREL**")
            for d, c in Counter(get_first_tok(s, ids)["deprel"] for s, ids in hits).most_common():
                st.markdown(f'<span class="badge b-dep">{d}</span> {c}×', unsafe_allow_html=True)
        with ec3:
            st.markdown("**Features**")
            feats_c = Counter(
                get_first_tok(s, ids)["feats"]
                for s, ids in hits
                if get_first_tok(s, ids)["feats"] != "_"
            )
            for feat, c in feats_c.most_common(12):
                st.markdown(f'<span class="badge b-feats">{feat}</span> {c}×', unsafe_allow_html=True)

# Results — current page only
for i, (sent, matched_ids) in enumerate(hits[start:end]):
    global_i = start + i
    highlight_set = set(matched_ids)
    sent_html = highlight_sentence(sent["tokens"], highlight_set)
    key_info  = (info_line_phrase(matched_ids, sent["tokens"]) if phrase_mode
                 else info_line_single(get_first_tok(sent, matched_ids), sent["tokens"]))

    st.markdown(f"""
    <div class="card">
      <div class="sent">{sent_html}</div>
      {key_info}
    </div>""", unsafe_allow_html=True)

    tok_key = f"tok_{global_i}"
    if tok_key not in st.session_state:
        st.session_state[tok_key] = False
    if st.button("show tokens", key=f"btn_{global_i}"):
        st.session_state[tok_key] = not st.session_state[tok_key]
    if st.session_state[tok_key]:
        st.markdown(token_detail_table(sent["tokens"], highlight_set), unsafe_allow_html=True)

# Pagination + back to top in one row
if hits:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    pc1, pc2, pc3, pc4 = st.columns([1, 3, 1, 1])
    with pc1:
        if page > 0:
            if st.button("← previous"):
                st.session_state["_page"] = page - 1
                st.query_params["t"] = str(page - 1)
                st.rerun()
    with pc2:
        if total_pages > 1:
            st.markdown(
                f'<div style="text-align:center; font-family:\'Lora\',Georgia,serif; '
                f'font-size:13px; color:#999; padding-top:6px;">'
                f'page {page + 1} of {total_pages}</div>',
                unsafe_allow_html=True
            )
    with pc3:
        st.markdown(
            '<div style="padding-top:6px; text-align:center;">'
            '<a href="#top" style="font-family:\'Lora\',Georgia,serif; font-size:13px; '
            'color:#999; text-decoration:none;">↑ top</a></div>',
            unsafe_allow_html=True
        )
    with pc4:
        if page < total_pages - 1:
            if st.button("next →", key="next_btn"):
                st.session_state["_page"] = page + 1
                st.query_params["t"] = str(page + 1)
                st.rerun()
