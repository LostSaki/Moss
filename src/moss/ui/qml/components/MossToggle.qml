import QtQuick
import QtQuick.Controls
import ".."

Switch {
    id: root
    implicitHeight: 24
    font.pixelSize: Theme.fontSecondary

    indicator: Rectangle {
        implicitWidth: 40
        implicitHeight: 24
        x: root.leftPadding
        y: parent.height / 2 - height / 2
        radius: 12
        color: root.checked ? Theme.accent : Theme.surfaceRaised
        border.width: 1
        border.color: root.checked ? Theme.accentPressed : Theme.border

        Rectangle {
            width: 18
            height: 18
            radius: 9
            x: root.checked ? parent.width - width - 3 : 3
            y: 3
            color: Theme.textPrimary
            Behavior on x { NumberAnimation { duration: Theme.durationFast } }
        }
    }

    contentItem: Text {
        text: root.text
        font: root.font
        color: Theme.textPrimary
        verticalAlignment: Text.AlignVCenter
        leftPadding: root.indicator.width + 10
    }
}
