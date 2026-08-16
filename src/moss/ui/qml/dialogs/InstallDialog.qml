import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import ".."

Dialog {
    id: root
    title: "Install Windows Game"
    modal: true
    width: 500
    height: 360
    standardButtons: Dialog.Ok | Dialog.Cancel
    onAccepted: moss.installSetup(setupPath.text, gameName.text)

    background: Rectangle {
        color: Theme.dialogPanelFill
        border.width: 1
        border.color: Theme.border
        radius: Theme.radiusLarge
    }

    Column {
        anchors.fill: parent
        anchors.margins: Theme.space16
        spacing: Theme.space16

        // Compact stepper
        Row {
            spacing: Theme.space12
            Repeater {
                model: ["01 Installer", "02 Name", "03 Finish"]
                Text {
                    text: modelData
                    color: index === 0 ? Theme.accent : Theme.textMuted
                    font.pixelSize: Theme.fontCaption
                    font.weight: index === 0 ? Font.DemiBold : Font.Normal
                }
            }
        }

        Rectangle { width: parent.width; height: 1; color: Theme.divider }

        Text {
            text: "Select installer"
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSection
            font.weight: Font.DemiBold
        }
        TextField {
            id: setupPath
            width: parent.width
            placeholderText: "setup.exe"
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSecondary
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.surface
                border.width: 1
                border.color: Theme.border
            }
        }
        MossSecondaryButton { text: "Choose file"; onClicked: fileDlg.open() }

        Text {
            text: "Game name"
            color: Theme.textMuted
            font.pixelSize: Theme.fontCaption
        }
        TextField {
            id: gameName
            width: parent.width
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSecondary
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.surface
                border.width: 1
                border.color: Theme.border
            }
        }
    }

    FileDialog {
        id: fileDlg
        title: "Windows installer"
        nameFilters: ["Executables (*.exe)"]
        onAccepted: setupPath.text = moss.localPath(selectedFile)
    }
}
