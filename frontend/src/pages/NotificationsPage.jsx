import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'

export default function NotificationsPage() {
  return (
    <div className="p-8 max-w-[700px]">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-on-surface m-0">Alertas</h1>
        <Button variant="text" size="sm">Marcar todo leído</Button>
      </div>
      <EmptyState
        icon="notifications_off"
        title="Sin alertas por ahora"
        subtitle="Te notificaremos cuando aparezca una figurita que buscás, cuando recibas una propuesta o cuando una subasta esté por finalizar"
      />
    </div>
  )
}
