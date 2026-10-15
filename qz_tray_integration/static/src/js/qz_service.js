/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export const qzTrayService = {
    dependencies: ["notification", "orm", "action"],
    start(env, { notification, orm, action }) {
        let cachedConfig = null;
        let lastConfigFetch = 0;

        /**
         * Get the global QZ Tray object.
         */
        function getQz() {
            return window.qz || globalThis.qz;
        }

        /**
         * Check if the QZ Tray library is loaded.
         */
        function isQzLoaded() {
            const qz = getQz();
            return typeof qz !== "undefined" && Boolean(qz.websocket);
        }

        /**
         * Fetch current QZ configuration from backend.
         */
        async function getConfig(force = false) {
            const now = Date.now();
            if (!force && cachedConfig && (now - lastConfigFetch < 15000)) {
                return cachedConfig;
            }
            try {
                cachedConfig = await orm.call("ir.actions.report", "get_qz_config", []);
                lastConfigFetch = now;
                return cachedConfig;
            } catch (err) {
                console.error("Failed to fetch QZ Tray config:", err);
                return { qz_enable: false, default_printer: "" };
            }
        }

        /**
         * Initialize QZ Tray cryptographic digital signature & certificate handlers for silent printing.
         * Must be configured before initiating websocket connection.
         */
        async function initSecurity() {
            if (!isQzLoaded()) {
                return;
            }
            const qz = getQz();
            if (!qz || !qz.security) {
                return;
            }
            const config = await getConfig();
            if (config.qz_silent_printing && config.qz_certificate) {
                qz.security.setCertificatePromise(function(resolve, reject) {
                    fetch("/qz/certificate", { cache: "no-store" })
                        .then(function(res) {
                            if (res.ok) {
                                return res.text();
                            }
                            throw new Error("Failed to fetch certificate: " + res.statusText);
                        })
                        .then(resolve)
                        .catch(reject);
                });
                qz.security.setSignatureAlgorithm("SHA512");
                qz.security.setSignaturePromise(function(toSign) {
                    return function(resolve, reject) {
                        fetch("/qz/sign?request=" + encodeURIComponent(toSign), { cache: "no-store" })
                            .then(function(res) {
                                if (res.ok) {
                                    return res.text();
                                }
                                throw new Error("Failed to sign QZ request: " + res.statusText);
                            })
                            .then(resolve)
                            .catch(reject);
                    };
                });
            }
        }

        // Initialize security handlers eagerly on service start
        initSecurity().catch((err) => console.warn("QZ Tray security pre-init warning:", err));

        /**
         * Connect to the QZ Tray desktop application WebSocket.
         */
        async function connect(silent = false) {
            if (!isQzLoaded()) {
                if (!silent) {
                    notification.add(
                        _t("QZ Tray library is not loaded. Please refresh the browser."),
                        { type: "danger" }
                    );
                }
                return false;
            }

            await initSecurity();

            const qz = getQz();
            try {
                if (!qz.websocket.isActive()) {
                    await qz.websocket.connect({ retries: 2, delay: 1 });
                }
                if (!silent) {
                    notification.add(
                        _t("Connected to QZ Tray desktop application successfully."),
                        { type: "success" }
                    );
                }
                return true;
            } catch (err) {
                console.error("QZ Tray connection error:", err);
                if (!silent) {
                    notification.add(
                        _t("Unable to connect to QZ Tray. Please ensure the QZ Tray desktop application is running on your computer."),
                        { type: "danger", sticky: true }
                    );
                }
                return false;
            }
        }

        /**
         * Find available printers via QZ Tray and persist them to Odoo in real-time.
         * Detects all currently active printers (including newly connected ones).
         */
        async function findPrinters() {
            if (!isQzLoaded()) {
                notification.add(
                    _t("QZ Tray library is not loaded. Please refresh the browser."),
                    { type: "danger" }
                );
                return [];
            }

            const qz = getQz();
            try {
                if (!qz.websocket.isActive()) {
                    const connected = await connect(true);
                    if (!connected) {
                        return [];
                    }
                }

                // Query QZ Tray directly so newly connected/powered-on printers are found
                const printers = await qz.printers.find();
                if (!printers || printers.length === 0) {
                    notification.add(
                        _t("No printers found from QZ Tray."),
                        { type: "warning" }
                    );
                    return [];
                }

                // Save detected printers to Odoo backend
                await orm.call("res.config.settings", "save_detected_printers", [printers]);
                await getConfig(true);

                notification.add(
                    _t("Found %s printer(s): %s", printers.length, printers.join(", ")),
                    { type: "success" }
                );

                // Reload the settings view so the printer dropdown refreshes with new options.
                // The certificate is installed in QZ Tray's trust store (override.crt),
                // so the reconnection after reload will be fully silent — no popup.
                action.doAction({
                    type: "ir.actions.client",
                    tag: "reload",
                });

                return printers;
            } catch (err) {
                console.error("QZ Tray printer detection error:", err);
                notification.add(
                    _t("Failed to detect printers from QZ Tray: ") + (err.message || err),
                    { type: "danger", sticky: true }
                );
                return [];
            }
        }

        /**
         * Intercept report action and print directly via QZ Tray.
         * Returns true if printed successfully, false to fallback to standard download.
         */
        async function printReport(reportAction, options) {
            // Do not intercept HTML preview actions
            if (reportAction.report_type === "qweb-html") {
                return false;
            }

            const config = await getConfig();
            if (!config || !config.qz_enable) {
                return false;
            }

            if (!config.default_printer) {
                return false;
            }

            // Ensure QZ Tray connection
            const qz = getQz();
            if (!qz || !qz.websocket || !qz.websocket.isActive()) {
                const connected = await connect(true);
                if (!connected) {
                    notification.add(
                        _t("QZ Tray desktop app is not connected. Downloading file instead."),
                        { type: "warning" }
                    );
                    return false;
                }
            }

            let resIds = null;
            if (reportAction.context) {
                if (reportAction.context.active_ids && reportAction.context.active_ids.length) {
                    resIds = reportAction.context.active_ids;
                } else if (reportAction.context.active_id) {
                    resIds = [reportAction.context.active_id];
                }
            }

            let payload;
            try {
                payload = await orm.call(
                    "ir.actions.report",
                    "render_report_for_qz",
                    [
                        reportAction.report_name,
                        resIds,
                        reportAction.data || {},
                        reportAction.context || {},
                    ]
                );
            } catch (err) {
                console.error("Failed to render report for QZ Tray:", err);
                notification.add(
                    _t("Could not prepare report for QZ Tray. Falling back to browser download."),
                    { type: "warning" }
                );
                return false;
            }

            if (!payload || !payload.data) {
                return false;
            }

            const targetPrinter = config.default_printer;
            if (!targetPrinter) {
                return false;
            }

            try {
                const qz = getQz();
                const qzConfig = qz.configs.create(targetPrinter);
                const qzData = [{
                    type: payload.type,
                    format: payload.format,
                    flavor: payload.flavor,
                    data: payload.data,
                }];

                await qz.print(qzConfig, qzData);

                notification.add(
                    _t("Printed '%s' successfully on %s", payload.report_name || reportAction.report_name, targetPrinter),
                    { type: "success" }
                );
                return true;
            } catch (err) {
                console.error("QZ Tray direct printing error:", err);
                notification.add(
                    _t("Printing via QZ Tray failed: ") + (err.message || err) + _t(". Falling back to download."),
                    { type: "danger" }
                );
                return false;
            }
        }

        return {
            connect,
            findPrinters,
            isQzLoaded,
            getQz,
            getConfig,
            printReport,
        };
    },
};

registry.category("services").add("qz_tray", qzTrayService);

// Register client actions triggered by res.config.settings buttons
registry.category("actions").add("qz_connect_action", async (env) => {
    const qzService = env.services.qz_tray;
    if (qzService) {
        await qzService.connect();
    }
});

registry.category("actions").add("qz_find_printers_action", async (env) => {
    const qzService = env.services.qz_tray;
    if (qzService) {
        await qzService.findPrinters();
    }
});

// Central Report Interceptor for all Odoo print/download actions
registry.category("ir.actions.report handlers").add("qz_tray_report_handler", async (action, options, env) => {
    const qzService = env.services?.qz_tray;
    if (!qzService) {
        return false;
    }
    return await qzService.printReport(action, options);
});
