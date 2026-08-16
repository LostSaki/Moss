import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: root
    implicitHeight: 36
    leftPadding: 12
    rightPadding: 12
    font.pixelSize: Theme.fontSecondary

    background: Rectangle {
        radius: Theme.radiusSmall
        color: root.down ? Theme.surfaceSelected
             : root.hovered ? Theme.surfaceHover
             : "transparent"
        border.width: root.activeFocus ? 1 : 0
        border.color: Theme.borderStrong
        Behavior on color { ColorAnimation { duration: Theme.durationFast } }
    }
    contentItem: Text {
        text: root.text
        color: root.enabled ? Theme.textSecondary : Theme.textDisabled
        font: root.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
