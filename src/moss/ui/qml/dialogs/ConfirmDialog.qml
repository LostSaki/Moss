import QtQuick
import QtQuick.Controls
import ".."

Dialog {
    id: root
    property string titleText: "Confirm"
    property string message: ""
    title: titleText
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    width: 400

    background: Rectangle {
        color: Theme.backgroundElevated
        border.width: 1
        border.color: Theme.border
        radius: Theme.radiusLarge
    }

    Text {
        width: parent.width
        wrapMode: Text.WordWrap
        text: root.message
        color: Theme.textSecondary
        font.pixelSize: Theme.fontSecondary
    }
}
