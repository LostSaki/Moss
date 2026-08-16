import QtQuick
import ".."

Column {
    id: root
    property string title
    property string description
    default property alias content: body.data
    spacing: Theme.space8
    width: parent ? parent.width : 400

    Text {
        text: root.title
        color: Theme.textPrimary
        font.pixelSize: Theme.fontSection
        font.weight: Font.DemiBold
    }
    Text {
        text: root.description
        color: Theme.textMuted
        font.pixelSize: Theme.fontCaption
        wrapMode: Text.WordWrap
        width: parent.width
        visible: root.description.length > 0
    }
    Rectangle {
        width: parent.width
        height: 1
        color: Theme.divider
    }
    Item {
        id: body
        width: parent.width
        height: childrenRect.height
    }
}
