import Button from './ui/Button'
import { lineaCierraEn, isAuctionActive } from '../utils/auctionTime'
import { useNow } from '../hooks/useNow'

export default function SubastaCardRow({
  sub,
  pubsMap,
  user,
  users,
  onOfertar,
  onVerOfertas,
  onCancelar,
  showVerOfertasButton = true,
}) {
  const isOwner = sub.usuario_id === user.id
  const now = useNow()
  const activa = isAuctionActive(sub, now)
  const cierre = lineaCierraEn(sub.fin)

  return (
    <div className="p-5 bg-surface rounded-2xl border border-outline-variant flex flex-wrap items-center gap-4 justify-between shadow-sm">
      <div>
        <h3 className="font-bold text-lg text-primary">
          {pubsMap[sub.figurita_id]
            ? `${pubsMap[sub.figurita_id].jugador} — ${users.find(u => u.id === sub.usuario_id)?.nombre ?? `Usuario ${sub.usuario_id}`}`
            : `Subasta #${sub.id}`}
        </h3>
        <p className="text-on-surface-variant text-sm mt-1">
          {pubsMap[sub.figurita_id] && (
            <>
              {pubsMap[sub.figurita_id].equipo}
              <br />
            </>
          )}
          {activa && cierre && (
            <>
              {cierre}
              <br />
            </>
          )}
          Estado:{' '}
          <span className={`capitalize font-medium ${activa ? 'text-green-600' : 'text-error'}`}>
            {activa ? 'activa' : 'finalizada'}
          </span>
        </p>
      </div>
      <div className="flex gap-2">
        {!isOwner && activa ? (
          <Button variant="tonal" icon="gavel" onClick={() => onOfertar(sub)}>
            Ofertar
          </Button>
        ) : showVerOfertasButton && onVerOfertas ? (
          <Button variant="outlined" icon="format_list_bulleted" onClick={() => onVerOfertas(sub)}>
            Ver ofertas
          </Button>
        ) : null}
        {isOwner && activa && onCancelar && (
          <Button variant="outlined" icon="cancel" onClick={() => onCancelar(sub)}>
            Cancelar
          </Button>
        )}
      </div>
    </div>
  )
}
