import QtQuick
import ".."

Item {
    id: root
    property string name
    property string cover
    property string status
    property string letter: "M"
    property bool selected: false
    signal clicked()

    width: 148
    height: 236
    opacity: 0

    Component.onCompleted: enterFade.start()

    NumberAnimation {
        id: enterFade
        target: root
        property: "opacity"
        to: 1
        duration: Theme.durationNormal
        easing.type: Easing.OutCubic
    }

    Column {
        anchors.fill: parent
        spacing: Theme.space8

        Rectangle {
            id: artFrame
            width: 148
            height: 198
            radius: Theme.radiusLarge
            color: Theme.surface
            border.width: root.selected ? 1 : 0
            border.color: Theme.accent
            clip: true

            Image {
                anchors.fill: parent
                source: root.cover
                fillMode: Image.PreserveAspectCrop
                visible: root.cover.length > 0
                opacity: hover.hovered ? 1.0 : 0.92
                Behavior on opacity { NumberAnimation { duration: Theme.durationFast } }
            }
            Text {
                anchors.centerIn: parent
                visible: root.cover.length === 0
                text: root.letter
                color: Theme.textPrimary
                font.pixelSize: 32
                font.weight: Font.Light
            }
        }

        Text {
            width: parent.width
            text: root.name
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSecondary
            font.weight: Font.Medium
            elide: Text.ElideRight
        }

        MossStatusIndicator { status: root.status }
    }

    HoverHandler { id: hover }
    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
