import { useEffect, useState } from 'react';
import { api } from '../api/client';
import RichEditor from '../components/RichEditor';

export default function ContentEditor() {
  const [posts, setPosts] = useState<any[]>([]);
  const [titulo, setTitulo] = useState('');
  const [contenido, setContenido] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = () => api.listPosts().then(setPosts).catch((e) => setError(e.message));

  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!titulo || !contenido) return;
    setBusy(true);
    setError('');
    try {
      await api.createPost({ titulo, contenido, es_plantilla: true });
      setTitulo('');
      setContenido('');
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <header className="topbar">
        <div className="eyebrow">Editor</div>
        <h1>Crear contenido</h1>
      </header>
      <div className="content">
        {error && <div className="card" style={{ color: 'var(--danger)' }}>{error}</div>}
        <div className="card">
          <input
            className="input"
            placeholder="Título (uso interno, no se publica)"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            style={{ marginBottom: 10 }}
          />
          <RichEditor value={contenido} onChange={setContenido} />
          <button className="btn" style={{ marginTop: 12 }} onClick={save} disabled={busy || !titulo || !contenido}>
            Guardar publicación
          </button>
        </div>

        <div className="card">
          <strong>Tus publicaciones</strong>
          {posts.length === 0 && (
            <div style={{ color: 'var(--muted)', fontSize: 13, marginTop: 8 }}>
              Todavía no has creado ninguna.
            </div>
          )}
          {posts.map((p) => (
            <div className="list-row" key={p.id}>
              <span>{p.titulo}</span>
              <button className="pill muted" style={{ border: 'none', cursor: 'pointer' }} onClick={() => api.deletePost(p.id).then(load)}>
                Eliminar
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
