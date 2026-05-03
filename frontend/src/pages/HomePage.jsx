import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Icon from '../components/ui/Icon'
import EmptyState from '../components/ui/EmptyState'
import FiguritaCard from '../components/FiguritaCard'
import { listarMisPublicaciones, buscarPublicaciones } from '../api/publicaciones'
import { listarFaltantes, obtenerReputacion } from '../api/faltantes'
import { listarIntercambios } from '../api/intercambios'

import { listarMiAlbum } from '../api/album'

export default function HomePage() {
  const navigate = useNavigate()
  const [figuritasCount, setFiguritasCount] = useState('—')
  const [faltanCount, setFaltanCount] = useState('—')
  const [intercambiosCount, setIntercambiosCount] = useState('—')
  const [reputacion, setReputacion] = useState('—')
  const [ultimasPublicadas, setUltimasPublicadas] = useState([])

  useEffect(() => {
    listarMiAlbum()
      .then(data => setFiguritasCount(data.length))
      .catch(() => {})
    listarFaltantes()
      .then(data => setFaltanCount(data.faltantes.length))
      .catch(() => {})
    listarIntercambios()
      .then(data => setIntercambiosCount((data.enviados?.length || 0) + (data.recibidos?.length || 0)))
      .catch(() => {})
    // Nota: El ID del usuario debería venir del contexto. Uso 1 como fallback si no hay.
    obtenerReputacion(1)
      .then(data => setReputacion(data.promedio?.toFixed(1) || '5.0'))
      .catch(() => {})
    buscarPublicaciones()
      .then(data => setUltimasPublicadas(data.slice(-4).reverse()))
      .catch(() => {})
  }, [])

  const STATS = [
    { icon: 'collections_bookmark', label: 'Figuritas',   value: figuritasCount, colorVar: 'var(--color-primary)' },
    { icon: 'playlist_add',         label: 'Faltan',       value: faltanCount,    colorVar: 'var(--color-secondary)' },
    { icon: 'swap_horiz',           label: 'Intercambios', value: intercambiosCount, colorVar: 'var(--color-tertiary)' },
    { icon: 'star',                 label: 'Reputación',   value: reputacion,     colorVar: 'var(--color-gold)' },
  ]

  return (
    <div className="p-8 max-w-[1100px]">
      <div className="mb-7">
        <h1 className="text-3xl font-bold text-on-surface m-0">Bienvenido de vuelta 👋</h1>
        <p className="mt-1 text-on-surface-variant text-[15px]">Tu resumen de actividad en FiguSwap</p>
      </div>

      {/* Estadisticas Figuritas - Faltan - Intercambios - Reputación */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {STATS.map((s, i) => (
          <Card key={i} elevated>
            <div className="flex items-center gap-3.5">
              <div
                className="w-11 h-11 rounded-[14px] flex items-center justify-center shrink-0"
                style={{ background: s.colorVar + '18' }}
              >
                <Icon name={s.icon} size={24} style={{ color: s.colorVar }} />
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">{s.value}</div>
                <div className="text-[13px] text-on-surface-variant">{s.label}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Acciones Publicar Figurita - Buscar Figuritas - Ver Subastas */}
      <div className="flex gap-2.5 mb-8">
        <Button icon="add" onClick={() => navigate('/coleccion')}>Publicar figurita</Button>
        <Button variant="tonal" icon="search" onClick={() => navigate('/buscar')}>Buscar figuritas</Button>
        <Button variant="outlined" icon="gavel" onClick={() => navigate('/subastas')}>Ver subastas</Button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Últimas publicadas */}
        <div>
          <div className="flex justify-between items-center mb-3.5">
            <h2 className="text-lg font-semibold m-0">Últimas publicadas</h2>
            <Button variant="text" size="sm" onClick={() => navigate('/buscar')}>Ver todas</Button>
          </div>
          {ultimasPublicadas.length === 0 ? (
            <EmptyState
              icon="style"
              title="Sin figuritas publicadas"
              subtitle="Todavía no hay figuritas disponibles para intercambio"
            />
          ) : (
            <div className="flex flex-col gap-2">
              {ultimasPublicadas.map(pub => (
                <FiguritaCard
                  key={pub.id}
                  compact
                  figurita={{
                    id: pub.id,
                    numero: pub.numero,
                    seleccion: pub.equipo,
                    jugador: pub.jugador,
                    tipo: pub.tipo_intercambio === 'intercambio_directo' ? 'intercambio' : 'subasta',
                    cantidad: pub.cantidad_disponible,
                    owner: `Usuario ${pub.usuario_id}`,
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Subastas y Sugerencias */}
        <div>
          <div className="flex justify-between items-center mb-3.5">
            <h2 className="text-lg font-semibold m-0">Subastas por finalizar</h2>
            <Button variant="text" size="sm" onClick={() => navigate('/subastas')}>Ver todas</Button>
          </div>
          <EmptyState
            icon="gavel"
            title="Sin subastas activas"
            subtitle="No hay subastas próximas a finalizar"
          />

          {/* Sugerencias */}
          <h2 className="text-lg font-semibold mt-6 mb-3.5">Sugerencias para vos</h2>
          <Card
            style={{
              background: 'linear-gradient(135deg, var(--color-primary-container), var(--color-tertiary-container))',
              border: 'none',
            }}
          >
            <div className="flex items-center gap-3">
              <Icon name="auto_awesome" size={28} className="text-primary" />
              <div className="flex-1">
                <div className="font-semibold text-[14px] text-on-primary-container">Sin sugerencias aún</div>
                <div className="text-[13px] text-on-primary-container/80">Registrá tus faltantes para recibir sugerencias automáticas</div>
              </div>
              <Button size="sm" onClick={() => navigate('/intercambios')}>Ver</Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
