pragma Singleton
import QtQuick

QtObject {
    id: root

    // Backgrounds
    property color background: "#111211"
    property color backgroundElevated: "#151615"
    property color backgroundDeep: "#0C0D0C"

    // Surfaces
    property color surface: "#191A19"
    property color surfaceRaised: "#1E201E"
    property color surfaceHover: "#242624"
    property color surfaceSelected: "#292C29"

    // Borders
    property color border: "#303330"
    property color borderStrong: "#3B3F3B"
    property color divider: "#292C29"

    // Text
    property color textPrimary: "#F1F2EF"
    property color textSecondary: "#B4B8B3"
    property color textMuted: "#777C77"
    property color textDisabled: "#515651"

    // Accent (botanical — not neon)
    property color accent: "#7FAF82"
    property color accentHover: "#91BE94"
    property color accentPressed: "#6E9B72"
    property color accentSurface: "#1D2A1F"

    // Semantic (muted)
    property color success: "#7FAF82"
    property color warning: "#D1A85A"
    property color error: "#C96B6B"
    property color info: "#7C9BB8"

    // Glass — in-app frosted chrome (not desktop acrylic)
    property bool glassEnabled: false
    property real glassOpacity: 0.55
    property real dialogGlassOpacity: 0.85
    property color panel: backgroundElevated
    property real panelOpacity: 1.0
    property color panelFill: backgroundElevated
    property color dialogPanelFill: backgroundElevated
    property color glassWash: backgroundDeep
    property color glassWashAccent: accentSurface
    property color windowFill: background

    // Radius (4–10 only)
    property int radiusSmall: 4
    property int radiusMedium: 6
    property int radiusLarge: 8
    property int radiusHero: 10

    // Spacing
    property int space4: 4
    property int space8: 8
    property int space12: 12
    property int space16: 16
    property int space20: 20
    property int space24: 24
    property int space32: 32
    property int space40: 40
    property int space48: 48
    property int space64: 64

    // Type sizes
    property int fontDisplay: 32
    property int fontPageTitle: 28
    property int fontSection: 17
    property int fontGameTitle: 18
    property int fontBody: 14
    property int fontSecondary: 13
    property int fontCaption: 12
    property int fontMicro: 11

    // Layout
    property int sidebarWidth: 240
    property int contentMargin: 28
    property int navItemHeight: 34
    property int playHeight: 40
    property int searchWidth: 260

    // Motion
    property int durationFast: 140
    property int durationNormal: 160

    // Compat aliases
    property color sidebar: backgroundElevated
    property color surfaceElevated: surfaceRaised
    property int radius: radiusMedium
    property int space: space16

    function _c(map, key, fallback) {
        if (!map)
            return fallback
        var v = map[key]
        return (v === undefined || v === null || v === "") ? fallback : v
    }

    function applyTokens(map) {
        if (!map)
            return
        background = _c(map, "background", background)
        backgroundElevated = _c(map, "backgroundElevated", backgroundElevated)
        backgroundDeep = _c(map, "backgroundDeep", backgroundDeep)
        surface = _c(map, "surface", surface)
        surfaceRaised = _c(map, "surfaceRaised", surfaceRaised)
        surfaceHover = _c(map, "surfaceHover", surfaceHover)
        surfaceSelected = _c(map, "surfaceSelected", surfaceSelected)
        border = _c(map, "border", border)
        borderStrong = _c(map, "borderStrong", borderStrong)
        divider = _c(map, "divider", divider)
        textPrimary = _c(map, "textPrimary", textPrimary)
        textSecondary = _c(map, "textSecondary", textSecondary)
        textMuted = _c(map, "textMuted", textMuted)
        textDisabled = _c(map, "textDisabled", textDisabled)
        accent = _c(map, "accent", accent)
        accentHover = _c(map, "accentHover", accentHover)
        accentPressed = _c(map, "accentPressed", accentPressed)
        accentSurface = _c(map, "accentSurface", accentSurface)
        success = _c(map, "success", success)
        warning = _c(map, "warning", warning)
        error = _c(map, "error", error)
        info = _c(map, "info", info)
        glassOpacity = Number(_c(map, "glassOpacity", glassOpacity))
        dialogGlassOpacity = Number(_c(map, "dialogGlassOpacity", dialogGlassOpacity))
        radiusSmall = Number(_c(map, "radiusSmall", radiusSmall))
        radiusMedium = Number(_c(map, "radiusMedium", radiusMedium))
        radiusLarge = Number(_c(map, "radiusLarge", radiusLarge))
        radiusHero = Number(_c(map, "radiusHero", radiusHero))
        refreshPanel()
    }

    function setGlass(enabled) {
        glassEnabled = !!enabled
        refreshPanel()
    }

    function refreshPanel() {
        panel = backgroundElevated
        panelOpacity = glassEnabled ? glassOpacity : 1.0
        panelFill = glassEnabled
            ? Qt.rgba(backgroundElevated.r, backgroundElevated.g, backgroundElevated.b, glassOpacity)
            : backgroundElevated
        dialogPanelFill = glassEnabled
            ? Qt.rgba(backgroundElevated.r, backgroundElevated.g, backgroundElevated.b, dialogGlassOpacity)
            : backgroundElevated
        // Strong botanical wash so translucent sidebar/menus have contrast
        glassWash = glassEnabled
            ? Qt.rgba(
                backgroundDeep.r * 0.45 + accent.r * 0.55,
                backgroundDeep.g * 0.45 + accent.g * 0.55,
                backgroundDeep.b * 0.45 + accent.b * 0.55,
                1.0)
            : backgroundDeep
        glassWashAccent = glassEnabled
            ? Qt.rgba(accent.r, accent.g, accent.b, 0.22)
            : accentSurface
        windowFill = glassEnabled ? glassWash : background
        sidebar = glassEnabled ? panelFill : backgroundElevated
        surfaceElevated = surfaceRaised
        radius = radiusMedium
        space = space16
    }

    function syncFromController(ctrl) {
        if (!ctrl)
            return
        applyTokens(ctrl.themeTokens)
        setGlass(ctrl.glassEnabled)
    }
}
