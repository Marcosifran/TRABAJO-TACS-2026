import { useState, useEffect } from 'react'
import Button from './ui/Button'
import { lineaCierraEn } from '../utils/auctionTime'

export default function SubastaCardRow({
  sub,
  pubsMap,
  user,
  users,
  onOfertar,
  onVerOfertas,
  showVerOfertasButton = true,
}) {
  const currentUserId = users.indexOf(user) + 1
  const isOwner = sub.usuario_id === currentUserId
  const [cierre, setCierre] = useState(() => lineaCierraEn(sub.fin))

  useEffect(() => {
    setCierre(lineaCierraEn(sub.fin))
    const id = setInterval(() => setCierre(lineaCierraEn(sub.fin)), 60000)
    return () => clearInterval(id)
  }, [sub.fin])

  return (
    <div className="p-5 bg-surface rounded-2xl border border-outline-variant flex justify-between items-center shadow-sm">
      <div>
        <h3 className="font-bold text-lg text-primary">
          Subasta #{sub.id}
        </h3>
        <p className="text-on-surface-variant text-sm mt-1">
          Figurita: {pubsMap[sub.figurita_id]
            ? `${pubsMap[sub.figurita_id].jugador} (${pubsMap[sub.figurita_id].equipo})`
            : `#${sub.figurita_id}`}{' '}
          <br />
          Propietario: {users[sub.usuario_id - 1]?.nombre ?? `Usuario ${sub.usuario_id}`}{' '}
          <br />
          {cierre && (
            <>
              {cierre}
              <br />
            </>
          )}
          Estado:{' '}
          <span className={`capitalize font-medium ${sub.estado === 'activa' ? 'text-green-600' : 'text-error'}`}>
            {sub.estado}
          </span>
        </p>
      </div>
      {!isOwner ? (
        <Button
          variant="tonal"
          icon="gavel"
          onClick={() => onOfertar(sub)}
        >
          Ofertar
        </Button>
      ) : showVerOfertasButton && onVerOfertas ? (
        <Button
          variant="outlined"
          icon="format_list_bulleted"
          onClick={() => onVerOfertas(sub)}
        >
          Ver ofertas
        </Button>
      ) : null}
    </div>
  )
}
