import QtQuick
import ".."

Row {
    id: root
    property string status: "Ready"
    spacing: 6

    Rectangle {
        width: 6
        height: 6
        radius: 3
        anchors.verticalCenter: parent.verticalCenter
        color: root.status === "Ready" ? Theme.success
             : (root.status.indexOf("Error") >= 0 || root.status.indexOf("Missing") >= 0) ? Theme.error
             : Theme.warning
    }
    Text {
        text: root.status
        color: Theme.textSecondary
        font.pixelSize: Theme.fontCaption
        anchors.verticalCenter: parent.verticalCenter
    }
}
