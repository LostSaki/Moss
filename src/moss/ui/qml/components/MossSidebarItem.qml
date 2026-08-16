import QtQuick
import ".."

Item {
    id: root
    property string label: ""
    property bool selected: false
    signal activated()

    height: Theme.navItemHeight
    width: parent ? parent.width : 200

    Rectangle {
        id: bg
        anchors.fill: parent
        anchors.leftMargin: Theme.space8
        anchors.rightMargin: Theme.space8
        radius: Theme.radiusMedium
        color: root.selected ? Theme.surfaceSelected
             : (hover.hovered ? Theme.surfaceHover : "transparent")
        Behavior on color { ColorAnimation { duration: Theme.durationFast } }
    }

    // Accent rail — selected only
    Rectangle {
        anchors.left: bg.left
        anchors.top: bg.top
        anchors.bottom: bg.bottom
        anchors.topMargin: 6
        anchors.bottomMargin: 6
        width: root.selected ? 3 : 0
        radius: 1
        color: Theme.accent
        Behavior on width { NumberAnimation { duration: Theme.durationFast } }
    }

    Text {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 20
        text: root.label
        color: root.selected ? Theme.textPrimary : Theme.textSecondary
        font.pixelSize: Theme.fontSecondary
        font.weight: root.selected ? Font.Medium : Font.Normal
    }

    HoverHandler { id: hover }
    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.activated()
    }
}
