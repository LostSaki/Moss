import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: root
    implicitHeight: Theme.playHeight
    leftPadding: 18
    rightPadding: 18
    font.pixelSize: Theme.fontBody
    font.weight: Font.DemiBold
    enabled: true

    background: Rectangle {
        radius: Theme.radiusMedium
        color: !root.enabled ? Theme.surfaceHover
             : root.down ? Theme.accentPressed
             : root.hovered ? Theme.accentHover
             : Theme.accent
        border.width: root.activeFocus ? 1 : 0
        border.color: Theme.textPrimary
        Behavior on color { ColorAnimation { duration: Theme.durationFast } }
    }
    contentItem: Text {
        text: root.text
        color: root.enabled ? Theme.backgroundDeep : Theme.textDisabled
        font: root.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
