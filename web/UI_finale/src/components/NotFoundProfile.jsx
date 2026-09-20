import '../styles/shell.css';

export default function NotFoundProfile({ message }) {
  return (
    <main className="main">
      <div
        style={{
          borderRadius: 18,
          background: 'var(--card)',
          boxShadow: '0 2px 12px rgba(20, 15, 40, 0.06)',
          padding: 20,
          marginTop: 32,
          maxWidth: 480,
        }}
      >
        <p style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 800 }}>Profil introuvable</p>
        <p style={{ margin: 0, fontSize: 12, color: 'var(--muted)' }}>{message}</p>
      </div>
    </main>
  );
}
