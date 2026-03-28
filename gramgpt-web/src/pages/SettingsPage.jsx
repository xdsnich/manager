import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { authAPI } from '../services/api'
import { Card, Input, Button, Badge } from '../components/ui'

export default function SettingsPage() {
  const { user } = useAuthStore()
  const [oldPwd, setOldPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [confirmPwd, setConfirmPwd] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)

  const handleChangePassword = async (e) => {
    e.preventDefault()
    if (newPwd !== confirmPwd) { setMsg({ type: 'error', text: 'Пароли не совпадают' }); return }
    if (newPwd.length < 8) { setMsg({ type: 'error', text: 'Минимум 8 символов' }); return }
    setSaving(true)
    try {
      await authAPI.changePassword(oldPwd, newPwd)
      setMsg({ type: 'success', text: 'Пароль изменён. Войди заново.' })
      setOldPwd(''); setNewPwd(''); setConfirmPwd('')
    } catch (err) { setMsg({ type: 'error', text: err.response?.data?.detail || 'Ошибка' }) }
    setSaving(false)
  }

  return (
    <div style={{ padding: '28px 32px', maxWidth: 560, animation: 'fadeUp 0.4s cubic-bezier(0.16,1,0.3,1)' }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 11, color: 'var(--yellow)', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>◐ НАСТРОЙКИ</div>
        <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.04em' }}>Настройки аккаунта</h1>
      </div>

      {/* Profile */}
      <div style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24, marginBottom: 16 }}>
        <h3 style={{ fontWeight: 700, fontSize: 14, marginBottom: 18, letterSpacing: '-0.02em' }}>Профиль</h3>
        {[
          ['Email', user?.email, 'default'],
          ['Тариф', (user?.plan || '—').toUpperCase(), 'violet'],
          ['Лимит аккаунтов', user?.account_limit, 'blue'],
          ['Верификация', user?.is_verified ? 'Подтверждён' : 'Не подтверждён', user?.is_verified ? 'green' : 'red'],
        ].map(([label, val, color]) => (
          <div key={label} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '10px 0', borderBottom: '1px solid var(--border)',
          }}>
            <span style={{ fontSize: 13, color: 'var(--text-3)' }}>{label}</span>
            <Badge color={color}>{val}</Badge>
          </div>
        ))}
      </div>

      {/* Change password */}
      <div style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24 }}>
        <h3 style={{ fontWeight: 700, fontSize: 14, marginBottom: 18, letterSpacing: '-0.02em' }}>Сменить пароль</h3>
        <form onSubmit={handleChangePassword} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input label="Текущий пароль" type="password" value={oldPwd} onChange={e => setOldPwd(e.target.value)} required />
          <Input label="Новый пароль" type="password" value={newPwd} onChange={e => setNewPwd(e.target.value)} required />
          <Input label="Повтор пароля" type="password" value={confirmPwd} onChange={e => setConfirmPwd(e.target.value)} required />
          {msg && (
            <div style={{
              padding: '10px 14px', borderRadius: 10, fontSize: 13,
              background: msg.type === 'error' ? 'var(--red-dim)' : 'var(--green-dim)',
              color: msg.type === 'error' ? 'var(--red)' : 'var(--green)',
              border: `1px solid ${msg.type === 'error' ? 'rgba(248,81,73,0.25)' : 'rgba(61,214,140,0.25)'}`,
            }}>{msg.text}</div>
          )}
          <Button variant="primary" type="submit" loading={saving}>Сохранить</Button>
        </form>
      </div>
    </div>
  )
}
