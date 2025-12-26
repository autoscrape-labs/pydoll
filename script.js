// Fetch stars and forks from GitHub API and wire small UX actions
(async () => {
  const repo = 'autoscrape-labs/pydoll'
  const apiUrl = `https://api.github.com/repos/${repo}`
  let repoStarsCount = 0

  // Simple localStorage cache with TTL
  const cacheGet = (key, maxAgeMs) => {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) return null
      const parsed = JSON.parse(raw)
      if (!parsed || typeof parsed !== 'object') return null
      if (typeof parsed.t !== 'number') return null
      const now = Date.now()
      if (now - parsed.t > maxAgeMs) return null
      return parsed.v
    } catch (_) {
      return null
    }
  }
  const cacheSet = (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify({ t: Date.now(), v: value }))
    } catch (_) {}
  }
  const TTL = 5 * 60 * 1000 // 5 minutes

  // Cursor glow effect (subtle follow)
  const glow = document.getElementById('cursorGlow')
  const hero = document.getElementById('hero')
  if (glow && hero) {
    let raf = 0
    let targetX = 0
    let targetY = 0
    let currentX = 0
    let currentY = 0

    const getHeroRect = () => hero.getBoundingClientRect()

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    const move = (e) => {
      const r = getHeroRect()
      // Coordenadas relativas à seção do herói
      targetX = e.clientX - r.left - glow.offsetWidth / 2
      targetY = e.clientY - r.top - glow.offsetHeight / 2
      if (!raf && !reduceMotion) raf = requestAnimationFrame(tick)
    }
    const tick = () => {
      const lerp = (a, b, t) => a + (b - a) * t
      currentX = lerp(currentX, targetX, 0.18)
      currentY = lerp(currentY, targetY, 0.18)
      glow.style.transform = `translate(${currentX}px, ${currentY}px)`
      raf = (Math.abs(currentX - targetX) + Math.abs(currentY - targetY) > 0.5) ? requestAnimationFrame(tick) : (raf = 0)
    }
    hero.addEventListener('mousemove', move, { passive: true })
  }

  // Stars, goal progress and latest stargazers
  try {
    const cacheKey = `gh:repo:${repo}`
    let data = cacheGet(cacheKey, TTL)
    if (!data) {
      const res = await fetch(apiUrl, { headers: { 'Accept': 'application/vnd.github+json' } })
      if (res.ok) {
        data = await res.json()
        cacheSet(cacheKey, data)
      }
    }
    if (data) {
      const starsCount = Number(data.stargazers_count ?? 0)
      repoStarsCount = starsCount
      const starsFmt = starsCount.toLocaleString('pt-BR')

      const starCount = document.getElementById('starCount')
      if (starCount) starCount.textContent = `${starsFmt}`

      // Update progress bar to 10k
      const GOAL = 10000
      const pct = Math.max(0, Math.min(100, Math.round((starsCount / GOAL) * 100)))
      const bar = document.getElementById('starsProgressBar')
      const label = document.getElementById('starsProgressLabel')
      const pctLabel = document.getElementById('starsProgressPct')
      if (bar) bar.style.width = `${pct}%`
      if (label) label.textContent = `${starsFmt} / ${GOAL.toLocaleString('pt-BR')}`
      if (pctLabel) pctLabel.textContent = `${pct}%`
    }
  } catch (_) {
    // noop: keep placeholders on failure
  }

  // Fetch latest stargazers (last 10, newest first, fill from previous page if needed)
  try {
    const perPage = 10
    const lastPage = Math.max(1, Math.ceil((repoStarsCount || 1) / perPage))

    const fetchPage = async (page) => {
      const cacheKey = `gh:stargazers:${repo}:p${page}:pp${perPage}`
      let payload = cacheGet(cacheKey, TTL)
      if (!payload) {
        const res = await fetch(`https://api.github.com/repos/${repo}/stargazers?per_page=${perPage}&page=${page}`, {
          headers: { 'Accept': 'application/vnd.github.v3.star+json' }
        })
        if (!res.ok) return []
        payload = await res.json()
        cacheSet(cacheKey, payload)
      }
      if (!Array.isArray(payload)) return []
      if (payload.length && (payload[0]?.user || payload[0]?.starred_at)) {
        return payload
          .map((it) => ({
            login: it?.user?.login,
            avatar_url: it?.user?.avatar_url,
            html_url: it?.user?.html_url || (it?.user?.login ? `https://github.com/${it.user.login}` : '#'),
            starred_at: it?.starred_at ? Date.parse(it.starred_at) : 0
          }))
          .filter((u) => u.login)
      }
      // Fallback if server ignores star+json
      return payload.map((u) => ({
        login: u.login,
        avatar_url: u.avatar_url,
        html_url: u.html_url || (u.login ? `https://github.com/${u.login}` : '#'),
        starred_at: 0
      }))
    }

    let entries = await fetchPage(lastPage)
    if (entries.length < perPage && lastPage > 1) {
      const prev = await fetchPage(lastPage - 1)
      entries = entries.concat(prev)
    }

    // Sort newest first and cap to perPage
    entries.sort((a, b) => b.starred_at - a.starred_at)
    entries = entries.slice(0, perPage)

    // Render
    const list = document.getElementById('stargazersList')
    if (list) {
      entries.forEach((u) => {
        const li = document.createElement('li')
        li.className = 'flex items-center gap-2'
        const a = document.createElement('a')
        a.href = u.html_url
        a.target = '_blank'
        a.rel = 'noopener'
        a.className = 'group inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-800/60 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800'
        const img = document.createElement('img')
        img.src = u.avatar_url
        img.alt = u.login
        img.width = 22
        img.height = 22
        img.loading = 'lazy'
        img.decoding = 'async'
        img.className = 'h-[22px] w-[22px] rounded-full ring-1 ring-white/10'
        const span = document.createElement('span')
        span.textContent = u.login
        a.appendChild(img)
        a.appendChild(span)
        li.appendChild(a)
        list.appendChild(li)
      })
    }
  } catch (_) {
    // ignore
  }

  // Copy install command
  const copyBtn = document.getElementById('copyBtn')
  const installCmd = document.getElementById('installCmd')
  if (copyBtn && installCmd) {
    copyBtn.addEventListener('click', async () => {
      try {
        const text = installCmd.textContent ?? ''
        await navigator.clipboard.writeText(text)
        const old = copyBtn.textContent
        copyBtn.textContent = 'Copiado!'
        setTimeout(() => (copyBtn.textContent = old), 1200)
      } catch (_) {
        // ignore
      }
    })
  }

  // Reveal on scroll
  const revealEls = Array.from(document.querySelectorAll('.reveal'))
  if (revealEls.length) {
    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed')
          io.unobserve(entry.target)
        }
      }
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 })
    revealEls.forEach((el) => io.observe(el))
  }

  // Tilt cards
  const tiltCards = Array.from(document.querySelectorAll('.tilt-card'))
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  tiltCards.forEach((card) => {
    const bounds = () => card.getBoundingClientRect()
    let frame = 0
    const onMove = (e) => {
      const r = bounds()
      const px = (e.clientX - r.left) / r.width
      const py = (e.clientY - r.top) / r.height
      const rotY = (px - 0.5) * 10
      const rotX = (0.5 - py) * 8
      const tx = (px - 0.5) * 8
      const ty = (py - 0.5) * 8
      if (prefersReduced) return
      if (!frame) frame = requestAnimationFrame(() => {
        card.style.transform = `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translate3d(${tx.toFixed(2)}px, ${ty.toFixed(2)}px, 0)`
        frame = 0
      })
    }
    const onLeave = () => {
      card.style.transform = 'perspective(1000px)'
    }
    card.addEventListener('mousemove', onMove)
    card.addEventListener('mouseleave', onLeave)
  })

  // Modal: Automação concorrente
  const openModalBtn = document.getElementById('openConcurrentModal')
  const closeModalBtn = document.getElementById('closeConcurrentModal')
  const modal = document.getElementById('concurrentModal')
  const copyConcurrentCodeBtn = document.getElementById('copyConcurrentCode')
  const concurrentCodeBlock = document.getElementById('concurrentCodeBlock')
  const toggleModal = (show) => {
    if (!modal) return
    modal.classList.toggle('hidden', !show)
    modal.classList.toggle('flex', show)
  }
  if (openModalBtn && modal) openModalBtn.addEventListener('click', () => toggleModal(true))
  if (closeModalBtn && modal) closeModalBtn.addEventListener('click', () => toggleModal(false))
  if (modal) {
    modal.addEventListener('click', (e) => { if (e.target === modal) toggleModal(false) })
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') toggleModal(false) })
  }

  // Copy concurrent code
  if (copyConcurrentCodeBtn && concurrentCodeBlock) {
    copyConcurrentCodeBtn.addEventListener('click', async () => {
      try {
        const text = concurrentCodeBlock.innerText || concurrentCodeBlock.textContent || ''
        await navigator.clipboard.writeText(text)
        const old = copyConcurrentCodeBtn.textContent
        copyConcurrentCodeBtn.textContent = 'Copiado!'
        setTimeout(() => (copyConcurrentCodeBtn.textContent = old), 1000)
      } catch (_) {}
    })
  }

  // (removido: bloco redundante de cópia de preferências)

  // Copy buttons for vertical cards
  const bindCopy = (btnId, codeElId) => {
    const btn = document.getElementById(btnId)
    const codeEl = document.getElementById(codeElId)
    if (!btn || !codeEl) return
    btn.addEventListener('click', async () => {
      try {
        const text = codeEl.innerText || codeEl.textContent || ''
        await navigator.clipboard.writeText(text)
        const old = btn.textContent
        btn.textContent = 'Copiado!'
        setTimeout(() => (btn.textContent = old), 1000)
      } catch (_) {}
    })
  }
  bindCopy('copyConcurrentBtn', 'codeConcurrent')
  bindCopy('copyRequestsBtn', 'codeRequests')
  bindCopy('copyPrefsBtn', 'codePrefs')

  // Mobile menu toggle
  const mobileMenuButton = document.getElementById('mobileMenuButton')
  const mobileMenu = document.getElementById('mobileMenu')
  const iconMenu = document.getElementById('iconMenu')
  const iconClose = document.getElementById('iconClose')
  if (mobileMenuButton && mobileMenu && iconMenu && iconClose) {
    const setExpanded = (expanded) => {
      mobileMenuButton.setAttribute('aria-expanded', String(expanded))
      mobileMenu.classList.toggle('hidden', !expanded)
      iconMenu.classList.toggle('hidden', expanded)
      iconClose.classList.toggle('hidden', !expanded)
    }
    mobileMenuButton.addEventListener('click', () => {
      const isOpen = mobileMenuButton.getAttribute('aria-expanded') === 'true'
      setExpanded(!isOpen)
    })
    // Close on escape and when clicking links
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') setExpanded(false)
    })
    mobileMenu.addEventListener('click', (e) => {
      const target = e.target
      if (target instanceof HTMLElement && target.tagName === 'A') setExpanded(false)
    })
  }

  // (CTA final não requer JS adicional)

  // Feature cards -> modals
  const modalMap = [
    { card: 'cardZeroConfig', modal: 'modalZeroConfig', close: 'closeZeroConfigModal' },
    { card: 'cardAsync', modal: 'modalAsync', close: 'closeAsyncModal' },
    { card: 'cardTypeSafety', modal: 'modalTypeSafety', close: 'closeTypeSafetyModal' },
    { card: 'cardRequests', modal: 'modalRequests', close: 'closeRequestsModal' },
    { card: 'cardIntuitive', modal: 'modalIntuitive', close: 'closeIntuitiveModal' },
    { card: 'cardEvents', modal: 'modalEvents', close: 'closeEventsModal' },
  ]

  const toggleGenericModal = (el, show) => {
    if (!el) return
    el.classList.toggle('hidden', !show)
    el.classList.toggle('flex', show)
  }

  modalMap.forEach(({ card, modal, close }) => {
    const cardEl = document.getElementById(card)
    const modalEl = document.getElementById(modal)
    const closeEl = document.getElementById(close)

    if (cardEl && modalEl) cardEl.addEventListener('click', () => toggleGenericModal(modalEl, true))
    if (closeEl && modalEl) closeEl.addEventListener('click', () => toggleGenericModal(modalEl, false))
    if (modalEl) {
      modalEl.addEventListener('click', (e) => { if (e.target === modalEl) toggleGenericModal(modalEl, false) })
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape') toggleGenericModal(modalEl, false) })
    }
  })
})()


