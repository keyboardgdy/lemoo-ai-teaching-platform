export interface ProblemDetail {
  type: string
  title: string
  status: number
  detail: string
  instance: string
  code: string
  request_id: string
}

export class ApiProblemError extends Error {
  readonly problem: ProblemDetail

  constructor(problem: ProblemDetail) {
    super(problem.detail)
    this.name = 'ApiProblemError'
    this.problem = problem
  }
}

function cookie(name: string): string | undefined {
  if (typeof document === 'undefined') return undefined
  const prefix = `${encodeURIComponent(name)}=`
  const item = document.cookie.split('; ').find((value) => value.startsWith(prefix))
  return item ? decodeURIComponent(item.slice(prefix.length)) : undefined
}

function isProblem(value: unknown): value is ProblemDetail {
  if (typeof value !== 'object' || value === null) return false
  const candidate = value as Partial<ProblemDetail>
  return (
    typeof candidate.type === 'string' &&
    typeof candidate.title === 'string' &&
    typeof candidate.status === 'number' &&
    typeof candidate.detail === 'string' &&
    typeof candidate.code === 'string' &&
    typeof candidate.request_id === 'string'
  )
}

export async function apiFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = cookie('lemoo_csrf')
    if (csrf) headers.set('X-CSRF-Token', csrf)
  }

  const response = await fetch(url, {
    ...options,
    method,
    headers,
    credentials: 'include',
  })
  const hasBody = response.status !== 204 && response.headers.get('content-length') !== '0'
  const payload: unknown = hasBody ? await response.json() : undefined
  if (!response.ok) {
    if (isProblem(payload)) throw new ApiProblemError(payload)
    throw new ApiProblemError({
      type: 'https://errors.lemoo.invalid/unexpected_response',
      title: 'Unexpected response',
      status: response.status,
      detail: 'The API returned an unexpected error response.',
      instance: new URL(url, globalThis.location?.origin ?? 'http://localhost').pathname,
      code: 'unexpected_response',
      request_id: response.headers.get('x-request-id') ?? 'unknown',
    })
  }
  return payload as T
}
