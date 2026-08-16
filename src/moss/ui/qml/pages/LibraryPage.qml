import QtQuick
import QtQuick.Controls
import ".."

Item {
    id: root

    Text {
        id: heading
        text: "Library"
        color: Theme.textPrimary
        font.pixelSize: Theme.fontPageTitle
        font.weight: Font.Normal
        anchors.top: parent.top
        anchors.left: parent.left
    }

    Text {
        id: sub
        text: "Your Games"
        color: Theme.textMuted
        font.pixelSize: Theme.fontCaption
        anchors.top: heading.bottom
        anchors.left: parent.left
        anchors.topMargin: Theme.space4
    }

    MossSearchField {
        id: search
        anchors.top: parent.top
        anchors.right: parent.right
        onTextChanged: moss.setSearch(text)
    }

    // Empty state — left-of-center in content, not giant centered art
    Item {
        anchors.top: sub.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.topMargin: Theme.space32
        visible: moss.isEmpty

        Column {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: -40
            spacing: Theme.space12
            width: Math.min(420, parent.width - 40)

            Text {
                text: "No games in your library"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSection
                font.weight: Font.DemiBold
            }
            Text {
                width: parent.width
                wrapMode: Text.WordWrap
                text: "Add a Windows game folder, executable, or installer."
                color: Theme.textSecondary
                font.pixelSize: Theme.fontBody
            }
        }
    }

    GridView {
        id: grid
        visible: !moss.isEmpty
        anchors.top: sub.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.topMargin: Theme.space24
        clip: true
        cellWidth: 164
        cellHeight: 248
        model: games
        delegate: MossGameCard {
            name: model.name
            cover: model.cover
            status: model.status
            letter: model.letter
            onClicked: moss.openGame(model.gameId)
        }
    }
}
