import { useRef } from 'react'

export default function TiltCard({ children }) {
  const cardRef = useRef(null)

  const handleMouseMove = (e) => {
    const card = cardRef.current
    if (!card) return

    const rect = card.getBoundingClientRect()

    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const centerX = rect.width / 2
    const centerY = rect.height / 2

    const rotateY = ((x - centerX) / centerX) * 15
    const rotateX = -((y - centerY) / centerY) * 15

    card.style.transform = `
      rotateX(${rotateX}deg)
      rotateY(${rotateY}deg)
      scale3d(1.03, 1.03, 1.03)
    `

    card.style.setProperty('--mouse-x', `${x}px`)
    card.style.setProperty('--mouse-y', `${y}px`)
  }

  const handleMouseLeave = () => {
    const card = cardRef.current
    if (!card) return

    card.style.transform = 'rotateX(0deg) rotateY(0deg) scale3d(1,1,1)'
  }

  return (
    <div className="perspective w-full h-full">
      <div
        ref={cardRef}
        className="tilt-card w-full h-full"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <div className="w-full h-full">{children}</div>
      </div>
    </div>
  )
}
