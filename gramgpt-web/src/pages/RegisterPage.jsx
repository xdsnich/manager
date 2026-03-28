import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../services/api'
import { Input, Spinner } from '../components/ui'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (password.length < 8) { setError('Пароль минимум 8 символов'); return }
    setSaving(true)
    try { await authAPI.register(email, password); navigate('/login') }
    catch (err) { setError(err.response?.data?.detail || 'Ошибка регистрации') }
    setSaving(false)
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
      position: 'relative', overflow: 'hidden',
    }}>
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0 }}>
        <div style={{ position: 'absolute', top: '15%', right: '20%', width: 400, height: 400, borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,61,154,0.1) 0%, transparent 70%)', filter: 'blur(40px)' }} />
        <div style={{ position: 'absolute', bottom: '20%', left: '15%', width: 350, height: 350, borderRadius: '50%', background: 'radial-gradient(circle, rgba(124,77,255,0.1) 0%, transparent 70%)', filter: 'blur(40px)' }} />
      </div>

      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 420, animation: 'fadeUp 0.45s cubic-bezier(0.16,1,0.3,1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 44 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
            <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #ff3d9a 0%, #7c4dff 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 800, color: '#fff', boxShadow: '0 8px 30px rgba(255,61,154,0.4)' }}>G</div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.03em' }}>
                Gram<span style={{ background: 'linear-gradient(135deg,#ff3d9a,#7c4dff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>GPT</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', letterSpacing: '0.04em' }}>MANAGER</div>
            </div>
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-3)' }}>Создай аккаунт для начала работы</div>
        </div>

        <div style={{ background: 'rgba(20,20,20,0.8)', border: '1px solid var(--border)', borderRadius: 20, padding: 32, backdropFilter: 'blur(20px)', boxShadow: '0 24px 80px rgba(0,0,0,0.5)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 24, letterSpacing: '-0.02em' }}>Регистрация</h2>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Input label="Email" type="email" value={email} onChange={e => { setEmail(e.target.value); setError('') }} placeholder="you@example.com" required autoFocus />
            <Input label="Пароль" type="password" value={password} onChange={e => { setPassword(e.target.value); setError('') }} placeholder="Минимум 8 символов" required />
            {error && <div style={{ padding: '10px 14px', background: 'var(--red-dim)', border: '1px solid rgba(248,81,73,0.25)', borderRadius: 10, fontSize: 13, color: 'var(--red)' }}>{error}</div>}
            <button type="submit" disabled={saving} style={{
              marginTop: 4, padding: 12,
              background: 'linear-gradient(135deg, #ff3d9a 0%, #7c4dff 100%)',
              color: '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700,
              cursor: saving ? 'not-allowed' : 'pointer', opacity: saving ? 0.7 : 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              boxShadow: '0 4px 24px rgba(255,61,154,0.35)', transition: 'transform 0.2s',
            }}>
              {saving && <Spinner size={16} color="#fff" />}
              {saving ? 'Создаём...' : 'Зарегистрироваться'}
            </button>
          </form>
        </div>
        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--text-3)' }}>
          Уже есть аккаунт?{' '}
          <Link to="/login" style={{ color: 'var(--violet)', fontWeight: 500 }}>Войти</Link>
        </div>
      </div>
    </div>
  )
}
