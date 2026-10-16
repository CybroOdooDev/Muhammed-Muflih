/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosTicketPrinterPlugin } from "@point_of_sale/app/plugins/pos_ticket_printer_plugin";
import { PosConfig } from "@point_of_sale/app/models/pos_config";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { _t } from "@web/core/l10n/translation";

// Disable automatic receipt printing upon order payment/validation
patch(OrderPaymentValidation.prototype, {
    async afterOrderValidation() {
        await this.pos.checkPreparationStateAndSentOrderInPreparation(this.order, {
            orderDone: true,
        });
        // Automatic receipt printing upon order validation is disabled.
        // Receipts will only be printed when the user explicitly clicks the print receipt button.
    },
});

patch(PosConfig.prototype, {
    get autoPrint() {
        return false;
    },
});

patch(PosTicketPrinterPlugin.prototype, {
    /**
     * Get the global QZ Tray object.
     */
    getQz() {
        return window.qz || globalThis.qz;
    },

    /**
     * Check if the QZ Tray library is loaded.
     */
    isQzLoaded() {
        const qz = this.getQz();
        return typeof qz !== "undefined" && Boolean(qz.websocket);
    },

    /**
     * Fetch QZ Tray configuration from backend with caching.
     */
    async getQzConfig(force = false) {
        const now = Date.now();
        if (!force && this._cachedQzConfig && (now - (this._lastQzConfigFetch || 0) < 30000)) {
            return this._cachedQzConfig;
        }
        try {
            let config;
            if (this.data && typeof this.data.call === "function") {
                config = await this.data.call("ir.actions.report", "get_qz_config", []);
            } else if (this.env?.services?.orm) {
                config = await this.env.services.orm.call("ir.actions.report", "get_qz_config", []);
            }
            if (config) {
                this._cachedQzConfig = config;
                this._lastQzConfigFetch = now;
                return config;
            }
        } catch (err) {
            console.warn("Could not fetch QZ Tray configuration in POS:", err);
        }
        return { qz_enable: false, default_printer: "" };
    },

    /**
     * Initialize digital certificate & signature endpoints for silent printing.
     */
    async initQzSecurity(config) {
        if (!this.isQzLoaded()) {
            return;
        }
        const qz = this.getQz();
        if (!qz || !qz.security) {
            return;
        }
        if (config.qz_silent_printing && config.qz_certificate) {
            qz.security.setCertificatePromise(function(resolve, reject) {
                fetch("/qz/certificate", { cache: "no-store" })
                    .then((res) => {
                        if (res.ok) return res.text();
                        throw new Error("Failed to fetch certificate: " + res.statusText);
                    })
                    .then(resolve)
                    .catch(reject);
            });
            qz.security.setSignatureAlgorithm("SHA512");
            qz.security.setSignaturePromise(function(toSign) {
                return function(resolve, reject) {
                    fetch("/qz/sign?request=" + encodeURIComponent(toSign), { cache: "no-store" })
                        .then((res) => {
                            if (res.ok) return res.text();
                            throw new Error("Failed to sign QZ request: " + res.statusText);
                        })
                        .then(resolve)
                        .catch(reject);
                };
            });
        }
    },

    /**
     * Connect to the local QZ Tray desktop application.
     */
    async connectQz(silent = true) {
        if (!this.isQzLoaded()) {
            return false;
        }
        const qz = this.getQz();
        try {
            if (!qz.websocket.isActive()) {
                await qz.websocket.connect({ retries: 2, delay: 1 });
            }
            return true;
        } catch (err) {
            console.error("QZ Tray connection error in POS:", err);
            if (!silent && this.notification) {
                this.notification.add(
                    _t("Unable to connect to QZ Tray. Ensure the desktop application is running."),
                    { type: "warning" }
                );
            }
            return false;
        }
    },

    /**
     * Intercept and print receipt directly via QZ Tray using default printer.
     * Returns { successful: true } if printed, or null to allow standard fallback.
     */
    async printViaQzTray({ iframe, image = null }) {
        const config = await this.getQzConfig();
        if (!config || !config.qz_enable) {
            return null;
        }

        const targetPrinter = config.default_printer;
        if (!targetPrinter) {
            console.warn("QZ Tray is enabled, but no default printer is configured.");
            if (this.notification) {
                this.notification.add(
                    _t("QZ Tray is enabled, but no printer is configured in QZ Tray Settings."),
                    { type: "warning" }
                );
            }
            return null;
        }

        if (!this.isQzLoaded()) {
            console.warn("QZ Tray library is not loaded.");
            return null;
        }

        await this.initQzSecurity(config);

        const connected = await this.connectQz(true);
        if (!connected) {
            if (this.notification) {
                this.notification.add(
                    _t("Could not connect to QZ Tray desktop app. Falling back to browser print."),
                    { type: "warning" }
                );
            }
            return null;
        }

        let canvas = image;
        if (!canvas && iframe) {
            canvas = await this.generateImage(iframe);
        }
        if (!canvas) {
            console.warn("No canvas or image available for receipt printing.");
            return null;
        }

        try {
            const qz = this.getQz();
            const dataUrl = canvas.toDataURL("image/png");
            const base64Data = dataUrl.replace(/^data:image\/\w+;base64,/, "");

            const qzConfig = qz.configs.create(targetPrinter, {
                scaleContent: true,
                rasterize: true,
                margins: 0,
            });

            const qzData = [{
                type: "pixel",
                format: "image",
                flavor: "base64",
                data: base64Data,
            }];

            await qz.print(qzConfig, qzData);

            if (this.notification) {
                this.notification.add(
                    _t("Receipt printed on %s via QZ Tray.", targetPrinter),
                    { type: "success" }
                );
            }
            return { successful: true };
        } catch (err) {
            console.error("QZ Tray direct print error:", err);
            if (this.notification) {
                this.notification.add(
                    _t("Failed to print via QZ Tray: %s. Falling back to browser print.", err.message || err),
                    { type: "danger" }
                );
            }
            return null;
        }
    },

    /**
     * Override printWithFallback to intercept POS receipts before browser dialog.
     */
    async printWithFallback(params = {}) {
        const { iframe, image = null, download = false } = params;

        // If IoT/ePOS hardware receipt printers are configured, or download was explicitly requested
        if (this.hasReceiptPrinters || download) {
            return await super.printWithFallback(...arguments);
        }

        // Try printing directly via QZ Tray
        try {
            const qzResult = await this.printViaQzTray({ iframe, image });
            if (qzResult && qzResult.successful) {
                return qzResult;
            }
        } catch (err) {
            console.error("QZ Tray printWithFallback exception:", err);
        }

        // Fallback to standard Odoo behavior (browser print popup)
        this._skipQzWeb = true;
        try {
            return await super.printWithFallback(...arguments);
        } finally {
            this._skipQzWeb = false;
        }
    },

    /**
     * Override printWeb to intercept direct calls to browser print.
     */
    async printWeb(iframe) {
        if (!this._skipQzWeb) {
            try {
                const qzResult = await this.printViaQzTray({ iframe });
                if (qzResult && qzResult.successful) {
                    return qzResult;
                }
            } catch (err) {
                console.error("QZ Tray printWeb exception:", err);
            }
        }
        return super.printWeb(iframe);
    },

    /**
     * Override openCashbox to support opening cash drawer via QZ Tray.
     */
    async openCashbox() {
        const opened = await super.openCashbox();
        if (opened) {
            return opened;
        }
        return await this.openCashboxViaQz();
    },

    /**
     * Open cashbox via QZ Tray using standard ESC/POS command.
     */
    async openCashboxViaQz() {
        const config = await this.getQzConfig();
        if (!config || !config.qz_enable) {
            return false;
        }
        const targetPrinter = config.default_printer;
        if (!targetPrinter || !this.isQzLoaded()) {
            return false;
        }
        await this.initQzSecurity(config);
        const connected = await this.connectQz(true);
        if (!connected) {
            return false;
        }
        try {
            const qz = this.getQz();
            const qzConfig = qz.configs.create(targetPrinter);
            const qzData = [{
                type: "raw",
                format: "command",
                flavor: "plain",
                data: "\x1B\x70\x00\x19\xFA",
            }];
            await qz.print(qzConfig, qzData);
            return true;
        } catch (err) {
            console.warn("Could not open cashbox via QZ Tray:", err);
            return false;
        }
    },
});
