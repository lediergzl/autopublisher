import { Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Communities from './pages/Communities';
import ContentEditor from './pages/ContentEditor';
import Campaigns from './pages/Campaigns';

export default function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/communities" element={<Communities />} />
        <Route path="/content" element={<ContentEditor />} />
        <Route path="/campaigns" element={<Campaigns />} />
      </Routes>

      <nav className="tabbar">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>Inicio</NavLink>
        <NavLink to="/communities" className={({ isActive }) => (isActive ? 'active' : '')}>Comunidades</NavLink>
        <NavLink to="/content" className={({ isActive }) => (isActive ? 'active' : '')}>Contenido</NavLink>
        <NavLink to="/campaigns" className={({ isActive }) => (isActive ? 'active' : '')}>Campañas</NavLink>
      </nav>
    </div>
  );
}
