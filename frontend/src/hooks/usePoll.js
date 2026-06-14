import { useEffect, useRef } from 'react'

/**
 * Polls `fn` immediately and then every `intervalMs`.
 * Re-runs (resets interval) when `deps` change.
 * Uses a ref so interval always calls the latest version of `fn`
 * without re-registering the interval on each render.
 */
export function usePoll(fn, intervalMs, deps = []) {
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    let cancelled = false
    function tick() {
      if (!cancelled) fnRef.current()
    }
    tick()
    const t = setInterval(tick, intervalMs)
    return () => {
      cancelled = true
      clearInterval(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
