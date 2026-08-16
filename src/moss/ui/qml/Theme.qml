pragma Singleton
import QtQuick

QtObject {
    // Backgrounds
    readonly property color background: "#111211"
    readonly property color backgroundElevated: "#151615"
    readonly property color backgroundDeep: "#0C0D0C"

    // Surfaces
    readonly property color surface: "#191A19"
    readonly property color surfaceRaised: "#1E201E"
    readonly property color surfaceHover: "#242624"
    readonly property color surfaceSelected: "#292C29"

    // Borders
    readonly property color border: "#303330"
    readonly property color borderStrong: "#3B3F3B"
    readonly property color divider: "#292C29"

    // Text
    readonly property color textPrimary: "#F1F2EF"
    readonly property color textSecondary: "#B4B8B3"
    readonly property color textMuted: "#777C77"
    readonly property color textDisabled: "#515651"

    // Accent (botanical — not neon)
    readonly property color accent: "#7FAF82"
    readonly property color accentHover: "#91BE94"
    readonly property color accentPressed: "#6E9B72"
    readonly property color accentSurface: "#1D2A1F"

    // Semantic (muted)
    readonly property color success: "#7FAF82"
    readonly property color warning: "#D1A85A"
    readonly property color error: "#C96B6B"
    readonly property color info: "#7C9BB8"

    // Radius (4–10 only)
    readonly property int radiusSmall: 4
    readonly property int radiusMedium: 6
    readonly property int radiusLarge: 8
    readonly property int radiusHero: 10

    // Spacing
    readonly property int space4: 4
    readonly property int space8: 8
    readonly property int space12: 12
    readonly property int space16: 16
    readonly property int space20: 20
    readonly property int space24: 24
    readonly property int space32: 32
    readonly property int space40: 40
    readonly property int space48: 48
    readonly property int space64: 64

    // Type sizes
    readonly property int fontDisplay: 32
    readonly property int fontPageTitle: 28
    readonly property int fontSection: 17
    readonly property int fontGameTitle: 18
    readonly property int fontBody: 14
    readonly property int fontSecondary: 13
    readonly property int fontCaption: 12
    readonly property int fontMicro: 11

    // Layout
    readonly property int sidebarWidth: 240
    readonly property int contentMargin: 28
    readonly property int navItemHeight: 34
    readonly property int playHeight: 40
    readonly property int searchWidth: 260

    // Motion
    readonly property int durationFast: 140
    readonly property int durationNormal: 160

    // Compat aliases used by older components
    readonly property color sidebar: backgroundElevated
    readonly property color surfaceElevated: surfaceRaised
    readonly property int radius: radiusMedium
    readonly property int space: space16
}
