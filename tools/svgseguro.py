"""Conferência de segurança dos SVG de terceiros antes de publicar.

Os SVG vêm do Wikimedia Commons e são servidos no mesmo domínio do site, então
nenhum pode carregar conteúdo ativo. A conferência usa um parser XML de verdade
(entidades e codificações já resolvidas), não busca de texto, e é fechada por
padrão: o que não for analisável é recusado.

Não dá para mandar cabeçalho CSP pelo GitHub Pages; esta conferência é a barreira.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

PROIBIDOS = {
    "script", "foreignobject", "iframe", "object", "embed", "audio", "video",
    "handler", "listener", "frame", "frameset", "applet", "meta", "link", "base",
}
ANIMACAO = {"animate", "set", "animatetransform", "animatemotion", "animatecolor"}
ATRIB_URL = {"href", "src", "action", "formaction", "data", "from", "to", "values", "by"}
ESQUEMA = re.compile(r"^\s*([a-z][a-z0-9+.\-]*)\s*:", re.I)
CSS_RUIM = re.compile(r"javascript\s*:|vbscript\s*:|expression\s*\(|@import|-moz-binding|behavior\s*:",
                      re.I)


def _local(nome: str) -> str:
    return nome.rsplit("}", 1)[-1].lower()


def _sem_controle(v: str) -> str:
    # navegadores ignoram espaços e caracteres de controle dentro do esquema
    return re.sub(r"[\x00-\x20\x7f]+", "", v)


def problema(dados: bytes) -> str | None:
    """Devolve o motivo da recusa, ou None se o SVG pode ser publicado."""
    # Sem declaração de entidades: evita XXE e expansão em cadeia ("billion
    # laughs") no parser da biblioteca padrão, e diferenças entre parsers.
    if re.search(rb"<!ENTITY", dados, re.I):
        return "declara entidades XML (<!ENTITY>)"
    try:
        raiz = ET.fromstring(dados)
    except Exception as e:  # XML inválido, entidade externa, codificação desconhecida
        return f"XML não analisável ({type(e).__name__})"
    if _local(raiz.tag) != "svg":
        return "a raiz não é <svg>"
    for el in raiz.iter():
        if not isinstance(el.tag, str):
            continue  # comentário ou instrução de processamento
        tag = _local(el.tag)
        if tag in PROIBIDOS:
            return f"elemento <{tag}>"
        if tag == "style" and CSS_RUIM.search(el.text or ""):
            return "CSS ativo em <style>"
        for nome, valor in el.attrib.items():
            a = _local(nome)
            v = _sem_controle(valor)
            if a.startswith("on"):
                return f"atributo de evento {a}"
            if a == "style" and CSS_RUIM.search(valor):
                return "CSS ativo em style"
            if tag in ANIMACAO and a == "attributename" and (
                    v.lower().endswith("href") or v.lower().startswith("on")):
                return "animação que altera href ou evento"
            if a in ATRIB_URL or tag in ANIMACAO:
                m = ESQUEMA.match(v)
                if a in ("href", "src"):
                    # só referência interna ou imagem embutida
                    if not (v.startswith("#") or v == ""
                            or re.match(r"data:image/(png|jpe?g|gif|webp);", v, re.I)):
                        return f"{a} externo ou ativo ({v[:40]})"
                elif m and m.group(1).lower() in ("javascript", "vbscript", "data"):
                    return f"{a} com esquema {m.group(1)}"
            elif "javascript:" in v.lower() or "vbscript:" in v.lower():
                return f"atributo {a} com script"
    return None
