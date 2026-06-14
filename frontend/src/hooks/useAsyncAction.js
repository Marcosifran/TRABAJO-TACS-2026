import { useState, useCallback } from 'react'

/**
 * Encapsulates pending/error state for async write operations (POST/PATCH/DELETE).
 * Re-throws so the caller can still react (e.g. keep modal open on error).
 */
export function useAsyncAction() {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(null)

  const run = useCallback(async (fn) => {
    setPending(true)
    setError(null)
    try {
      return await fn()
    } catch (e) {
      setError(e)
      throw e
    } finally {
      setPending(false)
    }
  }, [])

  return { run, pending, error }
}
