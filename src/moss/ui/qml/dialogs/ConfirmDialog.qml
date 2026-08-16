import QtQuick
import QtQuick.Controls
import ".."

Dialog {
    id: root
    property string titleText: "Confirm"
    property string message: ""
    property string confirmLabel: "OK"
    property string cancelLabel: "Cancel"
    title: titleText
    modal: true
    standardButtons: Dialog.NoButton
    width: 420

    background: Rectangle {
        color: Theme.dialogPanelFill
        border.width: 1
        border.color: Theme.border
        radius: Theme.radiusLarge
    }

    contentItem: Column {
        width: parent.width
        spacing: Theme.space16
        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            text: root.message
            color: Theme.textSecondary
            font.pixelSize: Theme.fontSecondary
        }
        Row {
            anchors.right: parent.right
            spacing: Theme.space8
            MossSecondaryButton {
                text: root.cancelLabel
                onClicked: root.reject()
            }
            MossButton {
                text: root.confirmLabel
                onClicked: root.accept()
            }
        }
    }
}
