import { ApiProblemError, apiFetch } from './fetcher'

afterEach(() => {
  vi.unstubAllGlobals()
  document.cookie = 'lemoo_csrf=; Max-Age=0; Path=/'
})

describe('apiFetch', () => {
  it('uses same-origin credentials without adding CSRF to safe reads', async () => {
    const fetchMock = vi.fn(async (...request: Parameters<typeof fetch>) => {
      void request
      return Promise.resolve(
        new Response(JSON.stringify({ items: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiFetch<{ items: unknown[] }>('/api/v1/devices')).resolves.toEqual({
      items: [],
    })
    const options = fetchMock.mock.calls[0]?.[1]
    expect(options?.credentials).toBe('include')
    expect(new Headers(options?.headers).has('X-CSRF-Token')).toBe(false)
  })

  it('adds the double-submit CSRF token to mutations', async () => {
    document.cookie = 'lemoo_csrf=synthetic-token; Path=/'
    const fetchMock = vi.fn(async (...request: Parameters<typeof fetch>) => {
      void request
      return Promise.resolve(
        new Response(JSON.stringify({ id: 'command-1' }), {
          status: 202,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
    })
    vi.stubGlobal('fetch', fetchMock)

    await apiFetch('/api/v1/device-commands', {
      method: 'POST',
      body: JSON.stringify({ command_type: 'refresh_shadow' }),
    })

    const options = fetchMock.mock.calls[0]?.[1]
    expect(new Headers(options?.headers).get('X-CSRF-Token')).toBe('synthetic-token')
    expect(new Headers(options?.headers).get('Content-Type')).toBe('application/json')
  })

  it('normalizes RFC 9457 responses into ApiProblemError', async () => {
    const problem = {
      type: 'https://errors.lemoo.invalid/resource_not_found',
      title: 'Resource not found',
      status: 404,
      detail: 'The requested resource is unavailable.',
      instance: '/api/v1/devices/missing',
      code: 'resource_not_found',
      request_id: '0198f001-7000-7000-8000-000000000001',
    }
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        Promise.resolve(
          new Response(JSON.stringify(problem), {
            status: 404,
            headers: { 'Content-Type': 'application/problem+json' },
          }),
        ),
      ),
    )

    const request = apiFetch('/api/v1/devices/missing')

    await expect(request).rejects.toBeInstanceOf(ApiProblemError)
    await expect(request).rejects.toMatchObject({ problem })
  })
})
