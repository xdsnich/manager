import { useState } from 'react'
import { tasksAPI } from '../services/api'
import { Card, Button, Spinner, Badge } from '../components/ui'

export default function TasksPage() {
  const [tasks, setTasks] = useState([])
  const [running, setRunning] = useState({})

  const startTask = async (name, starter) => {
    try {
      const { data } = await starter()
      setTasks(prev => [{ id: data.task_id, name, status: 'PROGRESS', progress: 0, message: 'Запускаю...' }, ...prev])
      setRunning(prev => ({ ...prev, [name]: data.task_id }))
      poll(data.task_id, name)
    } catch (err) { alert(err.response?.data?.detail || 'Ошибка запуска') }
  }

  const poll = (taskId, name) => {
    const iv = setInterval(async () => {
      try {
        const { data } = await tasksAPI.getStatus(taskId)
        setTasks(prev => prev.map(t => t.id === taskId ? {
          ...t, status: data.status,
          progress: data.progress?.percent || 0,
          message: data.progress?.message || (data.status === 'SUCCESS' ? '✓ Завершено' : data.status),
          result: data.result,
        } : t))
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
          clearInterval(iv)
          setRunning(prev => { const n = { ...prev }; delete n[name]; return n })
        }
      } catch { clearInterval(iv); setRunning(prev => { const n = { ...prev }; delete n[name]; return n }) }
    }, 1000)
  }

  const TASKS = [
    { name: 'check_accounts', title: '⚡ Проверить аккаунты', subtitle: 'Статус всех аккаунтов без @SpamBot', color: 'var(--violet)', starter: () => tasksAPI.checkAccounts(false) },
    { name: 'check_spam',     title: '🔍 Проверить спамблок', subtitle: '~15 сек/аккаунт через @SpamBot',    color: 'var(--blue)',   starter: () => tasksAPI.checkAccounts(true) },
    { name: 'check_proxies',  title: '🔗 Проверить прокси',  subtitle: 'Параллельная проверка всех прокси', color: 'var(--teal)',   starter: () => tasksAPI.checkProxies() },
  ]

  return (
    <div style={{ padding: '28px 32px', animation: 'fadeUp 0.4s cubic-bezier(0.16,1,0.3,1)' }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 11, color: 'var(--pink)', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>◆ ЗАДАЧИ</div>
        <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.04em' }}>Фоновые задачи</h1>
        <p style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 4 }}>Выполняются через Celery — нужен запущенный воркер</p>
      </div>

      {/* Task cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 32 }}>
        {TASKS.map(t => (
          <div key={t.name} style={{
            background: 'var(--bg-2)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', padding: 22,
            transition: 'border-color 0.2s, transform 0.2s',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = `${t.color}44`; e.currentTarget.style.transform = 'translateY(-2px)' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = 'translateY(0)' }}>
            <div style={{ fontSize: 22, marginBottom: 10 }}>{t.title.split(' ')[0]}</div>
            <div style={{ fontWeight: 700, fontSize: 14, letterSpacing: '-0.02em', marginBottom: 6 }}>{t.title.slice(2)}</div>
            <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 18, lineHeight: 1.5 }}>{t.subtitle}</div>
            <button
              disabled={!!running[t.name]}
              onClick={() => startTask(t.name, t.starter)}
              style={{
                width: '100%', padding: '10px', borderRadius: 10, border: 'none',
                background: running[t.name] ? 'rgba(255,255,255,0.06)' : `linear-gradient(135deg, ${t.color}, ${t.color}bb)`,
                color: running[t.name] ? 'var(--text-2)' : '#fff',
                fontSize: 13, fontWeight: 600, cursor: running[t.name] ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                transition: 'all 0.2s',
              }}>
              {running[t.name] && <Spinner size={14} color="#fff" />}
              {running[t.name] ? 'Выполняется...' : 'Запустить'}
            </button>
          </div>
        ))}
      </div>

      {/* Task log */}
      {tasks.length > 0 && (
        <>
          <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, letterSpacing: '-0.02em' }}>Лог задач</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {tasks.map(t => (
              <div key={t.id} style={{
                background: 'var(--bg-2)', border: '1px solid var(--border)',
                borderRadius: 12, padding: '14px 18px',
                display: 'flex', alignItems: 'center', gap: 12,
              }}>
                {t.status === 'PROGRESS' && <Spinner size={16} />}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{t.name}</span>
                    <Badge color={t.status === 'SUCCESS' ? 'green' : t.status === 'FAILURE' ? 'red' : 'violet'}>
                      {t.status}
                    </Badge>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-2)' }}>{t.message}</div>
                  {t.status === 'PROGRESS' && t.progress > 0 && (
                    <div style={{ marginTop: 8, height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
                      <div style={{ width: `${t.progress}%`, height: '100%', background: 'linear-gradient(90deg, #7c4dff, #3d8bff)', transition: 'width 0.5s ease' }} />
                    </div>
                  )}
                  {t.status === 'SUCCESS' && t.result && (
                    <div style={{ marginTop: 6, fontSize: 11, color: 'var(--text-3)' }}>
                      Всего: {t.result.total} · Активных: {t.result.active} · Спам: {t.result.spam || 0}
                    </div>
                  )}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>{t.id?.slice(0, 8)}…</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Celery setup hint */}
      <div style={{ marginTop: 28, padding: '18px 22px', background: 'rgba(124,77,255,0.06)', border: '1px solid rgba(124,77,255,0.15)', borderRadius: 14 }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8, letterSpacing: '-0.02em' }}>⚙ Как запустить Celery воркер</div>
        <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 10 }}>В папке <code style={{ color: 'var(--violet)', fontFamily: 'var(--font-mono)' }}>api/</code> активируй venv и запусти:</div>
        <pre style={{
          padding: '12px 16px', background: 'var(--bg-3)', borderRadius: 10,
          fontSize: 12, color: 'var(--violet)', fontFamily: 'var(--font-mono)',
          overflowX: 'auto', lineHeight: 1.8,
        }}>{`cd api\nvenv\\Scripts\\activate\npython -m celery -A celery_app worker -Q high_priority,bulk_actions --loglevel=info -P solo`}</pre>
      </div>
    </div>
  )
}
