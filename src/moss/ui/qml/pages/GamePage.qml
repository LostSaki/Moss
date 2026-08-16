import QtQuick
import QtQuick.Controls
import ".."

Item {
    id: root

    MossSecondaryButton {
        id: back
        text: "Library"
        anchors.top: parent.top
        anchors.left: parent.left
        onClicked: moss.backToLibrary()
    }

    // Hero — asymmetric: title + Play bottom-left
    Rectangle {
        id: hero
        anchors.top: back.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: Theme.space12
        height: 220
        radius: Theme.radiusHero
        color: Theme.surface
        clip: true

        Image {
            anchors.fill: parent
            source: moss.current.cover || ""
            fillMode: Image.PreserveAspectCrop
            opacity: 0.88
        }

        // Dark overlay for readability — not a decorative gradient wash
        Rectangle {
            anchors.fill: parent
            color: "#990C0D0C"
        }

        Text {
            visible: !(moss.current.cover)
            anchors.centerIn: parent
            text: moss.current.letter || "M"
            color: Theme.textPrimary
            font.pixelSize: 48
            font.weight: Font.Light
        }

        Column {
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.margins: Theme.space20
            spacing: Theme.space8

            Text {
                text: moss.current.name || ""
                color: Theme.textPrimary
                font.pixelSize: Theme.fontPageTitle
                font.weight: Font.Medium
            }
            Text {
                text: "Windows  ·  " + (moss.current.runtime || "none") + "  ·  " + (moss.current.status || "")
                color: Theme.textSecondary
                font.pixelSize: Theme.fontSecondary
            }
            Row {
                spacing: Theme.space8
                topPadding: Theme.space4
                MossButton {
                    text: moss.busy ? "Running" : "Play"
                    enabled: !moss.busy
                    onClicked: moss.play(moss.current.gameId)
                }
                MossSecondaryButton {
                    text: "More"
                    onClicked: moreMenu.open()
                    Menu {
                        id: moreMenu
                        MenuItem { text: "View Logs"; onTriggered: moss.loadLog(moss.current.gameId) }
                        MenuItem { text: "Open Prefix"; onTriggered: moss.openPrefix(moss.current.prefix) }
                        MenuItem {
                            text: moss.current.favorite ? "Remove Favorite" : "Add to Favorites"
                            onTriggered: moss.toggleFavorite(moss.current.gameId)
                        }
                        MenuSeparator {}
                        MenuItem { text: "Remove Game"; onTriggered: confirm.open() }
                    }
                }
            }
        }
    }

    // Specs as divider list — not a card stack
    Column {
        anchors.top: hero.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: Theme.space24
        spacing: 0

        Repeater {
            model: [
                { k: "Status", v: moss.current.status || "" },
                { k: "Runtime", v: moss.current.runtime || "" },
                { k: "Components", v: moss.current.verbs || "" },
                { k: "Last played", v: moss.current.lastPlayed || "—" }
            ]
            delegate: Column {
                width: parent.width
                spacing: 0
                Rectangle { width: parent.width; height: 1; color: Theme.divider }
                Row {
                    width: parent.width
                    height: 40
                    Text {
                        width: 120
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.k
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontCaption
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.v
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSecondary
                        elide: Text.ElideMiddle
                        width: parent.width - 120
                    }
                }
            }
        }
        Rectangle { width: parent.width; height: 1; color: Theme.divider }
    }

    ConfirmDialog {
        id: confirm
        titleText: "Remove Game"
        message: "Remove this game from Moss? Files on disk stay unless you remove the prefix."
        onAccepted: moss.removeGame(moss.current.gameId, false)
    }
}
