import { useState } from 'react'
import Tabs from '../components/ui/Tabs'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'
import Avatar from '../components/ui/Avatar'
import StarRating from '../components/ui/StarRating'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'
import Card from '../components/ui/Card'
import Icon from '../components/ui/Icon'

export default function TradesPage() {
  const [tab, setTab]             = useState('recibidas')
  const [ratingModal, setRatingModal] = useState(null)
  const [rating, setRating]       = useState(0)
  const [snack, setSnack]         = useState({ open: false, message: '', type: 'info' })

  return (
    <div className="p-8 max-w-[900px]">
      <h1 className="text-3xl font-bold text-on-surface mb-5">Intercambios</h1>

      <Tabs
        tabs={[
          { id: 'recibidas',   label: 'Recibidas (0)' },
          { id: 'enviadas',    label: 'Enviadas (0)' },
          { id: 'sugerencias', label: 'Sugerencias automáticas' },
        ]}
        active={tab}
        onChange={setTab}
      />

      <div className="mt-5">
        {tab === 'sugerencias' ? (
          <div>
            <Card
              style={{
                background: 'linear-gradient(135deg, var(--color-primary-container), var(--color-tertiary-container))',
                border: 'none',
                marginBottom: 16,
              }}
            >
              <div className="flex items-center gap-3">
                <Icon name="auto_awesome" size={28} className="text-primary" />
                <div>
                  <div className="font-semibold text-[15px] text-on-primary-container">Sugerencias inteligentes</div>
                  <div className="text-[13px] text-on-primary-container/80">Basadas en tus faltantes y las repetidas de otros usuarios</div>
                </div>
              </div>
            </Card>
            <EmptyState
              icon="auto_awesome"
              title="Sin sugerencias por ahora"
              subtitle="Registrá tus faltantes y publicá tus repetidas para recibir sugerencias automáticas"
            />
          </div>
        ) : (
          <EmptyState
            icon="swap_horiz"
            title={tab === 'recibidas' ? 'Sin propuestas recibidas' : 'Sin propuestas enviadas'}
            subtitle={tab === 'recibidas'
              ? 'Cuando alguien te proponga un intercambio aparecerá acá'
              : 'Las propuestas que enviés a otros usuarios aparecerán acá'
            }
          />
        )}
      </div>

      {/* Rating Modal */}
      <Modal open={!!ratingModal} onClose={() => setRatingModal(null)} title="Calificar usuario" width={380}>
        <div className="text-center py-2.5">
          <Avatar name={ratingModal || ''} size={56} />
          <div className="font-semibold text-base mt-2.5 text-on-surface">{ratingModal}</div>
          <p className="text-on-surface-variant text-sm mt-2 mb-4">¿Cómo fue la experiencia de intercambio?</p>
          <StarRating value={rating} onChange={setRating} size={36} />
          <div className="mt-5">
            <Button onClick={() => {
              setRatingModal(null)
              setSnack({ open: true, message: 'Calificación enviada', type: 'success' })
            }}>
              Calificar
            </Button>
          </div>
        </div>
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
