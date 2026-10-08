#!/usr/bin/env python3
"""Gera o site de um chalé/pousada a partir de um chale.json + pasta de fotos.

Uso:
  python3 build.py <chale.json> <pasta-de-fotos> <pasta-de-saida> [--inline]

  --inline  embute as fotos no HTML (base64), gerando um único index.html
            (para publicar como Artifact). Sem a flag, cria saida/index.html + saida/img/.

O template é template/index.template.html (o mesmo layout do demo-mipamaya-chale).
Campos do JSON: ver chale.exemplo.json e README.md.
"""
import base64, html, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
PALETA_PADRAO = dict(ink="#0e1c17", ink2="#162b24", moss="#2c4a3d", cream="#f6eedd",
                     sand="#e8d8b9", amber="#e3a65a", ember="#c9633a")
ICONES_VALIDOS = ["bath", "flame", "snow", "wifi", "utensils", "bed", "coffee", "car",
                  "paw", "mountain", "shield", "home", "wine", "key", "laptop"]


def esc(s):
    return html.escape(str(s), quote=False)


def em(s):
    """Texto com *destaque* -> <em>destaque</em>."""
    return re.sub(r"\*(.+?)\*", lambda m: f"<em>{m.group(1)}</em>", esc(s))


def js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def die(msg):
    sys.exit(f"ERRO: {msg}")


