import { useCallback, useEffect, useMemo, useState } from 'react'
import api from '../services/api'

/**
 * Fetch and mutate a paginated API resource.
 *
 * Handles loading, error, empty and pagination state so every list page gets
 * consistent behaviour without duplicating the logic.
 */
export function useResource(endpoint, { params = {}, auto = true, pageSize = 25 } = {}) {
  const [rows, setRows] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [numPages, setNumPages] = useState(1)
  const [loading, setLoading] = useState(auto)
  const [error, setError] = useState(null)
  const [reloadToken, setReloadToken] = useState(0)

  const paramsKey = JSON.stringify(params)

  const query = useMemo(
    () => ({ ...params, page, page_size: pageSize }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [paramsKey, page, pageSize],
  )

  const load = useCallback(async () => {
    if (!endpoint) return
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.get(endpoint, { params: query })
      if (Array.isArray(data)) {
        setRows(data)
        setCount(data.length)
        setNumPages(1)
      } else {
        setRows(data.results || [])
        setCount(data.count ?? (data.results || []).length)
        setNumPages(data.num_pages || 1)
      }
    } catch (err) {
      setError(err.friendlyMessage || 'Unable to load records.')
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [endpoint, query])

  useEffect(() => {
    if (auto) load()
  }, [load, auto, reloadToken])

  useEffect(() => {
    setPage(1)
  }, [paramsKey])

  const create = useCallback(
    async (payload) => {
      const { data } = await api.post(endpoint, payload)
      await load()
      return data
    },
    [endpoint, load],
  )

  const update = useCallback(
    async (id, payload) => {
      const { data } = await api.patch(`${endpoint}${id}/`, payload)
      await load()
      return data
    },
    [endpoint, load],
  )

  const remove = useCallback(
    async (id) => {
      await api.delete(`${endpoint}${id}/`)
      await load()
    },
    [endpoint, load],
  )

  return {
    rows,
    count,
    page,
    setPage,
    numPages,
    loading,
    error,
    reload: () => setReloadToken((token) => token + 1),
    create,
    update,
    remove,
    setRows,
  }
}

export default useResource
