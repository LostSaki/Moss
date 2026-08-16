import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."

Item {
    id: root

    property var cfg: ({})
    property string section: "general"
    property var runtimes: []
    property var geStatus: ({})

    Component.onCompleted: reload()

    function reload() {
        cfg = moss.loadSettings()
        runtimes = moss.listRuntimes()
        geStatus = moss.protonGeStatus()
        Theme.syncFromController(moss)
    }

    function fieldBg() {
        return Theme.surface
    }

    function saveCore() {
        moss.saveSettings({
            games_folder: gamesFolder.text,
            preferred_runtime: preferredRuntime.currentValue,
            proton_path: protonPath.text,
            wine_path: winePath.text,
            steamgriddb_api_key: apiKey.text,
            create_steam_shortcuts: steamOn.checked,
            check_updates: updatesOn.checked,
            theme: themeChoice.currentValue,
            glass_enabled: glassOn.checked
        })
        reload()
    }

    RowLayout {
        anchors.fill: parent
        spacing: Theme.space24

        // Settings nav
        Column {
            Layout.preferredWidth: 180
            Layout.fillHeight: true
            spacing: 2

            Text {
                text: "Settings"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontPageTitle
            }
            Item { width: 1; height: Theme.space16 }

            Repeater {
                model: [
                    { id: "general", label: "General" },
                    { id: "appearance", label: "Appearance" },
                    { id: "runtimes", label: "Runtimes" },
                    { id: "artwork", label: "Artwork" },
                    { id: "steam", label: "Steam" },
                    { id: "updates", label: "Updates" },
                    { id: "advanced", label: "Advanced" },
                    { id: "library", label: "Library", soon: true },
                    { id: "controllers", label: "Controllers", soon: true },
                    { id: "system", label: "System report", soon: true },
                    { id: "runners", label: "Runners extra", soon: true },
                    { id: "services", label: "Store services", soon: true }
                ]
                delegate: Button {
                    width: 180
                    implicitHeight: Theme.navItemHeight
                    text: modelData.label + (modelData.soon ? " · soon" : "")
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: root.section === modelData.id ? Theme.surfaceSelected : "transparent"
                        border.width: root.section === modelData.id ? 1 : 0
                        border.color: Theme.border
                    }
                    contentItem: Text {
                        text: parent.text
                        color: modelData.soon ? Theme.textMuted : Theme.textPrimary
                        font.pixelSize: Theme.fontSecondary
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: Theme.space8
                    }
                    onClicked: root.section = modelData.id
                }
            }
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: bodyCol.height + Theme.space40

            Column {
                id: bodyCol
                width: parent.width - 8
                spacing: Theme.space32

                // GENERAL
                MossSection {
                    visible: root.section === "general"
                    title: "General"
                    description: "Where Moss looks when adding games, and preferred runtime mode."
                    Column {
                        width: parent.width
                        spacing: Theme.space12
                        Text { text: "Games folder"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
                        RowLayout {
                            width: parent.width
                            spacing: Theme.space8
                            TextField {
                                id: gamesFolder
                                Layout.fillWidth: true
                                text: cfg.games_folder || ""
                                color: Theme.textPrimary
                                font.pixelSize: Theme.fontSecondary
                                background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
                            }
                            MossSecondaryButton { text: "Browse"; onClicked: folderDlg.open() }
                        }
                        Text { text: "Preferred runtime"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
                        ComboBox {
                            id: preferredRuntime
                            width: Math.min(280, parent.width)
                            textRole: "label"
                            valueRole: "id"
                            model: [
                                { id: "auto", label: "Auto (Proton, then Wine)" },
                                { id: "proton", label: "Proton" },
                                { id: "wine", label: "Wine" }
                            ]
                            Component.onCompleted: {
                                var i = 0
                                for (var n = 0; n < model.length; n++) {
                                    if (model[n].id === (cfg.preferred_runtime || "auto"))
                                        i = n
                                }
                                currentIndex = i
                            }
                        }
                    }
                }

                // APPEARANCE
                MossSection {
                    visible: root.section === "appearance"
                    title: "Appearance"
                    description: "Theme tokens and selective glass surfaces (sidebar, menus, dialogs)."
                    Column {
                        width: parent.width
                        spacing: Theme.space16
                        Text { text: "Theme"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
                        ComboBox {
                            id: themeChoice
                            width: Math.min(280, parent.width)
                            textRole: "label"
                            valueRole: "id"
                            model: moss.themes
                            Component.onCompleted: {
                                var want = cfg.theme || "moss_dark"
                                for (var n = 0; n < count; n++) {
                                    if (model[n].id === want)
                                        currentIndex = n
                                }
                            }
                            onActivated: {
                                moss.setTheme(currentValue)
                                if (currentValue === "soft_glass")
                                    glassOn.checked = true
                                reload()
                            }
                        }
                        MossToggle {
                            id: glassOn
                            checked: !!cfg.glass_enabled
                            text: "Glass surfaces"
                            onToggled: {
                                moss.setGlassEnabled(checked)
                                Theme.setGlass(checked)
                            }
                        }
                        Text {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            text: "When on, panels use ~88–90% opacity. Game cards stay opaque."
                            color: Theme.textMuted
                            font.pixelSize: Theme.fontCaption
                        }
                    }
                }

                // RUNTIMES
                MossSection {
                    visible: root.section === "runtimes"
                    title: "Runtimes"
                    description: "Detected Proton and Wine installs. Set a default for launches."
                    Column {
                        width: parent.width
                        spacing: Theme.space12

                        Text {
                            visible: runtimes.length === 0
                            width: parent.width
                            wrapMode: Text.WordWrap
                            text: geStatus.platform === "windows"
                                  ? "On Windows, Moss shows detection-only status. Full Proton/Wine launching is Linux-oriented."
                                  : "No Proton or Wine detected yet."
                            color: Theme.textMuted
                            font.pixelSize: Theme.fontCaption
                        }

                        Repeater {
                            model: runtimes
                            delegate: Rectangle {
                                width: parent.width
                                height: 52
                                radius: Theme.radiusSmall
                                color: Theme.surface
                                border.width: 1
                                border.color: (cfg.default_runtime_id === modelData.id) ? Theme.accent : Theme.border

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: Theme.space12
                                    spacing: Theme.space8
                                    Column {
                                        Layout.fillWidth: true
                                        spacing: 2
                                        Text {
                                            text: modelData.name + "  ·  " + modelData.kind
                                            color: Theme.textPrimary
                                            font.pixelSize: Theme.fontSecondary
                                        }
                                        Text {
                                            text: modelData.path
                                            color: Theme.textMuted
                                            font.pixelSize: Theme.fontMicro
                                            elide: Text.ElideMiddle
                                            width: parent.width
                                        }
                                    }
                                    MossSecondaryButton {
                                        text: (cfg.default_runtime_id === modelData.id) ? "Default" : "Set default"
                                        enabled: cfg.default_runtime_id !== modelData.id
                                        onClicked: {
                                            moss.setDefaultRuntime(modelData.id)
                                            reload()
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: Theme.divider
                        }

                        Item { width: 1; height: Theme.space8 }

                        Text {
                            text: "Manual paths"
                            color: Theme.textPrimary
                            font.pixelSize: Theme.fontSecondary
                            font.weight: Font.DemiBold
                        }
                        Text { text: "Proton path"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
                        TextField {
                            id: protonPath
                            width: parent.width
                            text: cfg.proton_path || ""
                            color: Theme.textPrimary
                            font.pixelSize: Theme.fontSecondary
                            background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
                        }
                        Text { text: "Wine path"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
                        TextField {
                            id: winePath
                            width: parent.width
                            text: cfg.wine_path || ""
                            color: Theme.textPrimary
                            font.pixelSize: Theme.fontSecondary
                            background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
                        }

                        Column {
                            width: parent.width
                            spacing: Theme.space8
                            Item { width: 1; height: Theme.space8 }
                            Text {
                                text: "Proton-GE"
                                color: Theme.textPrimary
                                font.pixelSize: Theme.fontSecondary
                                font.weight: Font.DemiBold
                            }
                            Text {
                                width: parent.width
                                wrapMode: Text.WordWrap
                                text: geStatus.message || ""
                                color: Theme.textMuted
                                font.pixelSize: Theme.fontCaption
                            }
                            Row {
                                spacing: Theme.space8
                                MossButton {
                                    text: moss.busy ? "Installing…" : "Install Proton-GE"
                                    enabled: !!geStatus.can_install && !moss.busy
                                    onClicked: moss.installProtonGE()
                                }
                                MossSecondaryButton {
                                    text: "Releases"
                                    onClicked: moss.openUrl(geStatus.releases_url || "https://github.com/GloriousEggroll/proton-ge-custom/releases")
                                }
                                MossSecondaryButton {
                                    text: "Refresh"
                                    onClicked: reload()
                                }
                            }
                        }
                    }
                }

                // ARTWORK
                MossSection {
                    visible: root.section === "artwork"
                    title: "Artwork"
                    description: "SteamGridDB API key for covers and heroes."
                    TextField {
                        id: apiKey
                        width: parent.width
                        echoMode: TextInput.Password
                        text: cfg.steamgriddb_api_key || ""
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSecondary
                        background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
                    }
                }

                // STEAM
                MossSection {
                    visible: root.section === "steam"
                    title: "Steam"
                    description: "Write non-Steam shortcuts and grid art."
                    MossToggle {
                        id: steamOn
                        checked: cfg.create_steam_shortcuts !== false
                        text: "Create Steam Shortcuts"
                    }
                }

                // UPDATES
                MossSection {
                    visible: root.section === "updates"
                    title: "Updates"
                    description: "Automatically check for new Moss releases."
                    MossToggle {
                        id: updatesOn
                        checked: cfg.check_updates !== false
                        text: "Check for Updates"
                    }
                }

                // ADVANCED
                MossSection {
                    visible: root.section === "advanced"
                    title: "Advanced"
                    description: "Library, prefixes, and logs."
                    Row {
                        spacing: Theme.space8
                        MossSecondaryButton { text: "Open data folder"; onClicked: moss.openDataDir() }
                        MossSecondaryButton { text: "GitHub"; onClicked: moss.openGithub() }
                    }
                }

                // PLACEHOLDERS
                MossSection {
                    visible: root.section === "library" || root.section === "controllers"
                              || root.section === "system" || root.section === "runners"
                              || root.section === "services"
                    title: sectionTitle()
                    description: "Scaffold only — not implemented in this slice."
                    Text {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontSecondary
                        text: placeholderCopy()
                    }
                }

                MossButton {
                    visible: root.section === "general" || root.section === "appearance"
                             || root.section === "runtimes" || root.section === "artwork"
                             || root.section === "steam" || root.section === "updates"
                    text: "Save"
                    onClicked: saveCore()
                }
            }
        }
    }

    function sectionTitle() {
        switch (root.section) {
        case "library": return "Library"
        case "controllers": return "Controllers"
        case "system": return "System report"
        case "runners": return "Runners"
        case "services": return "Store services"
        default: return "Coming soon"
        }
    }

    function placeholderCopy() {
        switch (root.section) {
        case "library": return "Categories, tags, and hidden games will land here."
        case "controllers": return "Controller layouts and Steam Input hooks — planned."
        case "system": return "Hardware/OS report for troubleshooting — planned."
        case "runners": return "Extra runners (DXVK builds, custom Wine) beyond Proton/Wine list — planned."
        case "services": return "GOG / Epic / store sync — planned. Not in this release."
        default: return "Coming soon."
        }
    }

    FolderDialog {
        id: folderDlg
        title: "Games folder"
        onAccepted: gamesFolder.text = moss.localPath(selectedFolder)
    }

    Connections {
        target: moss
        function onRuntimesChanged() { reload() }
        function onConfigChanged() { cfg = moss.loadSettings() }
    }
}