# ---------------------------------------------------------------- fotos
class Fotos:
    def __init__(self, pasta, saida, inline):
        self.pasta, self.saida, self.inline = Path(pasta), Path(saida), inline
        self.usadas = {}
        self.faltando = []

    def achar(self, nome):
        stem = Path(nome).stem
        for p in sorted(self.pasta.iterdir()):
            if p.stem == stem and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic"):
                return p
        return None

    def ref(self, nome):
        """Registra a foto e devolve o caminho/URL a usar no HTML."""
        if not nome:
            return ""
        stem = Path(nome).stem
        if stem not in self.usadas:
            src = self.achar(nome)
            if not src:
                self.faltando.append(nome)
                return f"img/{stem}.jpg"
            self.usadas[stem] = self.processar(src, stem)
        dest = self.usadas[stem]
        if self.inline:
            return "data:image/jpeg;base64," + base64.b64encode(dest.read_bytes()).decode()
        return f"img/{stem}.jpg"

    def processar(self, src, stem):
        pasta_img = self.saida / ("_tmp_img" if self.inline else "img")
        pasta_img.mkdir(parents=True, exist_ok=True)
        dest = pasta_img / f"{stem}.jpg"
        lado, qual = (900, 60) if self.inline else (1600, 72)
        pequeno = src.suffix.lower() in (".jpg", ".jpeg") and src.stat().st_size <= (400_000 if not self.inline else 90_000)
        if pequeno:
            shutil.copy(src, dest)
        else:
            try:
                subprocess.run(["sips", "-Z", str(lado), "-s", "format", "jpeg",
                                "-s", "formatOptions", str(qual), str(src), "--out", str(dest)],
                               check=True, capture_output=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                shutil.copy(src, dest)  # sem sips: copia como está
        return dest


# ---------------------------------------------------------------- blocos de HTML
def bloco_hero_h1(titulo):
    t = re.sub(r"\*(.+?)\*", lambda m: "*" + m.group(1).replace(" ", " ") + "*", titulo)
    palavras = [em(w).replace(" ", "&nbsp;") for w in t.split(" ")]
    return " ".join(f'<span class="w"><span>{w}</span></span>' for w in palavras)


def sec_historia(d, F):
    if not d:
        return ""
    selo = d.get("selo")
    selo_html = f'\n      <div class="badge"><i><b>{esc(selo["valor"])}</b>{esc(selo["rotulo"]).replace(chr(10), "<br>")}</i></div>' if selo else ""
    ass = f'\n      <div class="sign">{esc(d["assinatura"])}</div>' if d.get("assinatura") else ""
    ps = "\n      ".join(f"<p>{esc(p)}</p>" for p in d["paragrafos"])
    return f'''<!-- HISTÓRIA -->
<section id="historia" class="pad light">
  <div class="wrap story">
    <div class="story-imgs rv">
      <img class="a" src="{F.ref(d["foto_a"])}" alt="{esc(d.get("alt_a", ""))}" data-par="0.05" loading="lazy">
      <img class="b" src="{F.ref(d["foto_b"])}" alt="{esc(d.get("alt_b", ""))}" loading="lazy">{selo_html}
    </div>
    <div class="rv d1">
      <div class="eyebrow">{esc(d.get("eyebrow", "Nossa história"))}</div>
      <h2>{em(d["titulo"])}</h2>
      {ps}{ass}
    </div>
  </div>
</section>'''


def sec_stats(itens):
    if not itens:
        return ""
    cels = []
    for i, n in enumerate(itens):
        attrs = f'data-count="{n["valor"]}"'
        if n.get("dec"):
            attrs += f' data-dec="{n["dec"]}"'
        if n.get("prefixo"):
            attrs += f' data-pre="{esc(n["prefixo"])}"'
        if n.get("sep"):
            attrs += ' data-sep="1"'
        d = f" d{min(i, 3)}" if i else ""
        cels.append(f'    <div class="stat rv{d}"><b {attrs}>0</b><span>{esc(n["rotulo"])}</span></div>')
    cols = len(itens)
    estilo = f' style="--cols:{cols}"'
    return f'''<!-- NÚMEROS -->
<section class="stats">
  <div class="wrap"{estilo}>
''' + "\n".join(cels) + "\n  </div>\n</section>"


def sec_chale(d, F):
    if not d:
        return ""
    stage = "\n".join(f'        <img{" class=\"on\"" if i == 0 else ""} src="{F.ref(it["foto"])}" alt="{esc(it.get("alt", it["titulo"]))}">'
                      for i, it in enumerate(d["itens"]))
    steps = []
    for i, it in enumerate(d["itens"]):
        tags = "".join(f"<li>{esc(t)}</li>" for t in it.get("tags", []))
        steps.append(f'''        <div class="step" data-i="{i}">
          <img class="m-img" src="{F.ref(it["foto"])}" alt="" loading="lazy">
          <span class="n">{i + 1:02d} — {esc(it["rotulo"])}</span><h3>{esc(it["titulo"])}</h3>
          <p>{esc(it["texto"])}</p>
          <ul>{tags}</ul>
        </div>''')
    return f'''<!-- O CHALÉ -->
<section id="chale" class="pad">
  <div class="wrap">
    <div class="eyebrow">{esc(d.get("eyebrow", "O chalé"))}</div>
    <h2>{em(d["titulo"])}</h2>
    <p class="lead">{esc(d["lead"])}</p>
    <div class="sticky-wrap">
      <div class="stage" id="stage">
{stage}
      </div>
      <div>
''' + "\n".join(steps) + '''
      </div>
    </div>
  </div>
</section>'''


def sec_exp(d, F):
    if not d:
        return ""
    cards = []
    for i, it in enumerate(d["itens"]):
        dl = f" d{min(i, 3)}" if i else ""
        cards.append(f'      <article class="exp rv{dl}" tabindex="0"><img src="{F.ref(it["foto"])}" alt="{esc(it.get("alt", it["titulo"]))}" loading="lazy"><div><h3>{esc(it["titulo"])}</h3><p>{esc(it["texto"])}</p></div></article>')
    nota = f'\n    <p class="note">{esc(d["nota"])}</p>' if d.get("nota") else ""
    return f'''<!-- EXPERIÊNCIAS -->
<section id="experiencias" class="pad light">
  <div class="wrap">
    <div class="eyebrow">{esc(d.get("eyebrow", "Experiências"))}</div>
    <h2>{em(d["titulo"])}</h2>
    <p class="lead">{esc(d["lead"])}</p>
    <div class="exp-grid">
''' + "\n".join(cards) + f'''
    </div>{nota}
  </div>
</section>'''


def sec_aval(d):
    if not d:
        return ""
    topo = ""
    if d.get("nota"):
        topo = f'''      <div class="score rv"><b>{esc(d["nota"])}</b><div><div class="stars">★★★★★</div><small style="color:var(--muted)">{esc(d["resumo"])}</small></div></div>'''
    barras = ""
    if d.get("barras"):
        linhas = "\n".join(f'        <div class="bar">{esc(l)}<i style="--w:{w}%"></i><b>{esc(v)}</b></div>' for l, w, v in d["barras"])
        barras = f'\n      <div class="bars" id="bars">\n{linhas}\n      </div>'
    if av_dep(d):
        direita = '<div class="quote-box" id="qbox"></div>\n      <div class="dots" id="qdots"></div>'
    else:
        itens = "".join(f"<li>{esc(n)}<b>{q}</b></li>" for n, q in d.get("destaques", []))
        direita = f'<div class="quote-box hl"><h3>O que os hóspedes mais destacam</h3><ul>{itens}</ul></div>' if itens else ""
    return f'''<!-- AVALIAÇÕES -->
<section id="avaliacoes" class="pad">
  <div class="wrap rev-top">
    <div>
      <div class="eyebrow">Avaliações</div>
{topo}{barras}
    </div>
    <div class="rv d1">
      {direita}
      <p class="src">{esc(d["fonte_texto"])}</p>
    </div>
  </div>
</section>'''


def av_dep(d):
    return bool(d.get("depoimentos"))


def sec_local(d, c):
    dts = [f'        <div><dt>Endereço</dt><dd>{esc(c["endereco"]).replace(chr(10), "<br>")}</dd></div>']
    if d.get("gps"):
        dts.append(f'        <div><dt>No GPS</dt><dd>{esc(d["gps"])}</dd></div>')
    if d.get("estacionamento"):
        dts.append(f'        <div><dt>Estacionamento</dt><dd>{esc(d["estacionamento"])}</dd></div>')
    q = c.get("maps_query") or f'{c["nome"]} {c["cidade"]} {c["uf"]}'
    from urllib.parse import quote
    return f'''<!-- COMO CHEGAR -->
<section id="como-chegar" class="pad">
  <div class="wrap loc">
    <div class="rv">
      <div class="eyebrow">Como chegar</div>
      <h2>{em(d["titulo"])}</h2>
      <p class="lead">{esc(d["lead"])}</p>
      <dl>
''' + "\n".join(dts) + f'''
      </dl>
    </div>
    <div class="map rv d1"><iframe loading="lazy" title="Mapa" src="https://maps.google.com/maps?q={quote(q)}&output=embed"></iframe></div>
  </div>
</section>'''


# ---------------------------------------------------------------- principal
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    inline = "--inline" in sys.argv
    if len(args) != 3:
        sys.exit(__doc__)
    json_path, fotos_dir, saida = args
    c = json.load(open(json_path, encoding="utf-8"))
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    F = Fotos(fotos_dir, saida, inline)

    for k in ("slug", "nome", "cidade", "uf", "endereco", "meta_desc", "hero", "galeria", "comodidades", "local", "final"):
        if k not in c:
            die(f"campo obrigatório ausente no JSON: {k}")
    for ic, *_ in c["comodidades"]:
        if ic not in ICONES_VALIDOS:
            die(f"ícone inválido '{ic}'. Válidos: {', '.join(ICONES_VALIDOS)}")

    tema = {**PALETA_PADRAO, **c.get("tema", {})}
    paleta = " ".join(f"--{k}:{v};" for k, v in tema.items())
    paleta += " --text:#e9e4d6; --muted:#9db0a4; --dark-text:#1d2b25; --line:rgba(255,255,255,.14);"
    h = c["hero"]
    res = c.get("reservas", {})

    menu = []
    if c.get("historia"): menu.append(("historia", "Nossa história"))
    if c.get("comodos"): menu.append(("chale", "O chalé"))
    if c.get("experiencias"): menu.append(("experiencias", "Experiências"))
    menu.append(("galeria", "Galeria"))
    if c.get("avaliacoes"): menu.append(("avaliacoes", "Avaliações"))
    menu.append(("como-chegar", "Como chegar"))
    menu_html = "\n".join(f'      <a href="#{i}">{t}</a>' for i, t in menu) + '\n      <a href="#reservas" class="btn btn-amber">Reservar</a>'

    barra = "\n".join(f"      <div><b>{esc(b)}</b><small>{esc(s)}</small></div>" for b, s in h["barra"])
    pet = ""
    if res.get("aceita_pet", True):
        pet = '        <label class="chk"><input type="checkbox" id="pet"> Vou levar meu pet <small style="color:#7c8a80">(aceitamos)</small></label>'
    else:
        pet = '        <div style="display:none"><input type="checkbox" id="pet"></div>'

    links = []
    if c.get("instagram"):
        links.append(f'      <a href="https://instagram.com/{esc(c["instagram"])}" target="_blank" rel="noopener">@{esc(c["instagram"])}</a>')
    for nome_l, url in c.get("links", []):
        links.append(f'      <a href="{esc(url)}" target="_blank" rel="noopener">{esc(nome_l)}</a>')

    av = c.get("avaliacoes")
    rev = [[n, d, t] for n, d, t in av.get("depoimentos", [])] if av else []

    for f, _ in c["galeria"]:
        F.ref(f)

    subs = {
        "TITLE": esc(f'{c["nome"]} — {c["cidade"]}, {c["uf"]}'),
        "META_DESC": html.escape(c["meta_desc"], quote=True),
        "PALETTE": paleta,
        "HERO_CLASS": " side" if h.get("overlay_lateral") else "",
        "HERO_IMG": F.ref(h["foto"]),
        "FINAL_IMG": F.ref(c["final"]["foto"]),
        "LOGO_NAME": esc(c.get("nome_curto", c["nome"])),
        "MENU": menu_html,
        "HERO_EYEBROW": esc(h.get("eyebrow", f'{c["cidade"]} · {c["uf"]}')),
        "HERO_H1": bloco_hero_h1(h["titulo"]),
        "HERO_SUB": esc(h["sub"]),
        "HERO_BAR": barra,
        "SEC_HISTORIA": sec_historia(c.get("historia"), F),
        "SEC_STATS": sec_stats(c.get("numeros")),
        "SEC_CHALE": sec_chale(c.get("comodos"), F),
        "SEC_EXP": sec_exp(c.get("experiencias"), F),
        "SEC_AVAL": sec_aval(av),
        "BOOK_LEAD": esc(res.get("lead", "Veja a disponibilidade, selecione o período e envie o pedido direto para os anfitriões pelo WhatsApp. Sem comissão de plataforma.")),
        "PET_CHECK": pet,
        "OBS_PH": html.escape(res.get("obs_placeholder", "Aniversário, lua de mel, pedido especial…"), quote=True),
        "SEC_LOCAL": sec_local(c["local"], c),
        "FINAL_H2": em(c["final"]["titulo"]),
        "NOME": esc(c["nome"]),
        "FOOT_ADDR": esc(c.get("endereco_curto", c["endereco"].replace("\n", " · "))),
        "FOOT_LINKS": "\n".join(links),
        "CFG": js({"nome": c["nome"], "whatsapp": c.get("whatsapp", ""), "maxHospedes": res.get("max_hospedes", 4),
                   "storeKey": f'{c["slug"]}_demo_v1'}),
        "MQ": js(c.get("faixa", [])),
        "AM": js(c["comodidades"]),
        "IMGS": js({stem: "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode() for stem, p in F.usadas.items() if stem in {Path(f).stem for f, _ in c["galeria"]}}) if inline else "new Proxy({},{get:(_,k)=>`img/${k}.jpg`})",
        "GAL": js([[Path(f).stem, cap] for f, cap in c["galeria"]]),
        "REV": js(rev),
    }

    tpl = (HERE / "template" / "index.template.html").read_text(encoding="utf-8")
    for k, v in subs.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    sobra = re.findall(r"\{\{[A-Z_]+\}\}", tpl)
    if sobra:
        die(f"placeholders sem valor: {sobra}")
    if F.faltando:
        die("fotos não encontradas em " + str(fotos_dir) + ": " + ", ".join(sorted(set(F.faltando))))

    if inline:
        shutil.rmtree(saida / "_tmp_img", ignore_errors=True)
    (saida / "index.html").write_text(tpl, encoding="utf-8")
    tam = (saida / "index.html").stat().st_size / 1024
    print(f"OK: {saida/'index.html'} ({tam:.0f} KB, {len(F.usadas)} fotos{', inline' if inline else ''})")


if __name__ == "__main__":
    main()