// You can add more sponsors by pushing new objects to this array
const SPONSORS = [
  {
    name: 'Thordata',
    url: 'https://www.thordata.com/?ls=github&lk=pydoll',
    logo: '/images/Thordata-logo.png',
    width: 200,
    height: 45
  },
  {
    name: 'LambdaTest',
    url: 'https://www.lambdatest.com/?utm_source=pydoll&utm_medium=sponsor',
    logo: 'https://www.lambdatest.com/blue-logo.png',
    width: 200,
    height: 45
  },
  {
    name: 'CapSolver',
    url: 'https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc',
    logo: '/images/capsolver-logo.png',
    width: 150
  }
]

function renderSponsors(gridId = 'sponsorsGrid') {
  const grid = document.getElementById(gridId)
  if (!grid || !Array.isArray(SPONSORS)) return

  const frag = document.createDocumentFragment()
  for (const s of SPONSORS) {
    const li = document.createElement('li')
    li.className = 'flex items-center justify-center'

    const a = document.createElement('a')
    a.href = s.url
    a.target = '_blank'
    a.rel = 'noopener nofollow sponsored'
    a.className = 'group block w-full rounded-lg bg-slate-900/40 px-4 py-3 hover:bg-white/5 transition-colors'

    const img = document.createElement('img')
    img.src = s.logo
    img.alt = s.name
    img.loading = 'lazy'
    img.decoding = 'async'
    img.width = s.width || 200
    img.height = s.height || 40
    img.className = 'mx-auto max-h-10'

    a.appendChild(img)
    li.appendChild(a)
    frag.appendChild(li)
  }
  grid.innerHTML = ''
  grid.appendChild(frag)
}

document.addEventListener('DOMContentLoaded', () => {
  renderSponsors()
})

