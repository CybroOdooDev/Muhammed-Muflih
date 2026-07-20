(() => {
  'use strict';

  /* ============ UTILITIES ============ */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
  const isEditMode = () => document.body.classList.contains('editor_enable');

  /* ============ SCROLL PROGRESS + HEADER STATE ============ */
  const scrollProgress = $('#scrollProgress');
  const siteHeader = $('#siteHeader');
  const backToTop = $('#backToTop');

  function onScroll() {
    if (isEditMode()) return;
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    if (scrollProgress) scrollProgress.style.width = `${progress}%`;

    if (scrollTop > 60) {
      siteHeader?.classList.add('scrolled');
    } else {
      siteHeader?.classList.remove('scrolled');
    }

    if (scrollTop > 500) {
      backToTop?.classList.add('show');
    } else {
      backToTop?.classList.remove('show');
    }
  }
  document.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  backToTop?.addEventListener('click', () => {
    if (isEditMode()) return;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  /* ============ MOBILE MENU ============ */
  const hamburger = $('#hamburger');
  const mobileMenu = $('#mobileMenu');
  const mobileMenuClose = $('#mobileMenuClose');

  function closeMobileMenu() {
    hamburger?.classList.remove('active');
    hamburger?.setAttribute('aria-expanded', 'false');
    mobileMenu?.classList.remove('active');
  }

  hamburger?.addEventListener('click', () => {
    if (isEditMode()) return;
    const isActive = hamburger.classList.toggle('active');
    hamburger.setAttribute('aria-expanded', String(isActive));
    mobileMenu?.classList.toggle('active', isActive);
  });

  mobileMenuClose?.addEventListener('click', closeMobileMenu);
  $$('.mobile-menu a').forEach((link) => link.addEventListener('click', closeMobileMenu));

  /* ============ SEARCH OVERLAY ============ */
  const searchToggle = $('#searchToggle');
  const searchOverlay = $('#searchOverlay');
  const searchClose = $('#searchClose');
  const searchInput = $('#searchInput');

  function openSearch() {
    if (isEditMode()) return;
    searchOverlay?.classList.add('active');
    searchToggle?.setAttribute('aria-expanded', 'true');
    setTimeout(() => searchInput?.focus(), 300);
  }
  function closeSearch() {
    searchOverlay?.classList.remove('active');
    searchToggle?.setAttribute('aria-expanded', 'false');
  }

  searchToggle?.addEventListener('click', openSearch);
  searchClose?.addEventListener('click', closeSearch);
  searchOverlay?.addEventListener('click', (e) => {
    if (e.target === searchOverlay) closeSearch();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSearch();
      closeMobileMenu();
      closeCart();
    }
  });

  /* ============ TOAST ============ */
  const toast = $('#toast');
  let toastTimer = null;
  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
  }

  /* ============ CART DRAWER (backed by the real Odoo cart) ============ */
  const cartToggle = $('#cartToggle');
  const cartToggleMobile = $('#cartToggleMobile');
  const cartDrawer = $('#cartDrawer');
  const cartClose = $('#cartClose');
  const drawerBackdrop = $('#drawerBackdrop');
  const cartItemsEl = $('#cartItems');
  const cartTotalEl = $('#cartTotalWrap');

  async function jsonRpc(route, params = {}) {
    const response = await fetch(route, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params, id: Math.floor(performance.now()) }),
    });
    const payload = await response.json();
    if (payload.error) {
      throw new Error(payload.error.data?.message || 'Request failed');
    }
    return payload.result;
  }

  function updateCartBadges(quantity) {
    $$('.js-cart-count').forEach((el) => (el.textContent = String(quantity || 0)));
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  function bindCouponFormEvents() {
    if (!cartTotalEl) return;
    $$('.a-submit', cartTotalEl).forEach((link) => {
      link.addEventListener('click', (e) => {
        if (isEditMode()) return;
        e.preventDefault();
        link.closest('form')?.submit();
      });
    });
  }

  function renderCartLines(lines, currencySymbol) {
    if (!cartItemsEl) return;

    if (!lines.length) {
      cartItemsEl.innerHTML = '<p class="empty-state">Your bag is empty. Discover a scent worth carrying.</p>';
      return;
    }

    cartItemsEl.innerHTML = lines
      .map(
        (line) => `
      <div class="cart-item">
        <img src="${line.image_url}" alt="${escapeHtml(line.name)}" loading="lazy">
        <div class="cart-item-info">
          <h4>${escapeHtml(line.name)}</h4>
          <span>${currencySymbol}${line.price.toFixed(2)} &times; ${line.qty}</span>
        </div>
        <div class="cart-item-controls">
          <button class="qty-decrease" aria-label="Decrease quantity" data-product-id="${line.product_id}" data-line-id="${line.line_id}" data-qty="${line.qty}">&minus;</button>
          <span>${line.qty}</span>
          <button class="qty-increase" aria-label="Increase quantity" data-product-id="${line.product_id}" data-line-id="${line.line_id}" data-qty="${line.qty}">+</button>
          <button class="cart-item-remove" aria-label="Remove item" data-product-id="${line.product_id}" data-line-id="${line.line_id}"><i class="fa-solid fa-trash"></i></button>
        </div>
      </div>`
      )
      .join('');

    $$('.qty-decrease', cartItemsEl).forEach((btn) =>
      btn.addEventListener('click', () => {
        if (isEditMode()) return;
        changeCartLine(btn.dataset.productId, btn.dataset.lineId, Math.max(parseInt(btn.dataset.qty, 10) - 1, 0));
      })
    );
    $$('.qty-increase', cartItemsEl).forEach((btn) =>
      btn.addEventListener('click', () => {
        if (isEditMode()) return;
        changeCartLine(btn.dataset.productId, btn.dataset.lineId, parseInt(btn.dataset.qty, 10) + 1);
      })
    );
    $$('.cart-item-remove', cartItemsEl).forEach((btn) =>
      btn.addEventListener('click', () => {
        if (isEditMode()) return;
        changeCartLine(btn.dataset.productId, btn.dataset.lineId, 0);
      })
    );
  }

  function applyCartData(data) {
    if (!data) return;
    if (Array.isArray(data.lines)) {
      renderCartLines(data.lines, data.currency_symbol || '$');
    }
    if (cartTotalEl && data['website_sale.total'] !== undefined) {
      cartTotalEl.innerHTML = data['website_sale.total'];
      bindCouponFormEvents();
    }
    updateCartBadges(data.cart_quantity);
  }

  async function changeCartLine(productId, lineId, qty) {
    try {
      await jsonRpc('/shop/cart/update_json', {
        product_id: parseInt(productId, 10),
        line_id: lineId ? parseInt(lineId, 10) : false,
        set_qty: qty,
        display: true,
      });
      await loadCartDrawer();
    } catch (err) {
      showToast('Could not update your bag. Please try again.');
    }
  }

  async function loadCartDrawer() {
    if (!cartItemsEl) return;
    try {
      const data = await jsonRpc('/theme_velora/cart_drawer');
      applyCartData(data);
    } catch (err) {
      cartItemsEl.innerHTML = '<p class="empty-state">Your bag is empty. Discover a scent worth carrying.</p>';
    }
  }

  function openCart() {
    cartDrawer?.classList.add('active');
    drawerBackdrop?.classList.add('active');
    cartDrawer?.setAttribute('aria-hidden', 'false');
    loadCartDrawer();
  }
  function closeCart() {
    cartDrawer?.classList.remove('active');
    drawerBackdrop?.classList.remove('active');
    cartDrawer?.setAttribute('aria-hidden', 'true');
  }
  cartToggle?.addEventListener('click', (e) => {
    if (isEditMode()) return;
    e.preventDefault();
    openCart();
  });
  cartToggleMobile?.addEventListener('click', (e) => {
    if (isEditMode()) return;
    e.preventDefault();
    closeMobileMenu();
    openCart();
  });
  cartClose?.addEventListener('click', closeCart);
  drawerBackdrop?.addEventListener('click', closeCart);

  const wishlistToggleMobile = $('#wishlistToggleMobile');
  wishlistToggleMobile?.addEventListener('click', () => {
    if (isEditMode()) return;
    closeMobileMenu();
  });

  /* ============ CATEGORY QUICK-FILTER ============ */
  $$('.category-card').forEach((card) => {
    card.addEventListener('click', () => {
      if (isEditMode()) return;
      const note = card.dataset.note;
      showToast(`Exploring ${note} fragrances`);
      $('#velora_bestsellers')?.scrollIntoView({ behavior: 'smooth' });
    });
  });

  /* ============ WISHLIST (Homepage & Bestsellers Product Cards) ============ */
  /**
   * Retrieve wishlist product IDs from sessionStorage (same cache Odoo uses).
   */
  function getWishlistIds() {
    try {
      return JSON.parse(sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]');
    } catch {
      return [];
    }
  }

  function setWishlistIds(ids) {
    sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(ids));
  }

  /**
   * Update every wishlist count badge + show/hide the header heart icon.
   */
  function updateWishCountBadge(count) {
    const n = typeof count === 'number' ? count : count.length;
    // Update all badge spans
    $$('.js-wishlist-count, .my_wish_quantity').forEach((el) => {
      el.textContent = String(n);
    });
    // Show/hide the header wishlist anchor (hidden by d-none when count=0)
    $$('.o_wsale_my_wish_hide_empty').forEach((el) => {
      el.classList.toggle('d-none', n === 0);
    });
  }

  /**
   * Mark a wishlist button as "already in wishlist" (red solid heart).
   */
  function markWishlistBtn(btn, inWish) {
    const icon = btn.querySelector('i');
    if (inWish) {
      btn.classList.add('vc-in-wish', 'active');
      btn.setAttribute('disabled', 'disabled');
      if (icon) {
        icon.classList.remove('fa-regular');
        icon.classList.add('fa-solid');
      }
    } else {
      btn.classList.remove('vc-in-wish', 'active');
      btn.removeAttribute('disabled');
      if (icon) {
        icon.classList.add('fa-regular');
        icon.classList.remove('fa-solid');
      }
    }
  }

  /**
   * On page load, pre-mark cards whose products are already in the wishlist.
   * Also sync the header badge from the rendered server count.
   */
  function initWishlistBtns() {
    const ids = getWishlistIds();
    $$('.wishlist-btn[data-product-product-id]').forEach((btn) => {
      const pid = parseInt(btn.dataset.productProductId, 10);
      if (ids.includes(pid)) markWishlistBtn(btn, true);
    });
    // Sync header badge visibility from rendered server count on page load
    const serverCount = parseInt(
      document.querySelector('.my_wish_quantity')?.textContent?.trim() || '0', 10
    );
    if (!isNaN(serverCount)) updateWishCountBadge(serverCount);
  }

  /**
   * Handle wishlist button clicks on custom product cards.
   * Skips buttons that have Odoo's o_add_wishlist class (handled by Odoo's own widget).
   */
  document.addEventListener('click', async (e) => {
    if (isEditMode()) return;
    // Only handle our custom wishlist-btn (exclude Odoo shop page native buttons)
    const btn = e.target.closest('.wishlist-btn[data-product-product-id]:not(.o_add_wishlist)');
    if (!btn) return;

    // Already in wishlist — button is disabled
    if (btn.hasAttribute('disabled')) return;

    e.preventDefault();
    e.stopPropagation();

    const productId = parseInt(btn.dataset.productProductId, 10);
    if (!productId) return;

    const ids = getWishlistIds();
    if (ids.includes(productId)) return;

    // Optimistic UI: turn heart red immediately
    markWishlistBtn(btn, true);
    const newIds = [...ids, productId];
    setWishlistIds(newIds);
    updateWishCountBadge(newIds.length);

    try {
      await jsonRpc('/shop/wishlist/add', { product_id: productId });
      showToast('Added to wishlist \u2665');
    } catch (err) {
      // Rollback on error
      markWishlistBtn(btn, false);
      const rolled = ids.filter((id) => id !== productId);
      setWishlistIds(rolled);
      updateWishCountBadge(rolled.length);
      showToast('Could not add to wishlist. Please try again.');
    }
  });

  // Seed initial state from session cache
  initWishlistBtns();

  /* ============ SCROLL REVEAL (Intersection Observer) ============ */
  const revealItems = $$('.reveal');
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -50px 0px' }
  );
  revealItems.forEach((item) => revealObserver.observe(item));

  /* ============ COUNT-UP STATISTICS ============ */
  const statNumbers = $$('.stat-number');
  const statObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          statObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.5 }
  );
  statNumbers.forEach((el) => statObserver.observe(el));

  function animateCount(el) {
    const target = parseInt(el.dataset.count, 10);
    const duration = 1800;
    const startTime = performance.now();

    function tick(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.floor(eased * target);
      el.textContent = value.toLocaleString();
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = target.toLocaleString();
      }
    }
    requestAnimationFrame(tick);
  }

  /* ============ TESTIMONIAL CAROUSEL DOTS + AUTOPLAY ============ */
  const testimonialTrack = $('#testimonialTrack');
  const testimonialDots = $('#testimonialDots');
  const testimonialWrap = $('.testimonial-track-wrap');

  if (testimonialTrack && testimonialDots) {
    const cards = $$('.testimonial-card', testimonialTrack);
    let activeIndex = 0;

    function goToTestimonial(index) {
      if (isEditMode()) return;
      const target = (index + cards.length) % cards.length;
      const card = cards[target];
      const trackRect = testimonialTrack.getBoundingClientRect();
      const cardRect = card.getBoundingClientRect();
      const scrollLeft = testimonialTrack.scrollLeft + (cardRect.left - trackRect.left);
      testimonialTrack.scrollTo({ left: scrollLeft, behavior: 'smooth' });
    }

    cards.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.setAttribute('aria-label', `Go to testimonial ${i + 1}`);
      if (i === 0) dot.classList.add('active');
      dot.addEventListener('click', () => {
        if (isEditMode()) return;
        goToTestimonial(i);
      });
      testimonialDots.appendChild(dot);
    });

    const dotEls = $$('button', testimonialDots);
    const dotObserverOptions = { root: testimonialTrack, threshold: 0.6 };
    const dotObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        const index = cards.indexOf(entry.target);
        if (entry.isIntersecting && index > -1) {
          activeIndex = index;
          dotEls.forEach((d) => d.classList.remove('active'));
          dotEls[index]?.classList.add('active');
        }
      });
    }, dotObserverOptions);
    cards.forEach((card) => dotObserver.observe(card));

    const prefersReducedMotionTestimonials = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const AUTOPLAY_DELAY = 5000;
    let autoplayTimer = null;

    function startAutoplay() {
      if (isEditMode() || prefersReducedMotionTestimonials) return;
      stopAutoplay();
      autoplayTimer = setInterval(() => goToTestimonial(activeIndex + 1), AUTOPLAY_DELAY);
    }
    function stopAutoplay() {
      clearInterval(autoplayTimer);
    }

    (testimonialWrap || testimonialTrack).addEventListener('mouseenter', stopAutoplay);
    (testimonialWrap || testimonialTrack).addEventListener('mouseleave', startAutoplay);
    testimonialTrack.addEventListener('focusin', stopAutoplay);
    testimonialTrack.addEventListener('focusout', startAutoplay);
    testimonialTrack.addEventListener('touchstart', stopAutoplay, { passive: true });
    testimonialTrack.addEventListener('touchend', startAutoplay, { passive: true });
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stopAutoplay();
      else startAutoplay();
    });

    const sectionVisibilityObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) startAutoplay();
          else stopAutoplay();
        });
      },
      { threshold: 0.4 }
    );
    sectionVisibilityObserver.observe(testimonialWrap || testimonialTrack);

    function updateEdgeFades() {
      if (!testimonialWrap) return;
      const maxScroll = testimonialTrack.scrollWidth - testimonialTrack.clientWidth;
      testimonialWrap.classList.toggle('show-left-fade', testimonialTrack.scrollLeft > 8);
      testimonialWrap.classList.toggle('show-right-fade', testimonialTrack.scrollLeft < maxScroll - 8);
    }
    testimonialTrack.addEventListener('scroll', updateEdgeFades, { passive: true });
    window.addEventListener('resize', updateEdgeFades);
    updateEdgeFades();
  }

  /* ============ FAQ ACCORDION ============ */
  $$('.accordion-header').forEach((header) => {
    header.addEventListener('click', () => {
      if (isEditMode()) return;
      const panel = header.nextElementSibling;
      const isOpen = header.getAttribute('aria-expanded') === 'true';

      $$('.accordion-header').forEach((h) => {
        h.setAttribute('aria-expanded', 'false');
        h.nextElementSibling.style.maxHeight = null;
        h.nextElementSibling.style.paddingBottom = '0';
      });

      if (!isOpen) {
        header.setAttribute('aria-expanded', 'true');
        panel.style.maxHeight = `${panel.scrollHeight}px`;
      }
    });
  });

  /* ============ NEWSLETTER FORM ============ */
  const newsletterForm = $('#newsletterForm');
  const formMessage = $('#formMessage');

  newsletterForm?.addEventListener('submit', (e) => {
    if (isEditMode()) return;
    e.preventDefault();
    const emailInput = $('#newsletterEmail');
    const email = emailInput.value.trim();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email)) {
      formMessage.textContent = 'Please enter a valid email address.';
      formMessage.style.color = '#e07a7a';
      return;
    }

    formMessage.textContent = `Thank you! ${email} has joined the Velora Circle.`;
    formMessage.style.color = '';
    newsletterForm.reset();
    showToast('Subscribed successfully');
  });

  /* ============ CONTACT FORM ============ */
  const contactForm = $('#contactForm');
  const contactFormMessage = $('#contactFormMessage');

  contactForm?.addEventListener('submit', (e) => {
    if (isEditMode()) return;
    e.preventDefault();
    const name = $('#contactName').value.trim();
    const email = $('#contactEmail').value.trim();
    const subject = $('#contactSubject').value.trim();
    const message = $('#contactMessage').value.trim();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!name || !subject || !message || !emailPattern.test(email)) {
      contactFormMessage.textContent = 'Please fill in every field with a valid email address.';
      contactFormMessage.style.color = '#e07a7a';
      return;
    }

    contactFormMessage.textContent = `Thank you, ${name}. Our concierge team will reply to ${email} shortly.`;
    contactFormMessage.style.color = '';
    contactForm.reset();
    showToast('Message sent successfully');
  });

  /* ============ AJAX ADD TO CART ============ */
  document.addEventListener('submit', async (e) => {
    if (isEditMode()) return;
    const form = e.target.closest('form[action="/shop/cart/update"]');
    if (!form) return;
    const btn = form.querySelector('.add-cart-btn');
    if (!btn) return;

    e.preventDefault();

    const productId = parseInt(form.querySelector('[name="product_id"]')?.value, 10);
    const addQty = parseFloat(form.querySelector('[name="add_qty"]')?.value || '1');
    if (!productId) return;

    // visual feedback — disable button while adding
    btn.disabled = true;
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

    try {
      const data = await jsonRpc('/shop/cart/update_json', {
        product_id: productId,
        add_qty: addQty,
        display: true,
      });
      applyCartData(data);
      showToast('Added to your bag ✓');
      openCart();
    } catch (err) {
      showToast('Could not add to bag. Please try again.');
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  });

  /* ============ AJAX ADD TO CART (STANDALONE BUTTONS) ============ */
  document.addEventListener('click', async (e) => {
    if (isEditMode()) return;
    const btn = e.target.closest('.add-cart-btn');
    if (!btn || btn.closest('form')) return;

    e.preventDefault();
    if (btn.disabled) return;

    const productId = parseInt(btn.dataset.productId, 10);
    if (!productId) return;

    btn.disabled = true;
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

    try {
      const data = await jsonRpc('/shop/cart/update_json', {
        product_id: productId,
        add_qty: 1,
        display: true,
      });
      applyCartData(data);
      showToast('Added to your bag ✓');
      openCart();
    } catch (err) {
      showToast('Could not add to bag. Please try again.');
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  });

  /* ============ BUTTON RIPPLE EFFECT ============ */
  $$('.btn').forEach((btn) => {
    btn.addEventListener('click', function (e) {
      if (isEditMode()) return;
      const rect = btn.getBoundingClientRect();
      const ripple = document.createElement('div');
      const size = Math.max(rect.width, rect.height);
      ripple.className = 'ripple';
      ripple.style.width = ripple.style.height = `${size}px`;
      ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
      ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  /* ============ FOOTER YEAR ============ */
  const yearEl = $('#year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ============ WISHLIST TOAST ============ */
  document.addEventListener('click', (e) => {
    if (isEditMode()) return;
    const btn = e.target.closest('.o_add_wishlist');
    if (btn && !btn.disabled) {
      showToast('Added to wishlist ✓');
    }
  });

  /* ============ DYNAMIC COLLECTIONS REDIRECT ============ */
  document.addEventListener('click', (e) => {
    if (isEditMode()) return;
    const link = e.target.closest('a');
    if (!link) return;

    const href = link.getAttribute('href');
    if (href && href.startsWith('/collections/')) {
      // 1. Check if we're in a homepage or collections page card
      const card = link.closest('.collection-card, .collection-overlay, .collections-page-card');
      if (card) {
        const h3 = card.querySelector('h3');
        if (h3) {
          const categoryName = h3.textContent.trim();
          if (categoryName) {
            e.preventDefault();
            window.location.href = `/collections/redirect?name=${encodeURIComponent(categoryName)}`;
            return;
          }
        }
      }
    }
  });

  /* ============ WISHLIST ADD TO CART AJAX ============ */
  document.addEventListener('click', async (e) => {
    if (isEditMode()) return;
    const btn = e.target.closest('.velora-wishlist-page .o_wish_add');
    if (!btn || btn.classList.contains('disabled')) return;

    // Prevent Odoo's default event listener from running!
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    const tr = btn.closest('tr');
    if (!tr) return;

    const productId = parseInt(tr.dataset.productId, 10);
    const wishId = parseInt(tr.dataset.wishId, 10);
    if (!productId) return;

    btn.disabled = true;
    btn.classList.add('disabled');
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

    try {
      // 1. Add to cart via AJAX
      await jsonRpc('/shop/cart/update_json', {
        product_id: productId,
        add_qty: 1,
        display: true,
      });

      // 2. Handle wishlist removal if checkbox b2b_wish is NOT checked
      const b2bWish = document.getElementById('b2b_wish');
      const keepInWishlist = b2bWish && b2bWish.checked;

      if (!keepInWishlist && wishId) {
        // Remove from wishlist DB
        await jsonRpc(`/shop/wishlist/remove/${wishId}`);
        // Remove product ID from sessionStorage
        let sessionIds = JSON.parse(sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]');
        sessionIds = sessionIds.filter(id => id !== productId);
        sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(sessionIds));
        
        // Update header wishlist quantity badge
        const wishButtons = document.querySelectorAll('.o_wsale_my_wish');
        wishButtons.forEach(wb => {
          const qtyEl = wb.querySelector('.my_wish_quantity');
          if (qtyEl) qtyEl.textContent = sessionIds.length;
          if (wb.classList.contains('o_wsale_my_wish_hide_empty')) {
            wb.classList.toggle('d-none', !sessionIds.length);
          }
        });

        // Animate row removal beautifully!
        tr.style.transition = 'all 0.4s ease';
        tr.style.opacity = '0';
        tr.style.transform = 'translateX(50px)';
        setTimeout(() => {
          tr.remove();
          // If no rows left, reload the page or redirect to cart
          const remainingRows = document.querySelectorAll('.velora-wishlist-page #o_comparelist_table tbody tr');
          if (remainingRows.length === 0) {
            window.location.href = '/shop/cart';
          }
        }, 400);
      }

      // 3. Load cart drawer and display success
      await loadCartDrawer();
      showToast('Added to your bag ✓');
      openCart();

    } catch (err) {
      showToast('Could not add to bag. Please try again.');
    } finally {
      btn.disabled = false;
      btn.classList.remove('disabled');
      btn.innerHTML = originalHtml;
    }
  }, true); // Capture phase to preempt Odoo's handler

  /* ============ USER MENU DROPDOWN ============ */
  document.addEventListener('click', (e) => {
    if (isEditMode()) return;
    const userMenuButton = e.target.closest('#userMenuButton');
    const userDropdown = document.querySelector('.velora-user-dropdown');

    if (userMenuButton && userDropdown) {
      e.preventDefault();
      e.stopPropagation();
      const isExpanded = userMenuButton.getAttribute('aria-expanded') === 'true';
      userMenuButton.setAttribute('aria-expanded', String(!isExpanded));
      userDropdown.classList.toggle('show');
      return;
    }

    // Close user dropdown if clicking outside
    if (userDropdown && userDropdown.classList.contains('show')) {
      if (!e.target.closest('.user-dropdown-wrap')) {
        const button = document.querySelector('#userMenuButton');
        if (button) button.setAttribute('aria-expanded', 'false');
        userDropdown.classList.remove('show');
      }
    }
  }, true);

})();
