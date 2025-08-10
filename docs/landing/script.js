// Fetch stars and forks from GitHub API and wire small UX actions
(async () => {
  const repo = 'autoscrape-labs/pydoll'
  const apiUrl = `https://api.github.com/repos/${repo}`

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

  try {
    const res = await fetch(apiUrl, { headers: { 'Accept': 'application/vnd.github+json' } })
    if (res.ok) {
      const data = await res.json()
      const stars = (data.stargazers_count ?? 0).toLocaleString('pt-BR')

      const starCount = document.getElementById('starCount')
      if (starCount) {
        starCount.textContent = `${stars}★`
      }
      // forks removidos da UI
    }
  } catch (_) {
    // noop: keep placeholders on failure
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

  // (CTA final não requer JS adicional)
})()


