import { useEffect, useState } from 'react'
import { proxiesAPI } from '../services/api'
import { Button, Modal, Input, Empty, Spinner, Badge } from '../components/ui'

export default function ProxiesPage() {
  const [proxies, setProxies] = useState([])
  const [loading, setLoading] = useState(true)
  const [addModal, setAddModal] = useState(false)
  const [bulkModal, setBulkModal] = useState(false)
  const [form, setForm] = useState({ host: '', port: '', login: '', password: '', protocol: 'socks5' })
  const [bulkText, setBulkText] = useState('')
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try { const { data } = await proxiesAPI.list(); setProxies(data) } catch {}
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  const handleAdd = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      await proxiesAPI.create({ ...form, port: parseInt(form.port) })
      setAddModal(false); setForm({ host: '', port: '', login: '', password: '', protocol: 'socks5' }); await load()
    } catch (err) { alert(err.response?.data?.detail || 'Ошибка') }
    setSaving(false)
  }

  const handleBulk = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      const { data } = await proxiesAPI.bulkCreate(bulkText)
      alert(`Добавлено: ${data.added}. Ошибок: ${data.errors?.length || 0}`)
      setBulkModal(false); setBulkText(''); await load()
    } catch (err) { alert(err.response?.data?.detail || 'Ошибка') }
    setSaving(false)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Удалить прокси?')) return
    try { await proxiesAPI.delete(id); await load() } catch {}
  }

  const valid = proxies.filter(p => p.is_valid === true).length
  const invalid = proxies.filter(p => p.is_valid === false).length
  const unchecked = proxies.filter(p => p.is_valid === null).length

  return (
    <div style={{ padding: '28px 32px', animation: 'fadeUp 0.4s cubic-bezier(0.16,1,0.3,1)' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--teal)', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>◎ ПРОКСИ</div>
          <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.04em' }}>Управление прокси</h1>
          <div style={{ display: 'flex', gap: 14, marginTop: 6 }}>
            <span style={{ fontSize: 12, color: 'var(--green)' }}>✓ {valid} валидных</span>
            <span style={{ fontSize: 12, color: 'var(--red)' }}>✗ {invalid} нерабочих</span>
            <span style={{ fontSize: 12, color: 'var(--text-3)' }}>? {unchecked} не проверено</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="ghost" onClick={() => setBulkModal(true)}>📋 Загрузить список</Button>
          <Button variant="primary" onClick={() => setAddModal(true)}>+ Добавить</Button>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 64 }}><Spinner size={28} /></div>
      ) : proxies.length === 0 ? (
        <Empty icon="🔗" title="Нет прокси" subtitle="Добавь прокси для назначения на аккаунты"
          action={<Button variant="primary" onClick={() => setBulkModal(true)}>📋 Загрузить список</Button>} />
      ) : (
        <div style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 80px 1fr 100px 120px', padding: '10px 20px', borderBottom: '1px solid var(--border)', fontSize: 10, color: 'var(--text-3)', letterSpacing: '0.1em', fontWeight: 700, textTransform: 'uppercase' }}>
            <span>Адрес</span><span>Протокол</span><span>Логин</span><span>Статус</span><span style={{ textAlign: 'right' }}>Действия</span>
          </div>
          {proxies.map((p, i) => (
            <div key={p.id} style={{
              display: 'grid', gridTemplateColumns: '2fr 80px 1fr 100px 120px',
              padding: '13px 20px', alignItems: 'center',
              borderBottom: i < proxies.length - 1 ? '1px solid var(--border)' : 'none',
              transition: 'background 0.1s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{p.host}:{p.port}</div>
              <Badge color={p.protocol === 'socks5' ? 'violet' : 'blue'}>{p.protocol.toUpperCase()}</Badge>
              <div style={{ fontSize: 12, color: 'var(--text-2)' }}>{p.login || '—'}</div>
              <div>
                {p.is_valid === true && <Badge color="green">✓ OK</Badge>}
                {p.is_valid === false && <Badge color="red">✗ Нет</Badge>}
                {p.is_valid === null && <Badge color="default">? Не проверен</Badge>}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={() => handleDelete(p.id)} style={{
                  padding: '5px 10px', borderRadius: 7, border: '1px solid transparent',
                  background: 'transparent', color: 'var(--text-3)', fontSize: 11, cursor: 'pointer', transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'var(--red-dim)'; e.currentTarget.style.color = 'var(--red)'; e.currentTarget.style.borderColor = 'rgba(248,81,73,0.3)' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-3)'; e.currentTarget.style.borderColor = 'transparent' }}>
                  🗑 Удалить
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={addModal} onClose={() => setAddModal(false)} title="Добавить прокси">
        <form onSubmit={handleAdd} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px', gap: 10 }}>
            <Input label="Host" value={form.host} onChange={e => setForm(d => ({ ...d, host: e.target.value }))} placeholder="1.2.3.4" required />
            <Input label="Port" value={form.port} onChange={e => setForm(d => ({ ...d, port: e.target.value }))} placeholder="1080" type="number" required />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <Input label="Логин" value={form.login} onChange={e => setForm(d => ({ ...d, login: e.target.value }))} placeholder="user" />
            <Input label="Пароль" value={form.password} onChange={e => setForm(d => ({ ...d, password: e.target.value }))} type="password" placeholder="pass" />
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Протокол</label>
            <select value={form.protocol} onChange={e => setForm(d => ({ ...d, protocol: e.target.value }))} style={{ width: '100%', padding: '10px 14px', background: 'var(--bg-3)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text)', fontSize: 14, outline: 'none' }}>
              <option value="socks5">SOCKS5</option>
              <option value="http">HTTP</option>
            </select>
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
            <Button variant="ghost" type="button" onClick={() => setAddModal(false)}>Отмена</Button>
            <Button variant="primary" type="submit" loading={saving}>Добавить</Button>
          </div>
        </form>
      </Modal>

      <Modal open={bulkModal} onClose={() => setBulkModal(false)} title="Загрузить список прокси" width={520}>
        <form onSubmit={handleBulk} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ padding: '12px 14px', background: 'rgba(124,77,255,0.08)', border: '1px solid rgba(124,77,255,0.15)', borderRadius: 10, fontSize: 12, color: 'var(--text-2)', lineHeight: 1.8 }}>
            Поддерживаемые форматы:<br />
            <code style={{ color: 'var(--violet)' }}>socks5://login:pass@host:port</code><br />
            <code style={{ color: 'var(--violet)' }}>host:port:login:pass</code><br />
            <code style={{ color: 'var(--violet)' }}>host:port</code>
          </div>
          <textarea value={bulkText} onChange={e => setBulkText(e.target.value)} placeholder={"1.2.3.4:1080:user:pass\n5.6.7.8:1080\n..."} rows={8} style={{
            background: 'var(--bg-3)', border: '1px solid var(--border)', borderRadius: 10,
            color: 'var(--text)', padding: '12px 14px', fontSize: 13,
            fontFamily: 'var(--font-mono)', resize: 'vertical', outline: 'none',
          }} />
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <Button variant="ghost" type="button" onClick={() => setBulkModal(false)}>Отмена</Button>
            <Button variant="primary" type="submit" loading={saving}>Загрузить</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
