import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [posts, setPosts] = useState<any[]>([]);
  const [communities, setCommunities] = useState<any[]>([]);
  const [nombre, setNombre] = useState('');
  const [contenidoId, setContenidoId] = useState<number | ''>('');
  const [selected, setSelected] = useState<number[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [publishingKey, setPublishingKey] = useState<string | null>(null);

  const load = () => api.listCampaigns().then(setCampaigns).catch((e) => setError(e.message));

  useEffect(() => {
    load();
    api.listPosts().then(setPosts).catch(() => {});
    api.listCommunities().then(setCommunities).catch(() => {});
  }, []);

  const toggleSelected = (id: number) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const createCampaign = async () => {
    if (!nombre || !contenidoId || selected.length === 0) return;
    setBusy(true);
    setError('');
    try {
      await api.createCampaign({ nombre, contenido_id: contenidoId, community_ids: selected });
      setNombre('');
      setContenidoId('');
      setSelected([]);
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const publishOne = async (campaignId: number, communityId: number) => {
    const key = `${campaignId}-${communityId}`;
    setPublishingKey(key);
    setError('');
    try {
      await api.executeOne(campaignId, communityId);
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setPublishingKey(null);
    }
  };

  const communityName = (id: number) => communities.find((c) => c.id === id)?.nombre || `Comunidad #${id}`;

  return (
    <>
      <header className="topbar">
        <div className="eyebrow">Planificación</div>
        <h1>Campañas</h1>
      </header>
      <div className="content">
        {error && <div className="card" style={{ color: 'var(--danger)' }}>{error}</div>}

        <div className="card">
          <strong>Nueva campaña</strong>
          <input
            className="input"
            placeholder="Nombre de la campaña"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            style={{ margin: '10px 0' }}
          />
          <select className="input" value={contenidoId} onChange={(e) => setContenidoId(Number(e.target.value))} style={{ marginBottom: 10 }}>
            <option value="">Elegir publicación...</option>
            {posts.map((p) => (
              <option key={p.id} value={p.id}>{p.titulo}</option>
            ))}
          </select>

          <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 6 }}>Comunidades destino</div>
          <div style={{ maxHeight: 160, overflowY: 'auto', marginBottom: 10 }}>
            {communities.map((c) => (
              <label key={c.id} className="list-row" style={{ cursor: 'pointer' }}>
                <span>{c.nombre || c.telegram_chat_id}</span>
                <input type="checkbox" checked={selected.includes(c.id)} onChange={() => toggleSelected(c.id)} />
              </label>
            ))}
          </div>

          <button className="btn" onClick={createCampaign} disabled={busy || !nombre || !contenidoId || selected.length === 0}>
            Crear campaña
          </button>
        </div>

        {campaigns.map((camp) => (
          <div className="card" key={camp.id}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>{camp.nombre}</strong>
              <span className="pill">{camp.estado}</span>
            </div>
            <div style={{ marginTop: 8 }}>
              {camp.comunidades.map((cc: any) => (
                <div className="list-row" key={cc.id}>
                  <span style={{ fontSize: 13 }}>{communityName(cc.community_id)}</span>
                  {cc.publicado === 'publicado' ? (
                    <span className="pill">Publicado</span>
                  ) : cc.publicado === 'error' ? (
                    <span className="pill" style={{ background: 'rgba(226,96,79,0.15)', color: 'var(--danger)' }}>Error</span>
                  ) : (
                    <button
                      className="btn secondary"
                      style={{ padding: '4px 10px', fontSize: 12 }}
                      onClick={() => publishOne(camp.id, cc.community_id)}
                      disabled={publishingKey === `${camp.id}-${cc.community_id}`}
                    >
                      {publishingKey === `${camp.id}-${cc.community_id}` ? 'Publicando...' : 'Publicar aquí'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
