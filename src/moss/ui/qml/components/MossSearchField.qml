import QtQuick
import QtQuick.Controls
import ".."

TextField {
    id: root
    implicitHeight: 34
    implicitWidth: Theme.searchWidth
    placeholderText: "Search games"
    color: Theme.textPrimary
    placeholderTextColor: Theme.textMuted
    font.pixelSize: Theme.fontSecondary
    leftPadding: 12
    rightPadding: 12
    selectByMouse: true

    background: Rectangle {
        radius: Theme.radiusSmall
        color: Theme.surface
        border.width: 1
        border.color: root.activeFocus ? Theme.borderStrong : Theme.border
    }
}
