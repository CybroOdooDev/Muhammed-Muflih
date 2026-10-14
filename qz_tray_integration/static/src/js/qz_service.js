/** @odoo-module **/

import { Component, proxy, onWillUnmount, useProps, xml } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export const qzTrayService = {
    dependencies: ["notification", "orm", "action"],
    start(env, { notification, orm, action }) {
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
         * Connect to the QZ Tray desktop application WebSocket.
         */
        async function connect(silent = false) {
            if (!isQzLoaded()) {
                notification.add(
                    _t("QZ Tray library is not loaded. Please refresh the browser."),
                    { type: "danger" }
                );
                return false;
            }

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
                notification.add(
                    _t("Unable to connect to QZ Tray. Please ensure the QZ Tray desktop application is running on your computer."),
                    { type: "danger", sticky: true }
                );
                return false;
            }
        }

        /**
         * Find available printers via QZ Tray and persist them to Odoo.
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

                notification.add(
                    _t("Found %s printer(s): %s", printers.length, printers.join(", ")),
                    { type: "success" }
                );

                // Reload the settings view so the available_printers dropdown updates
                action.doAction("reload");
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

        return {
            connect,
            findPrinters,
            isQzLoaded,
            getQz,
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

/**
 * Connection Status Indicator Widget for res.config.settings
 */
export class QzConnectionStatus extends Component {
    static template = xml`
        <div class="d-inline-flex align-items-center">
            <span t-if="this.isConnected" class="badge rounded-pill text-bg-success py-1 px-2" title="QZ Tray is connected and ready">
                <i class="fa fa-circle me-1" style="font-size: 8px; vertical-align: middle;"/> Connected
            </span>
            <span t-else="" class="badge rounded-pill text-bg-danger py-1 px-2" title="QZ Tray is not running or disconnected">
                <i class="fa fa-circle-o me-1" style="font-size: 8px; vertical-align: middle;"/> Disconnected
            </span>
        </div>
    `;

    props = useProps({
        ...standardWidgetProps,
    });

    setup() {
        this.state = proxy({
            connected: false,
        });
        this.checkStatus();
        this.interval = setInterval(() => this.checkStatus(), 2000);
        onWillUnmount(() => {
            clearInterval(this.interval);
        });
    }

    get isConnected() {
        return Boolean(this.state && this.state.connected);
    }

    checkStatus() {
        const qz = window.qz || globalThis.qz;
        this.state.connected = Boolean(qz && qz.websocket && qz.websocket.isActive && qz.websocket.isActive());
    }
}

export const qzConnectionStatus = {
    component: QzConnectionStatus,
    additionalClasses: ["d-inline-block"],
};

registry.category("view_widgets").add("qz_connection_status", qzConnectionStatus);
