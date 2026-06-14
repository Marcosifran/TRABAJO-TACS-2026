import { useState, useCallback, useRef } from 'react'

export function useModalForm(initial) {
  const initialRef = useRef(initial)
  const [open, setOpen] = useState(null)
  const [form, setForm] = useState(initial)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(null)

  const close = useCallback(() => {
    setOpen(null)
    setForm(initialRef.current)
    setError(null)
  }, [])

  // formOverride lets callers pre-fill the form when opening (e.g. editing existing data)
  const openWith = useCallback((ctx = true, formOverride) => {
    setForm(formOverride !== undefined ? formOverride : initialRef.current)
    setError(null)
    setOpen(ctx)
  }, [])

  return { open, openWith, close, form, setForm, pending, setPending, error, setError }
}
