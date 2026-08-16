import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."

Dialog {
    id: root
    modal: true
    anchors.centerIn: Overlay.overlay
    width: Math.min(560, parent ? parent.width - 48 : 560)
    height: Math.min(720, parent ? parent.height - 48 : 720)
    title: "Game settings"
    standardButtons: Dialog.Save | Dialog.Cancel
    property string gameId: ""
    property var runtimes: []
    property var winetricksVerbs: []
    property var hostTools: ({ gamescope: false, mangohud: false, gamemode: false })
    property var profileModel: []
    property bool syncSupported: false

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.durationNormal; easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; from: 0.98; to: 1; duration: Theme.durationNormal; easing.type: Easing.OutCubic }
        }
    }

    background: Rectangle {
        color: Theme.dialogPanelFill
        border.width: 1
        border.color: Theme.border
        radius: Theme.radiusLarge
    }

    function fieldBg() {
        return Theme.surface
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: formCol.height
        clip: true

        ColumnLayout {
            id: formCol
            width: parent.width
            spacing: Theme.space12

            Text { text: "Name"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            TextField {
                id: nameField
                Layout.fillWidth: true
                color: Theme.textPrimary
                background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
            }

            Text { text: "Executable"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.space8
                TextField {
                    id: exeField
                    Layout.fillWidth: true
                    color: Theme.textPrimary
                    background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
                }
                MossSecondaryButton { text: "Browse"; onClicked: exeDlg.open() }
            }

            Text { text: "Working directory"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.space8
                TextField {
                    id: cwdField
                    Layout.fillWidth: true
                    color: Theme.textPrimary
                    placeholderText: "Default: EXE folder"
                    background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
                }
                MossSecondaryButton { text: "Browse"; onClicked: cwdDlg.open() }
            }

            Text { text: "Launch arguments"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            TextField {
                id: argsField
                Layout.fillWidth: true
                color: Theme.textPrimary
                placeholderText: "e.g. -windowed -novid"
                background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
            }

            Text { text: "Runner"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            ComboBox {
                id: runnerBox
                Layout.fillWidth: true
                textRole: "label"
                valueRole: "id"
                model: root.runtimes
            }

            Text { text: "Windows version"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            ComboBox {
                id: winBox
                Layout.preferredWidth: 200
                model: [
                    { id: "", label: "Default" },
                    { id: "win10", label: "Windows 10" },
                    { id: "win7", label: "Windows 7" },
                    { id: "winxp", label: "Windows XP" }
                ]
                textRole: "label"
                valueRole: "id"
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Applied with winecfg on Linux when you save or launch."
                color: Theme.textMuted
                font.pixelSize: Theme.fontCaption
            }

            MossToggle { id: dxvkToggle; text: "DXVK" }
            MossToggle { id: vkd3dToggle; text: "VKD3D (D3D12)" }
            MossToggle {
                id: gamescopeToggle
                text: "Gamescope" + (root.hostTools.gamescope ? "" : " (not found)")
            }
            TextField {
                id: gamescopeArgsField
                Layout.fillWidth: true
                enabled: gamescopeToggle.checked
                color: Theme.textPrimary
                placeholderText: "Gamescope args (optional)"
                background: Rectangle { radius: Theme.radiusSmall; color: fieldBg(); border.width: 1; border.color: Theme.border }
            }
            MossToggle {
                id: mangohudToggle
                text: "MangoHud" + (root.hostTools.mangohud ? "" : " (not found)")
            }
            MossToggle {
                id: gamemodeToggle
                text: "GameMode" + (root.hostTools.gamemode ? "" : " (not found)")
            }
            MossToggle {
                id: esyncToggle
                text: root.syncSupported ? "Esync" : "Esync (Linux only)"
                enabled: root.syncSupported
            }
            MossToggle {
                id: fsyncToggle
                text: root.syncSupported ? "Fsync" : "Fsync (Linux only)"
                enabled: root.syncSupported
            }
            Text {
                visible: !root.syncSupported
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Esync/Fsync apply on Linux/SteamOS hosts only."
                color: Theme.textMuted
                font.pixelSize: Theme.fontCaption
            }

            Text { text: "Launch profile"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            ComboBox {
                id: profileBox
                Layout.fillWidth: true
                textRole: "name"
                valueRole: "id"
                model: root.profileModel
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Profiles override args/runner/env for this game. Add profiles as JSON later or use Default."
                color: Theme.textMuted
                font.pixelSize: Theme.fontCaption
            }

            Text { text: "Environment (KEY=value per line)"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                TextArea {
                    id: envField
                    wrapMode: TextEdit.NoWrap
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSecondary
                    font.family: "monospace"
                }
            }

            Text { text: "DLL overrides (dll=n,b per line)"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 64
                TextArea {
                    id: dllField
                    wrapMode: TextEdit.NoWrap
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSecondary
                    font.family: "monospace"
                    placeholderText: "d3d11=n,b"
                }
            }

            Text { text: "Winetricks"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            RowLayout {
                Layout.fillWidth: true
                ComboBox {
                    id: verbBox
                    Layout.fillWidth: true
                    textRole: "label"
                    valueRole: "id"
                    model: root.winetricksVerbs
                }
                MossSecondaryButton {
                    text: "Run"
                    enabled: !!(verbBox.currentValue)
                    onClicked: {
                        if (verbBox.currentValue)
                            moss.runWinetricksVerb(root.gameId, verbBox.currentValue)
                    }
                }
            }

            MossToggle {
                id: favToggle
                text: "Favorite"
            }
        }
    }

    onAccepted: {
        moss.saveGameConfig({
            gameId: root.gameId,
            name: nameField.text,
            exe: exeField.text,
            workingDir: cwdField.text,
            launchArgs: argsField.text,
            envVars: envField.text,
            dllOverrides: dllField.text,
            runnerId: runnerBox.currentValue || "",
            windowsVersion: winBox.currentValue || "",
            favorite: favToggle.checked,
            dxvkEnabled: dxvkToggle.checked,
            vkd3dEnabled: vkd3dToggle.checked,
            gamescopeEnabled: gamescopeToggle.checked,
            gamescopeArgs: gamescopeArgsField.text,
            mangohudEnabled: mangohudToggle.checked,
            gamemodeEnabled: gamemodeToggle.checked,
            esyncEnabled: esyncToggle.checked,
            fsyncEnabled: fsyncToggle.checked,
            activeProfileId: profileBox.currentValue || ""
        })
    }

    function openFor(gid) {
        root.gameId = gid
        var cfg = moss.getGameConfig(gid)
        var listed = moss.listRuntimes() || []
        var opts = [{ id: "", label: "Default (Settings)" }]
        for (var i = 0; i < listed.length; i++) {
            opts.push({
                id: listed[i].id,
                label: listed[i].name + " · " + listed[i].kind
            })
        }
        root.runtimes = opts
        root.winetricksVerbs = moss.listWinetricksVerbs(gid) || []
        root.hostTools = moss.hostTools() || {}
        root.syncSupported = !!cfg.syncSupported

        var profiles = [{ id: "", name: "Default" }]
        var rawProfiles = cfg.launchProfiles || []
        for (var p = 0; p < rawProfiles.length; p++) {
            profiles.push({
                id: rawProfiles[p].id,
                name: rawProfiles[p].name || rawProfiles[p].id
            })
        }
        root.profileModel = profiles

        nameField.text = cfg.name || ""
        exeField.text = cfg.exe || ""
        cwdField.text = cfg.workingDir || ""
        argsField.text = cfg.launchArgs || ""
        envField.text = cfg.envVars || ""
        dllField.text = cfg.dllOverrides || ""
        favToggle.checked = !!cfg.favorite
        dxvkToggle.checked = cfg.dxvkEnabled !== false
        vkd3dToggle.checked = cfg.vkd3dEnabled !== false
        gamescopeToggle.checked = !!cfg.gamescopeEnabled
        gamescopeArgsField.text = cfg.gamescopeArgs || ""
        mangohudToggle.checked = !!cfg.mangohudEnabled
        gamemodeToggle.checked = !!cfg.gamemodeEnabled
        esyncToggle.checked = cfg.esyncEnabled !== false
        fsyncToggle.checked = cfg.fsyncEnabled !== false

        var wantRunner = cfg.runnerId || ""
        runnerBox.currentIndex = 0
        for (var r = 0; r < opts.length; r++) {
            if (opts[r].id === wantRunner)
                runnerBox.currentIndex = r
        }

        var wantWin = cfg.windowsVersion || ""
        winBox.currentIndex = 0
        for (var w = 0; w < winBox.model.length; w++) {
            if (winBox.model[w].id === wantWin)
                winBox.currentIndex = w
        }

        var wantProfile = cfg.activeProfileId || ""
        profileBox.currentIndex = 0
        for (var pr = 0; pr < profiles.length; pr++) {
            if (profiles[pr].id === wantProfile)
                profileBox.currentIndex = pr
        }
        root.open()
    }

    FileDialog {
        id: exeDlg
        title: "Executable"
        nameFilters: ["Executables (*.exe)", "All files (*)"]
        onAccepted: exeField.text = moss.localPath(selectedFile)
    }
    FolderDialog {
        id: cwdDlg
        title: "Working directory"
        onAccepted: cwdField.text = moss.localPath(selectedFolder)
    }
}
