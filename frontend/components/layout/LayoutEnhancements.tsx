"use client";

import { CommandPalette } from "@/components/layout/CommandPalette";
import { NotificationCenter, useNotifications } from "@/components/layout/NotificationCenter";

export function LayoutEnhancements() {
    const { notifications, removeNotification } = useNotifications();

    return (
        <>
            <CommandPalette />
            <NotificationCenter notifications={notifications} onRemove={removeNotification} />
        </>
    );
}
