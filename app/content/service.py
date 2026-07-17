import re


def render_post(contenido: str, variables: dict[str, str]) -> str:
    """
    Reemplaza variables tipo {{comunidad}}, {{fecha}} en el contenido.
    El formato markdown (**negrita**, _cursiva_, [link](url)) se mantiene
    intacto porque Telegram lo interpreta de forma nativa vía parse_mode.
    """
    def replace(match):
        key = match.group(1).strip()
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", replace, contenido)
