export function rotationState(now, startedAt, intervalMs, count, position = 0) {
  if (!Number.isFinite(intervalMs) || intervalMs < 1000 || count < 1) return null
  const elapsed = Math.max(0, now - startedAt)
  const tick = position + Math.floor(elapsed / intervalMs)
  return { tick, index: ((tick % count) + count) % count, remainingMs: intervalMs - (elapsed % intervalMs), elapsedMs: elapsed }
}

export function createContentRuntime({ apiBase, siteId }) {
  const base = new URL(apiBase)
  if (base.protocol !== 'https:' && !(base.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(base.hostname))) throw new Error('Invalid content endpoint')
  const endpoint = base.origin
  let clock = null, pendingSession = null, destroyed = false
  const controllers = new Set()
  const now = () => clock ? clock.serverTime + performance.now() - clock.receivedAt : Date.now()
  function absorb(data) {
    if (!Number.isFinite(data.startedAt) || !Number.isFinite(data.serverTime) || !Number.isFinite(data.intervalMs)) throw new Error('Invalid session')
    if (clock?.sessionTag === data.sessionTag && (data.navigationVersion || 0) < (clock.navigationVersion || 0)) return false
    clock = { ...data, receivedAt: performance.now() }
    return true
  }
  async function request(path, options = {}) {
    const abort = new AbortController(), timeout = setTimeout(() => abort.abort(), 1500)
    try {
      const response = await fetch(endpoint + path, { ...options, credentials: 'include', signal: abort.signal, cache: 'no-store' })
      if (!response.ok) throw new Error(`Content request failed (${response.status})`)
      return await response.json()
    } finally { clearTimeout(timeout) }
  }
  function session() {
    if (!pendingSession) pendingSession = request('/public/v1/session', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ siteId, reason: 'bootstrap' }),
    }).then(data => { absorb(data); return data }).finally(() => { pendingSession = null })
    return pendingSession
  }
  const ready = session().catch(() => null)
  const heartbeat = setInterval(() => { if (!document.hidden) session().catch(() => {}) }, 60000)
  function getState() {
    if (!clock) return null
    return { ...clock, now: now() }
  }
  function attach(container, { slotId, layout = 'wide' }) {
    let stopped = false, control = null, refreshing = false, visible = false
    let presentation = '', imageSource = '', activeAsset = '', instanceId = '', viewed = false, viewTimer = null
    const failedImages = new Set(), reduceMotion = matchMedia('(prefers-reduced-motion: reduce)')
    let navigating = false, current = null
    container.classList.add('sc-slot')
    container.classList.toggle('sc-slot--side', layout === 'side')
    container.hidden = true
    const node = (tag, cls, text) => { const e = document.createElement(tag); e.className = cls; if (text) e.textContent = text; return e }
    const card = node('div', 'sc-card'), link = node('a', 'sc-link'), artwork = node('span', 'sc-artwork')
    const image = node('img', 'sc-image'), monogram = node('span', 'sc-monogram')
    image.alt = ''; image.hidden = true; image.width = 44; image.height = 44; artwork.append(image, monogram)
    const copy = node('span', 'sc-copy')
    const title = node('span', 'sc-title'), description = node('span', 'sc-description')
    const cta = node('span', 'sc-cta', '了解详情 ↗')
    const controls = node('div', 'sc-controls'), previous = node('button', 'sc-previous', '‹'), next = node('button', 'sc-next', '›')
    controls.setAttribute('role', 'group'); controls.setAttribute('aria-label', '素材切换')
    for (const [button, name] of [[previous, '上一条'], [next, '下一条']]) { button.type = 'button'; button.setAttribute('aria-label', name); button.title = name }
    const status = node('span', 'sc-status'); status.setAttribute('role', 'status')
    controls.append(previous, next)
    link.target = '_blank'; link.rel = 'noopener sponsored'; copy.append(title, description); link.append(artwork, copy, cta); card.append(link, controls, status); container.replaceChildren(card)
    function cancelView() { clearTimeout(viewTimer); viewTimer = null }
    function scheduleView() {
      if (viewed || viewTimer || !visible || document.hidden || container.hidden || !current) return
      const captured = instanceId
      viewTimer = setTimeout(() => {
        viewTimer = null
        if (stopped || !visible || document.hidden || container.hidden || instanceId !== captured) return
        viewed = true
        request('/public/v1/events', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ eventId: captured, creativeId: current.id, slotId }) }).catch(() => {})
      }, 1000)
    }
    function draw() {
      if (stopped) return
      if (!control || control.mode !== 'native_playlist' || now() >= control.validUntil || !control.playlist?.length) {
        container.hidden = true; cancelView(); return
      }
      const state = rotationState(now(), clock.rotationStartedAt ?? clock.startedAt, clock.intervalMs, control.playlist.length, clock.position || 0)
      if (!state) return
      const item = current && navigating ? current : control.playlist[state.index]
      if (!item || !/^[a-zA-Z0-9_-]+$/.test(item.id)) { container.hidden = true; return }
      container.hidden = false
      container.dataset.scSession = clock.sessionTag
      container.dataset.scStartedAt = String(clock.startedAt)
      container.dataset.scTick = String(state.tick)
      container.dataset.scRotationStartedAt = String(clock.rotationStartedAt ?? clock.startedAt)
      container.dataset.scPosition = String(clock.position || 0)
      container.dataset.scNavigationVersion = String(clock.navigationVersion || 0)
      container.dataset.scRevision = String(control.revision)
      previous.hidden = next.hidden = control.playlist.length < 2
      previous.disabled = next.disabled = navigating
      if (presentation !== JSON.stringify(item)) {
        cancelView(); current = item; presentation = JSON.stringify(item); instanceId = crypto.randomUUID(); viewed = false
        container.dataset.scCreative = item.id
        title.textContent = item.title; description.textContent = item.description
        link.href = `${endpoint}/c/${encodeURIComponent(item.id)}`
        monogram.textContent = item.title.slice(0, 1)
        if (/^#[0-9a-fA-F]{6}$/.test(item.accent)) card.style.setProperty('--sc-accent', item.accent)
        image.alt = [item.title, item.description].filter(Boolean).join('：')
        image.decoding = 'async'
        if (visible && !document.hidden && !reduceMotion.matches) {
          card.animate([{ opacity: 0.35 }, { opacity: 1 }], { duration: 200 })
        }
      }
      const source = matchMedia('(max-width: 767px)').matches ? item.imageMobile || item.image : layout === 'side' ? item.imageSide || item.image : item.image
      const hasImage = source && /^\/media\/[a-f0-9]{64}\.(png|gif)$/.test(source) && !failedImages.has(source)
      card.classList.toggle('sc-card--image', Boolean(hasImage))
      container.dataset.scFormat = hasImage ? 'image' : 'text'
      if (hasImage) {
        activeAsset = source
        const animated = source.endsWith('.gif')
        const still = animated && (reduceMotion.matches || document.hidden || !visible)
        const nextImage = endpoint + (still ? source.replace(/\.gif$/, '.png') : source)
        if (imageSource !== nextImage) { imageSource = nextImage; image.src = nextImage }
        image.hidden = false; monogram.hidden = true
      } else {
        activeAsset = ''; imageSource = ''; image.removeAttribute('src'); image.hidden = true; monogram.hidden = false
      }
      scheduleView()
    }
    image.addEventListener('error', () => { if (activeAsset) failedImages.add(activeAsset); draw() })
    async function navigate(direction) {
      if (stopped || navigating || !current || control?.playlist?.length < 2 || container.hidden) return
      navigating = true; previous.disabled = next.disabled = true; status.textContent = ''
      try {
        const data = await request('/public/v1/navigation', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ siteId, slotId, direction, creativeId: current.id, revision: control.revision }) })
        if (stopped) return
        if (absorb(data)) { control = data; current = null; presentation = '' }
      } catch {
        if (!stopped) { status.textContent = '切换失败，请稍后重试'; await refresh() }
      } finally { navigating = false; draw() }
    }
    previous.addEventListener('click', () => navigate('previous'))
    next.addEventListener('click', () => navigate('next'))
    controls.addEventListener('keydown', event => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); navigate(event.key === 'ArrowLeft' ? 'previous' : 'next') }
    })
    const observer = new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting && entries[0].intersectionRatio >= .5
      if (!visible) cancelView()
      draw()
    }, { threshold: [0, .5] })
    observer.observe(container)
    async function refresh() {
      if (stopped || document.hidden || refreshing) return
      refreshing = true
      try {
        if (slotId === 'blog.home.sidebar' && matchMedia('(max-width: 767px)').matches) { control = null; draw(); return }
        const device = matchMedia('(max-width: 767px)').matches ? 'mobile' : 'desktop'
        const data = await request(`/public/v1/control?${new URLSearchParams({ siteId, slotId, device })}`)
        if (stopped) return
        if (!absorb(data)) return
        control = data
        // Configuration updates and session resets must release references to removed creatives.
        if (current && (!control.playlist?.some(item => item.id === current.id) || container.dataset.scSession !== clock.sessionTag)) {
          current = null; presentation = ''
        }
        draw()
      } catch { draw() } finally { refreshing = false }
    }
    const poll = setInterval(refresh, 5000)
    const tick = setInterval(() => { if (!document.hidden) draw() }, 200)
    const media = matchMedia('(max-width: 767px)')
    const mediaChanged = () => refresh()
    media.addEventListener('change', mediaChanged)
    reduceMotion.addEventListener('change', draw)
    const controller = { refresh, draw, stop() { stopped = true; clearInterval(poll); clearInterval(tick); cancelView(); observer.disconnect(); media.removeEventListener('change', mediaChanged); reduceMotion.removeEventListener('change', draw); controllers.delete(controller); container.replaceChildren(); container.hidden = true } }
    controllers.add(controller); ready.then(refresh)
    return controller.stop
  }
  function visibility() {
    if (document.hidden) { controllers.forEach(c => c.draw()); return }
    session().catch(() => {}).finally(() => controllers.forEach(c => c.refresh()))
  }
  document.addEventListener('visibilitychange', visibility)
  window.addEventListener('pageshow', visibility)
  return { attach, getState, ready, refresh: () => session().then(() => Promise.all([...controllers].map(c => c.refresh()))), destroy() { if (destroyed) return; destroyed = true; clearInterval(heartbeat); document.removeEventListener('visibilitychange', visibility); window.removeEventListener('pageshow', visibility); [...controllers].forEach(c => c.stop()) } }
}
