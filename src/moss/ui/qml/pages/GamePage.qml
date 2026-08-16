import QtQuick
import QtQuick.Controls
import ".."

Item {
    id: root
    signal editConfig()

    MossSecondaryButton {
        id: back
        text: "Library"
        anchors.top: parent.top
        anchors.left: parent.left
        onClicked: moss.backToLibrary()
    }

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
                Item { width: 1; height: Theme.space4 }
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
                        background: Rectangle {
                            implicitWidth: 200
                            color: Theme.panelFill
                            border.width: 1
                            border.color: Theme.border
                            radius: Theme.radiusMedium
                        }
                        MenuItem { text: "Configure…"; onTriggered: root.editConfig() }
                        MenuItem { text: "View Logs"; onTriggered: moss.loadLog(moss.current.gameId) }
                        MenuItem { text: "Open Prefix"; onTriggered: moss.openGamePrefix(moss.current.gameId) }
                        MenuItem {
                            text: "Backup Prefix"
                            enabled: !!moss.current.canBackupPrefix
                            onTriggered: moss.backupGamePrefix(moss.current.gameId)
                        }
                        MenuItem {
                            text: "Delete Prefix…"
                            enabled: !!moss.current.canDeletePrefix
                            onTriggered: deletePrefixConfirm.open()
                        }
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

    Column {
        anchors.top: hero.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: Theme.space24
        spacing: 0

        Rectangle {
            visible: !!(moss.current.antiCheatHint)
            width: parent.width
            height: antiCol.implicitHeight + Theme.space16
            radius: Theme.radiusMedium
            color: Theme.accentSurface
            border.width: 1
            border.color: Theme.border
            Column {
                id: antiCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.margins: Theme.space12
                spacing: Theme.space4
                Text {
                    text: "Anti-cheat"
                    color: Theme.warning
                    font.pixelSize: Theme.fontCaption
                    font.weight: Font.DemiBold
                }
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: moss.current.antiCheatHint || ""
                    color: Theme.textSecondary
                    font.pixelSize: Theme.fontSecondary
                }
            }
        }
        Item { visible: !!(moss.current.antiCheatHint); width: 1; height: Theme.space16 }

        Repeater {
            model: [
                { k: "Status", v: moss.current.status || "" },
                { k: "Runner", v: moss.current.runtime || "" },
                { k: "Executable", v: moss.current.exe || "" },
                { k: "Working dir", v: moss.current.workingDir || "—" },
                { k: "Launch args", v: moss.current.launchArgs || "—" },
                { k: "Windows ver.", v: moss.current.windowsVersion || "default" },
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

        Item { width: 1; height: Theme.space16 }
        Row {
            spacing: Theme.space8
            MossSecondaryButton {
                text: "Advanced configuration"
                onClicked: root.editConfig()
            }
            MossSecondaryButton {
                text: "Backup prefix"
                enabled: !!moss.current.canBackupPrefix
                onClicked: moss.backupGamePrefix(moss.current.gameId)
            }
        }
        Text {
            visible: !moss.current.canBackupPrefix
            text: "Prefix backup available after the first launch creates a prefix."
            color: Theme.textMuted
            font.pixelSize: Theme.fontCaption
        }
    }

    ConfirmDialog {
        id: confirm
        titleText: "Remove Game"
        message: "Remove this game from Moss? Files on disk stay unless you remove the prefix."
        onAccepted: moss.removeGame(moss.current.gameId, false)
    }

    ConfirmDialog {
        id: deletePrefixConfirm
        titleText: "Delete Prefix"
        message: "Permanently delete this game's Wine/Proton prefix? Saves inside the prefix will be lost unless you backed up first."
        onAccepted: moss.deleteGamePrefix(moss.current.gameId)
    }
}
