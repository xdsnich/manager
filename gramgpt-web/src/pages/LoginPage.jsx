import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Input, Button, Spinner } from '../components/ui'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    const ok = await login(email, password)
    setSubmitting(false)
    if (ok) navigate('/')
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Background glow blobs — JetBrains style */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0 }}>
        <div style={{
          position: 'absolute', top: '10%', left: '20%',
          width: 500, height: 500, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(124,77,255,0.12) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }} />
        <div style={{
          position: 'absolute', bottom: '10%', right: '15%',
          width: 400, height: 400, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(61,139,255,0.1) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }} />
        <div style={{
          position: 'absolute', top: '50%', left: '60%',
          width: 300, height: 300, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,61,154,0.08) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }} />
      </div>

      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 420, animation: 'fadeUp 0.45s cubic-bezier(0.16,1,0.3,1)' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 44 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 12, marginBottom: 14,
          }}>
            <div style={{
              width: 44, height: 44, borderRadius: 12,
              background: 'linear-gradient(135deg, #7c4dff 0%, #ff3d9a 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 20, fontWeight: 800, color: '#fff',
              boxShadow: '0 8px 30px rgba(124,77,255,0.4)',
            }}>G</div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.03em' }}>
                Gram<span style={{ background: 'linear-gradient(135deg,#7c4dff,#ff3d9a)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>GPT</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', letterSpacing: '0.04em' }}>MANAGER</div>
            </div>
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-3)' }}>Войди чтобы управлять аккаунтами</div>
        </div>

        {/* Card */}
        <div style={{
          background: 'rgba(20,20,20,0.8)',
          border: '1px solid var(--border)',
          borderRadius: 20, padding: 32,
          backdropFilter: 'blur(20px)',
          boxShadow: '0 24px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.03)',
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 24, letterSpacing: '-0.02em' }}>
            Вход в систему
          </h2>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Input label="Email" type="email" value={email}
              onChange={e => { setEmail(e.target.value); clearError?.() }}
              placeholder="you@example.com" required autoFocus />
            <Input label="Пароль" type="password" value={password}
              onChange={e => { setPassword(e.target.value); clearError?.() }}
              placeholder="••••••••" required />

            {error && (
              <div style={{
                padding: '10px 14px', background: 'var(--red-dim)',
                border: '1px solid rgba(248,81,73,0.25)',
                borderRadius: 10, fontSize: 13, color: 'var(--red)',
              }}>{error}</div>
            )}

            <button type="submit" disabled={submitting} style={{
              marginTop: 4, padding: '12px',
              background: 'linear-gradient(135deg, #7c4dff 0%, #3d8bff 100%)',
              color: '#fff', border: 'none', borderRadius: 10,
              fontSize: 14, fontWeight: 700, letterSpacing: '-0.01em',
              cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.7 : 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              boxShadow: '0 4px 24px rgba(124,77,255,0.4)',
              transition: 'transform 0.2s, box-shadow 0.2s',
            }}
            onMouseEnter={e => { if (!submitting) { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 8px 32px rgba(124,77,255,0.5)' } }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 24px rgba(124,77,255,0.4)' }}>
              {submitting && <Spinner size={16} color="#fff" />}
              {submitting ? 'Входим...' : 'Войти'}
            </button>
          </form>
        </div>

        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--text-3)' }}>
          Нет аккаунта?{' '}
          <Link to="/register" style={{ color: 'var(--violet)', fontWeight: 500 }}>Зарегистрироваться</Link>
        </div>
      </div>
    </div>
  )
}
