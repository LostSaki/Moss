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
    height: Math.min(620, parent ? parent.height - 48 : 620)
    title: "Game settings"
    standardButtons: Dialog.Save | Dialog.Cancel
    property string gameId: ""
    property var runtimes: []

    background: Rectangle {
        color: Theme.panelFill
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
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: root.runtimes.length <= 1
                      ? "No local Proton/Wine detected — using system default when available."
                      : "Per-game runner overrides Settings default."
                color: Theme.textMuted
                font.pixelSize: Theme.fontCaption
            }

            Text { text: "Windows version (stored; winecfg apply later)"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
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

            Text { text: "Environment (KEY=value per line)"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 88
                TextArea {
                    id: envField
                    wrapMode: TextEdit.NoWrap
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSecondary
                    font.family: "monospace"
                }
            }

            Text { text: "DLL overrides (dll=n,b per line → WINEDLLOVERRIDES)"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                TextArea {
                    id: dllField
                    wrapMode: TextEdit.NoWrap
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSecondary
                    font.family: "monospace"
                    placeholderText: "d3d11=n,b"
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
            favorite: favToggle.checked
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

        nameField.text = cfg.name || ""
        exeField.text = cfg.exe || ""
        cwdField.text = cfg.workingDir || ""
        argsField.text = cfg.launchArgs || ""
        envField.text = cfg.envVars || ""
        dllField.text = cfg.dllOverrides || ""
        favToggle.checked = !!cfg.favorite

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
