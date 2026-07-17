import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  return (
    <>
      <header className="topbar">
        <div className="eyebrow">AutoPublisher</div>
        <h1>Tu resumen</h1>
      </header>
      <div className="content">
        {error && <div className="card" style={{ color: 'var(--danger)' }}>{error}</div>}
        <div className="stat-grid">
          <div className="stat-card">
            <div className="value">{data?.comunidades ?? '—'}</div>
            <div className="label">Comunidades</div>
          </div>
          <div className="stat-card">
            <div className="value">{data?.publicaciones ?? '—'}</div>
            <div className="label">Publicaciones</div>
          </div>
          <div className="stat-card">
            <div className="value">{data?.campanas_activas ?? '—'}</div>
            <div className="label">Campañas activas</div>
          </div>
        </div>

        <div className="card">
          <strong>Actividad reciente</strong>
          <div style={{ marginTop: 10 }}>
            {(data?.actividad_reciente || []).length === 0 && (
              <span style={{ color: 'var(--muted)', fontSize: 13 }}>
                Aún no hay publicaciones. Conecta tu cuenta y crea tu primera campaña.
              </span>
            )}
            {(data?.actividad_reciente || []).map((a: any) => (
              <div className="list-row" key={a.id}>
                <span style={{ fontSize: 13 }}>Comunidad #{a.community_id}</span>
                <span className={`pill ${a.estado === 'publicado' ? '' : 'muted'}`}>{a.estado}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
