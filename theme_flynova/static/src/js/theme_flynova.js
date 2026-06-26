/** @odoo-module **/

import { Component, onMounted, onWillDestroy } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class FlynovaTheme extends Component {
    static template = "theme_flynova.FlynovaTheme";

    setup() {
        this._cleanups = [];
        this._intervals = [];
        this._timeouts = [];
        this._animations = new Map();

        onMounted(() => {
            // Run _initScrollHeader synchronously so the correct header
            // background is applied on the very first frame — before any
            // paint — preventing the transparent-to-white flicker.
            this._initScrollHeader();

            // Defer heavier non-critical initialisation to keep TTI low.
            this._registerTimeout(() => {
                this._initMobileMenu();
                this._initCarousels();
                this._initBookingGallery();
                this._initBookingCounters();
                this._initExtraServices();
                this._initPaymentButtons();
            }, 0);
        });

        onWillDestroy(() => {
            this._cleanupAll();
        });
    }

    _cleanupAll() {
        this._cleanups.forEach((cleanup) => cleanup());
        this._cleanups = [];

        this._intervals.forEach((timer) => window.clearInterval(timer));
        this._intervals = [];

        this._timeouts.forEach((timer) => window.clearTimeout(timer));
        this._timeouts = [];

        this._animations.forEach((animationId) => window.cancelAnimationFrame(animationId));
        this._animations.clear();
    }

    _registerCleanup(target, eventName, handler, options) {
        target.addEventListener(eventName, handler, options);
        this._cleanups.push(() => target.removeEventListener(eventName, handler, options));
    }

    _registerInterval(callback, delay) {
        const intervalId = window.setInterval(callback, delay);
        this._intervals.push(intervalId);
        return intervalId;
    }

    _registerTimeout(callback, delay) {
        const timeoutId = window.setTimeout(() => {
            this._timeouts = this._timeouts.filter((id) => id !== timeoutId);
            callback();
        }, delay);
        this._timeouts.push(timeoutId);
        return timeoutId;
    }

    _initMobileMenu() {
        const menuBtn = document.getElementById("menuBtn");
        const closeBtn = document.getElementById("closeBtn");
        const mobileNav = document.getElementById("mobileNav");
        const overlay = document.getElementById("overlay");

        if (!mobileNav || !overlay) {
            return;
        }

        const toggleMenu = () => {
            mobileNav.classList.toggle("active");
            overlay.classList.toggle("active");
        };

        if (menuBtn) {
            this._registerCleanup(menuBtn, "click", toggleMenu);
        }
        if (closeBtn) {
            this._registerCleanup(closeBtn, "click", toggleMenu);
        }
        this._registerCleanup(overlay, "click", toggleMenu);
    }

    _initScrollHeader() {
        const header = document.querySelector("header#top");
        if (!header) {
            return;
        }
        const wrap = document.querySelector("#wrapwrap");
        const getScrollTop = () => (
            window.scrollY
            || document.documentElement.scrollTop
            || document.body.scrollTop
            || (wrap && wrap.scrollTop)
            || 0
        );

        const onScroll = () => {
            // Threshold of 1px: header turns solid the moment any scroll
            // begins, including when Odoo scrolls #wrapwrap instead of window.
            header.classList.toggle("active", getScrollTop() > 1);
        };
        const prepareForScroll = (event) => {
            if ((event.deltaY || 0) > 0 || getScrollTop() > 1) {
                header.classList.add("active");
            }
        };
        // Apply immediately (synchronous) so initial state is correct
        // before the first painted frame.
        onScroll();
        this._registerCleanup(window, "scroll", onScroll, { passive: true });
        this._registerCleanup(window, "wheel", prepareForScroll, { passive: true });
        this._registerCleanup(window, "touchstart", prepareForScroll, { passive: true });
        if (wrap) {
            this._registerCleanup(wrap, "scroll", onScroll, { passive: true });
        }
    }

    _animateScroll(viewport, targetLeft, duration = 260) {
        const currentAnimation = this._animations.get(viewport);
        if (currentAnimation) {
            window.cancelAnimationFrame(currentAnimation);
        }

        const startLeft = viewport.scrollLeft;
        const distance = targetLeft - startLeft;
        if (Math.abs(distance) < 1) {
            viewport.scrollLeft = targetLeft;
            return;
        }

        const startTime = performance.now();
        const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

        const step = (now) => {
            const progress = Math.min((now - startTime) / duration, 1);
            viewport.scrollLeft = startLeft + (distance * easeOutCubic(progress));
            if (progress < 1) {
                const animationId = window.requestAnimationFrame(step);
                this._animations.set(viewport, animationId);
            } else {
                this._animations.delete(viewport);
                viewport.scrollLeft = targetLeft;
            }
        };

        const animationId = window.requestAnimationFrame(step);
        this._animations.set(viewport, animationId);
    }

    _initCarousels() {
        document.querySelectorAll(".flynova-carousel").forEach((carousel) => {
            const viewport = carousel.querySelector(".flynova-carousel-viewport");
            const track = carousel.querySelector(".flynova-carousel-track");
            const prevBtn = carousel.querySelector(".flynova-carousel-control--prev");
            const nextBtn = carousel.querySelector(".flynova-carousel-control--next");
            const controlsEnabled = carousel.dataset.carouselControls !== "false";
            const sourceSlides = Array.from(track?.querySelectorAll(".flynova-carousel-slide") || []);

            if (!viewport || !track || !sourceSlides.length) {
                return;
            }

            if (sourceSlides.length > 1) {
                sourceSlides.forEach((slide) => {
                    track.appendChild(slide.cloneNode(true));
                });
            }

            const getStride = () => {
                const firstSlide = track.querySelector(".flynova-carousel-slide");
                if (!firstSlide) {
                    return viewport.clientWidth;
                }
                const trackStyle = window.getComputedStyle(track);
                const gap = parseFloat(trackStyle.columnGap || trackStyle.gap || "0");
                return firstSlide.getBoundingClientRect().width + gap;
            };

            const getCycleWidth = () => getStride() * sourceSlides.length;

            const updateStaticState = () => {
                const isStatic = sourceSlides.length <= 1;
                carousel.classList.toggle("is-static", isStatic);
                if (prevBtn) {
                    prevBtn.disabled = isStatic;
                }
                if (nextBtn) {
                    nextBtn.disabled = isStatic;
                }
            };

            const normalizePosition = () => {
                if (sourceSlides.length <= 1) {
                    return;
                }
                const cycleWidth = getCycleWidth();
                const currentLeft = viewport.scrollLeft;
                if (currentLeft >= cycleWidth) {
                    viewport.scrollLeft = currentLeft - cycleWidth;
                } else if (currentLeft < 0) {
                    viewport.scrollLeft = currentLeft + cycleWidth;
                }
            };

            const scrollByStep = (direction) => {
                if (sourceSlides.length <= 1) {
                    return;
                }

                const stride = getStride();
                const cycleWidth = getCycleWidth();

                if (direction < 0 && viewport.scrollLeft <= 1) {
                    viewport.scrollLeft = cycleWidth;
                }

                this._animateScroll(viewport, viewport.scrollLeft + (stride * direction), 240);
                this._registerTimeout(() => {
                    if (direction > 0 && viewport.scrollLeft >= cycleWidth - (stride * 0.35)) {
                        viewport.scrollLeft -= cycleWidth;
                    } else if (direction < 0 && viewport.scrollLeft <= stride * 0.35) {
                        viewport.scrollLeft += cycleWidth;
                    }
                }, 250);
            };

            if (controlsEnabled && prevBtn) {
                this._registerCleanup(prevBtn, "click", () => scrollByStep(-1));
            }
            if (controlsEnabled && nextBtn) {
                this._registerCleanup(nextBtn, "click", () => scrollByStep(1));
            }

            const onResize = () => {
                normalizePosition();
                updateStaticState();
            };
            this._registerCleanup(window, "resize", onResize, { passive: true });
            updateStaticState();

            if (carousel.dataset.carouselAutoplay === "true" && sourceSlides.length > 1) {
                const intervalMs = parseInt(carousel.dataset.carouselInterval || "2200", 10);
                let autoplayId = null;

                const stopAutoplay = () => {
                    if (autoplayId) {
                        window.clearInterval(autoplayId);
                        this._intervals = this._intervals.filter((id) => id !== autoplayId);
                        autoplayId = null;
                    }
                };
                const startAutoplay = () => {
                    if (!autoplayId) {
                        autoplayId = this._registerInterval(() => scrollByStep(1), intervalMs);
                    }
                };

                startAutoplay();
                this._registerCleanup(carousel, "mouseenter", stopAutoplay);
                this._registerCleanup(carousel, "mouseleave", startAutoplay);
                this._registerCleanup(carousel, "focusin", stopAutoplay);
                this._registerCleanup(carousel, "focusout", startAutoplay);
                this._registerCleanup(carousel, "touchstart", stopAutoplay, { passive: true });
                this._registerCleanup(carousel, "touchend", startAutoplay, { passive: true });
            }
        });
    }

    _initBookingGallery() {
        const thumbnails = document.querySelectorAll(".booking-thumbnail");
        const mainImage = document.getElementById("main_booking_image");

        if (!mainImage || !thumbnails.length) {
            return;
        }

        thumbnails.forEach((thumb) => {
            this._registerCleanup(thumb, "click", () => {
                const img = thumb.querySelector("img");
                if (img) {
                    mainImage.src = img.src;
                    thumbnails.forEach((t) => t.classList.remove("active"));
                    thumb.classList.add("active");
                }
            });
        });
    }

    _initBookingCounters() {
        const counterControls = document.querySelectorAll(".counter-controls");
        if (!counterControls.length) {
            return;
        }

        counterControls.forEach((control) => {
            const type = control.dataset.type;
            const minusBtn = control.querySelector(".minus");
            const plusBtn = control.querySelector(".plus");
            const valueDisplay = control.querySelector(".counter-value");
            const hiddenInput = document.getElementById(`${type}_qty_input`);

            if (!minusBtn || !plusBtn || !valueDisplay || !hiddenInput) {
                return;
            }

            const updateValue = (delta) => {
                let currentValue = parseInt(valueDisplay.textContent, 10);
                const newValue = Math.max(type === "adult" ? 1 : 0, currentValue + delta);
                valueDisplay.textContent = newValue;
                hiddenInput.value = newValue;
                // Trigger total price update
                this._updateBookingTotal();
            };

            this._registerCleanup(minusBtn, "click", () => updateValue(-1));
            this._registerCleanup(plusBtn, "click", () => updateValue(1));
        });
    }

    _updateBookingTotal() {
        const totalEl = document.getElementById("tour_total_price") || document.getElementById("hotel_total_price");
        if (!totalEl) return;

        const adultPrice = parseFloat(totalEl.dataset.adultPrice || "0");
        const childPrice = parseFloat(totalEl.dataset.childPrice || "0");

        const adultQty = parseInt(document.getElementById("adult_qty_input")?.value || "1", 10);
        const childQty = parseInt(document.getElementById("child_qty_input")?.value || "0", 10);
        const totalGuests = adultQty + childQty;

        let total = (adultQty * adultPrice) + (childQty * childPrice);

        // Add extra services (multiply by guest count)
        const checkboxes = document.querySelectorAll(".extra-service-checkbox");
        checkboxes.forEach((cb) => {
            if (cb.checked) {
                total += parseFloat(cb.dataset.price || "0") * totalGuests;
            }
        });

        totalEl.textContent = Math.round(total);
    }

    _initExtraServices() {
        const checkboxes = document.querySelectorAll(".extra-service-checkbox");
        if (!checkboxes.length) return;

        checkboxes.forEach((cb) => {
            this._registerCleanup(cb, "change", () => this._updateBookingTotal());
        });

        // Initial update
        this._updateBookingTotal();
    }

    _initPaymentButtons() {
        const backBtn = document.querySelector(".flynova-payment-back-btn");
        if (!backBtn) {
            return;
        }

        const alignButtons = () => {
            const submitBtn = document.querySelector('button[name="o_payment_submit_button"]');
            if (submitBtn && backBtn.parentNode !== submitBtn.parentNode) {
                submitBtn.parentNode.insertBefore(backBtn, submitBtn);
                const wrapper = document.querySelector(".action-buttons");
                if (wrapper && !wrapper.children.length) {
                    wrapper.remove();
                }
                return true;
            }
            return false;
        };

        // Try immediately
        if (alignButtons()) {
            return;
        }

        // If not found (e.g. loading dynamically), observe #payment_method
        const paymentMethodEl = document.getElementById("payment_method");
        if (paymentMethodEl) {
            const observer = new MutationObserver((mutations, obs) => {
                if (alignButtons()) {
                    obs.disconnect();
                }
            });
            observer.observe(paymentMethodEl, {
                childList: true,
                subtree: true
            });
            this._cleanups.push(() => observer.disconnect());
        }
    }
}

registry.category("public_components").add("theme_flynova.FlynovaTheme", FlynovaTheme);
