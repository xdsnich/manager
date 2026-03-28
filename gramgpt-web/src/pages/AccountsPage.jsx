import { useEffect, useState } from 'react'
import { accountsAPI } from '../services/api'
import { Card, Button, Input, Modal, TrustBar, StatusBadge, Empty, Spinner, Badge } from '../components/ui'

const ROLES = ['default', 'продавец', 'прогреватель', 'читатель', 'консультант']
const STATUS_FILTERS = [
  { key: 'all', label: 'Все' },
  { key: 'active', label: '● Живые' },
  { key: 'spamblock', label: '● Спам' },
  { key: 'frozen', label: '● Заморожено' },
  { key: 'unknown', label: '● Неизвестно' },
]

export default function AccountsPage() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [selected, setSelected] = useState(null)
  const [addModal, setAddModal] = useState(false)
  const [editModal, setEditModal] = useState(false)
  const [phone, setPhone] = useState('')
  const [editData, setEditData] = useState({})
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try { const { data } = await accountsAPI.list(); setAccounts(data) } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const filtered = accounts.filter(a => {
    const q = search.toLowerCase()
    const matchSearch = !q || [a.phone, a.username, a.first_name, a.last_name, a.status].some(v => (v || '').toLowerCase().includes(q))
    const matchStatus = filterStatus === 'all' || a.status === filterStatus
    return matchSearch && matchStatus
  })

  const handleAdd = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      await accountsAPI.create(phone.startsWith('+') ? phone : '+' + phone)
      setAddModal(false); setPhone(''); await load()
    } catch (err) { alert(err.response?.data?.detail || 'Ошибка') }
    setSaving(false)
  }

  const handleEdit = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      await accountsAPI.update(selected.id, editData)
      setEditModal(false); await load()
    } catch (err) { alert(err.response?.data?.detail || 'Ошибка') }
    setSaving(false)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Удалить аккаунт?')) return
    try { await accountsAPI.delete(id); await load() } catch {}
  }

  const openEdit = (acc) => {
    setSelected(acc)
    setEditData({ role: acc.role, notes: acc.notes || '', tags: acc.tags || [] })
    setEditModal(true)
  }

  return (
    <div style={{ padding: '28px 32px', animation: 'fadeUp 0.4s cubic-bezier(0.16,1,0.3,1)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--blue)', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>◉ АККАУНТЫ</div>
          <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.04em' }}>Управление аккаунтами</h1>
          <p style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 4 }}>{accounts.length} аккаунтов в базе</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="ghost" onClick={() => accountsAPI.importJson().then(load)}>📥 Импорт JSON</Button>
          <Button variant="primary" onClick={() => setAddModal(true)}>+ Добавить</Button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, maxWidth: 300 }}>
          <Input placeholder="🔍  Поиск..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {STATUS_FILTERS.map(({ key, label }) => (
            <button key={key} onClick={() => setFilterStatus(key)} style={{
              padding: '9px 14px', borderRadius: 10, cursor: 'pointer',
              border: `1px solid ${filterStatus === key ? 'rgba(124,77,255,0.4)' : 'var(--border)'}`,
              background: filterStatus === key ? 'rgba(124,77,255,0.15)' : 'transparent',
              color: filterStatus === key ? 'var(--violet)' : 'var(--text-2)',
              fontSize: 12, fontWeight: filterStatus === key ? 600 : 400,
              transition: 'all 0.15s',
            }}>{label}</button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 64 }}><Spinner size={28} /></div>
      ) : filtered.length === 0 ? (
        <Empty icon="👤" title="Нет аккаунтов"
          subtitle={search || filterStatus !== 'all' ? 'Попробуй изменить фильтры' : 'Добавь первый аккаунт'}
          action={!search && filterStatus === 'all' && <Button variant="primary" onClick={() => setAddModal(true)}>+ Добавить</Button>} />
      ) : (
        <div style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          {/* Header row */}
          <div style={{
            display: 'grid', gridTemplateColumns: '2fr 1.2fr 1fr 1.2fr 100px 100px',
            padding: '10px 20px', borderBottom: '1px solid var(--border)',
            fontSize: 10, color: 'var(--text-3)', letterSpacing: '0.1em', fontWeight: 700, textTransform: 'uppercase',
          }}>
            <span>Аккаунт</span><span>Телефон</span><span>Статус</span><span>Trust</span><span>Роль</span><span style={{ textAlign: 'right' }}>Действия</span>
          </div>

          {filtered.map((acc, i) => (
            <div key={acc.id} style={{
              display: 'grid', gridTemplateColumns: '2fr 1.2fr 1fr 1.2fr 100px 100px',
              padding: '14px 20px', alignItems: 'center',
              borderBottom: i < filtered.length - 1 ? '1px solid var(--border)' : 'none',
              transition: 'background 0.1s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              {/* Name + avatar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                  background: 'linear-gradient(135deg, rgba(124,77,255,0.25), rgba(61,139,255,0.15))',
                  border: '1px solid rgba(124,77,255,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700, color: 'var(--violet)',
                }}>{acc.first_name?.[0]?.toUpperCase() || '?'}</div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{acc.first_name || '—'} {acc.last_name || ''}</div>
                  {acc.username && <div style={{ fontSize: 11, color: 'var(--text-3)' }}>@{acc.username}</div>}
                </div>
              </div>

              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)' }}>{acc.phone}</div>
              <StatusBadge status={acc.status} />
              <TrustBar score={acc.trust_score} />
              <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{acc.role}</div>

              {/* Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 4 }}>
                <button onClick={() => openEdit(acc)} style={{
                  padding: '5px 10px', borderRadius: 7,
                  border: '1px solid var(--border)', background: 'transparent',
                  color: 'var(--text-2)', fontSize: 11, cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(124,77,255,0.4)'; e.currentTarget.style.color = 'var(--violet)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-2)' }}>
                  ✏ Ред.
                </button>
                <button onClick={() => handleDelete(acc.id)} style={{
                  padding: '5px 8px', borderRadius: 7,
                  border: '1px solid transparent', background: 'transparent',
                  color: 'var(--text-3)', fontSize: 11, cursor: 'pointer', transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(248,81,73,0.3)'; e.currentTarget.style.color = 'var(--red)'; e.currentTarget.style.background = 'var(--red-dim)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'transparent'; e.currentTarget.style.color = 'var(--text-3)'; e.currentTarget.style.background = 'transparent' }}>
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ADD Modal */}
      <Modal open={addModal} onClose={() => setAddModal(false)} title="Добавить аккаунт">
        <form onSubmit={handleAdd} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Input label="Номер телефона" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+380991234567" required autoFocus />
          <div style={{ padding: '12px 14px', background: 'rgba(124,77,255,0.08)', border: '1px solid rgba(124,77,255,0.15)', borderRadius: 10, fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6 }}>
            💡 После добавления авторизуй через <code style={{ color: 'var(--violet)' }}>python main.py</code>, затем нажми «Импорт JSON»
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <Button variant="ghost" type="button" onClick={() => setAddModal(false)}>Отмена</Button>
            <Button variant="primary" type="submit" loading={saving}>Добавить</Button>
          </div>
        </form>
      </Modal>

      {/* EDIT Modal */}
      <Modal open={editModal} onClose={() => setEditModal(false)} title={`Редактировать — ${selected?.phone}`}>
        <form onSubmit={handleEdit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Роль</label>
            <select value={editData.role || 'default'} onChange={e => setEditData(d => ({ ...d, role: e.target.value }))} style={{
              width: '100%', padding: '10px 14px', background: 'var(--bg-3)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
              color: 'var(--text)', fontSize: 14, outline: 'none',
            }}>{ROLES.map(r => <option key={r} value={r}>{r}</option>)}</select>
          </div>
          <Input label="Заметка" value={editData.notes || ''} onChange={e => setEditData(d => ({ ...d, notes: e.target.value }))} placeholder="Заметка..." />
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <Button variant="ghost" type="button" onClick={() => setEditModal(false)}>Отмена</Button>
            <Button variant="primary" type="submit" loading={saving}>Сохранить</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
