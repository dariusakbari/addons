/** @odoo-module */
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import { useState, useRef } from "@odoo/owl";

export class PasswordCopyField extends CharField {
    static template = "custom_password_copy_field.PasswordCopyField";

    setup() {
        super.setup();
        this.state = useState({ showPassword: false });
        this.inputRef = useRef("input");
    }

    togglePasswordVisibility() {
        this.state.showPassword = !this.state.showPassword;
        this.inputRef.el.type = this.state.showPassword ? "text" : "password";
    }

    async copyToClipboard() {
        try {
            await navigator.clipboard.writeText(this.inputRef.el.value);
            this.env.services.notification.add("Copied to clipboard ✅", { type: "success" });
        } catch (err) {
            this.env.services.notification.add("Failed to copy ❌", { type: "danger" });
        }
    }
}

registry.category("fields").add("password_toggle_copy", {
    component: PasswordCopyField,
});
