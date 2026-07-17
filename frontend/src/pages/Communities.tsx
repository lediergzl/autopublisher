import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Communities() {
  const [communities, setCommunities] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [connected, setConnected] = useState<boolean | null>(null);
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [needsPassword, setNeedsPassword] = useState(false);
  const [loginState, setLoginState] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = () => api.listCommunities(q).then(setCommunities).catch((e) => setError(e.message));

  useEffect(() => {
    api.telegramStatus().then((s) => setConnected(s.conectado));
    load();
  }, []);

  const startLogin = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await api.loginStart(phone);
      setLoginState(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const completeLogin = async () => {
    setBusy(true);
    setError('');
    try {
      await api.loginComplete({ ...loginState, phone, code, password: password || undefined });
      setConnected(true);
    } catch (e: any) {
      if (e.detail === 'requires_password') {
        setNeedsPassword(true);
        setError('Tu cuenta tiene verificación en dos pasos. Ingresa tu contraseña de Telegram.');
      } else {
        setError(e.message);
      }
    } finally {
      setBusy(false);
    }
  };

  const sync = async () => {
    setBusy(true);
    try {
      const res = await api.syncCommunities();
      setCommunities(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (connected === false) {
    return (
      <>
        <header className="topbar">
          <div className="eyebrow">Paso 1</div>
          <h1>Conecta tu Telegram</h1>
        </header>
        <div className="content">
          {error && <div className="card" style={{ color: 'var(--danger)' }}>{error}</div>}
          <div className="card">
            <p style={{ marginTop: 0, color: 'var(--muted)', fontSize: 13 }}>
              Usa tu propio número. Solo verás y gestionarás las comunidades a las que ya perteneces.
            </p>
            {!loginState ? (
              <>
                <input className="input" placeholder="+34 600 000 000" value={phone} onChange={(e) => setPhone(e.target.value)} />
                <button className="btn" style={{ marginTop: 10 }} onClick={startLogin} disabled={busy || !phone}>
                  Enviar código
                </button>
              </>
            ) : (
              <>
                <input className="input" placeholder="Código recibido en Telegram" value={code} onChange={(e) => setCode(e.target.value)} />
                {needsPassword && (
                  <input
                    className="input"
                    type="password"
                    placeholder="Contraseña de verificación en dos pasos"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{ marginTop: 10 }}
                  />
                )}
                <button
                  className="btn"
                  style={{ marginTop: 10 }}
                  onClick={completeLogin}
                  disabled={busy || !code || (needsPassword && !password)}
                >
                  Confirmar
                </button>
              </>
            )}
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <header className="topbar">
        <div className="eyebrow">Tus grupos y canales</div>
        <h1>Comunidades</h1>
      </header>
      <div className="content">
        {error && <div className="card" style={{ color: 'var(--danger)' }}>{error}</div>}
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <input className="input" placeholder="Buscar..." value={q} onChange={(e) => setQ(e.target.value)} onBlur={load} />
          <button className="btn secondary" onClick={sync} disabled={busy}>Sincronizar</button>
        </div>
        <div className="card">
          {communities.length === 0 && (
            <span style={{ color: 'var(--muted)', fontSize: 13 }}>
              Pulsa "Sincronizar" para traer tus grupos y canales actuales.
            </span>
          )}
          {communities.map((c) => (
            <div className="list-row" key={c.id}>
              <span>{c.nombre || c.telegram_chat_id}</span>
              <button
                className="pill"
                style={{ border: 'none', cursor: 'pointer' }}
                onClick={() => api.updateCommunity(c.id, { estado: !c.estado }).then(load)}
              >
                {c.estado ? 'Activa' : 'Inactiva'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
