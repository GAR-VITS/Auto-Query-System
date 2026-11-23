import { useEffect, useState } from 'react'
import { healthCheck } from '@/services/api'

export function useBackendHealth(pollIntervalMs = 30000) {
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    let active = true

    const check = async () => {
      const ok = await healthCheck()
      if (active) setOnline(ok)
    }

    check()
    const interval = setInterval(check, pollIntervalMs)

    return () => {
      active = false
      clearInterval(interval)
    }
  }, [pollIntervalMs])

  return online
}
