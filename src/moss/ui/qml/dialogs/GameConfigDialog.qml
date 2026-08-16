import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."

Dialog {
    id: root
    modal: true
    anchors.centerIn: Overlay.overlay
    width: Math.min(520, parent ? parent.width - 48 : 520)
    title: "Game settings"
    standardButtons: Dialog.Save | Dialog.Cancel
    property string gameId: ""

    background: Rectangle {
        color: Theme.panelFill
        border.width: 1
        border.color: Theme.border
        radius: Theme.radiusLarge
    }

    function fieldBg() {
        return Theme.surface
    }

    ColumnLayout {
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

        Text { text: "Environment (KEY=value per line)"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
        ScrollView {
            Layout.fillWidth: true
            Layout.preferredHeight: 110
            TextArea {
                id: envField
                wrapMode: TextEdit.NoWrap
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSecondary
                font.family: "monospace"
            }
        }

        MossToggle {
            id: favToggle
            text: "Favorite"
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
            favorite: favToggle.checked
        })
    }

    function openFor(gid) {
        root.gameId = gid
        var cfg = moss.getGameConfig(gid)
        nameField.text = cfg.name || ""
        exeField.text = cfg.exe || ""
        cwdField.text = cfg.workingDir || ""
        argsField.text = cfg.launchArgs || ""
        envField.text = cfg.envVars || ""
        favToggle.checked = !!cfg.favorite
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
