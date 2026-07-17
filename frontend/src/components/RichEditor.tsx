interface Props {
  value: string;
  onChange: (v: string) => void;
}

// Convierte markdown estilo Telegram (**b**, _i_, [link](url)) a HTML para la vista previa.
// El texto guardado se mantiene en markdown; Telegram lo interpreta igual con parse_mode='md'.
function renderPreviewHtml(text: string): string {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  html = html.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  html = html.replace(/_(.+?)_/g, '<i>$1</i>');
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" style="color: var(--accent)">$1</a>');
  html = html.replace(/`(.+?)`/g, '<code>$1</code>');
  return html.replace(/\n/g, '<br/>');
}

export default function RichEditor({ value, onChange }: Props) {
  const insert = (before: string, after = '') => {
    onChange(value + before + (after ? '' : '') + after);
  };

  return (
    <div>
      <div className="toolbar">
        <button onClick={() => insert('**negrita**')}>B</button>
        <button onClick={() => insert('_cursiva_')}>I</button>
        <button onClick={() => insert('[texto](https://...)')}>Link</button>
        <button onClick={() => insert('{{comunidad}}')}>+ Comunidad</button>
        <button onClick={() => insert('{{fecha}}')}>+ Fecha</button>
      </div>
      <textarea
        className="input"
        rows={6}
        placeholder="Escribe tu publicación... usa **negrita**, _cursiva_ y variables como {{comunidad}}"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <div style={{ marginTop: 10 }}>
        <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6 }}>VISTA PREVIA</div>
        <div className="tg-bubble" dangerouslySetInnerHTML={{ __html: renderPreviewHtml(value || 'Tu mensaje aparecerá aquí...') }} />
        <span className="meta" style={{ display: 'block', textAlign: 'right', color: 'var(--muted)', fontSize: 10, marginTop: 4 }}>
          12:34 ✓✓
        </span>
      </div>
    </div>
  );
}
