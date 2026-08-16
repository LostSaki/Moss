import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."

Flickable {
    id: root
    clip: true
    contentWidth: width
    contentHeight: col.height + Theme.space40

    property var cfg: ({})

    Component.onCompleted: cfg = moss.loadSettings()

    function fieldBg(focus) {
        return focus ? Theme.surfaceHover : Theme.surface
    }

    Column {
        id: col
        width: parent.width - 8
        spacing: Theme.space32

        Text {
            text: "Settings"
            color: Theme.textPrimary
            font.pixelSize: Theme.fontPageTitle
        }

        MossSection {
            title: "General"
            description: "Where Moss looks when adding games."
            RowLayout {
                width: parent.width
                spacing: Theme.space8
                TextField {
                    id: gamesFolder
                    Layout.fillWidth: true
                    text: cfg.games_folder || ""
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSecondary
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.border
                    }
                }
                MossSecondaryButton {
                    text: "Browse"
                    onClicked: folderDlg.open()
                }
            }
        }

        MossSection {
            title: "Runtime"
            description: "Preferred Proton, then Wine."
            Column {
                width: parent.width
                spacing: Theme.space8
                Text { text: "Proton path"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
                TextField {
                    id: protonPath
                    width: parent.width
                    text: cfg.proton_path || ""
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSecondary
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.border
                    }
                }
                Text { text: "Wine path"; color: Theme.textMuted; font.pixelSize: Theme.fontCaption }
                TextField {
                    id: winePath
                    width: parent.width
                    text: cfg.wine_path || ""
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSecondary
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.border
                    }
                }
            }
        }

        MossSection {
            title: "Artwork"
            description: "SteamGridDB API key for covers."
            TextField {
                id: apiKey
                width: parent.width
                echoMode: TextInput.Password
                text: cfg.steamgriddb_api_key || ""
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSecondary
                background: Rectangle {
                    radius: Theme.radiusSmall
                    color: Theme.surface
                    border.width: 1
                    border.color: Theme.border
                }
            }
        }

        MossSection {
            title: "Steam"
            description: "Write non-Steam shortcuts and grid art."
            MossToggle {
                id: steamOn
                checked: cfg.create_steam_shortcuts !== false
                text: "Create Steam Shortcuts"
            }
        }

        MossSection {
            title: "Updates"
            description: "Automatically check for new Moss releases."
            MossToggle {
                id: updatesOn
                checked: cfg.check_updates !== false
                text: "Check for Updates"
            }
        }

        MossSection {
            title: "Advanced"
            description: "Library, prefixes, and logs."
            Row {
                spacing: Theme.space8
                MossSecondaryButton { text: "Open data folder"; onClicked: moss.openDataDir() }
                MossSecondaryButton { text: "GitHub"; onClicked: moss.openGithub() }
            }
        }

        MossButton {
            text: "Save"
            onClicked: moss.saveSettings({
                games_folder: gamesFolder.text,
                proton_path: protonPath.text,
                wine_path: winePath.text,
                steamgriddb_api_key: apiKey.text,
                create_steam_shortcuts: steamOn.checked,
                check_updates: updatesOn.checked
            })
        }
    }

    FolderDialog {
        id: folderDlg
        title: "Games folder"
        onAccepted: gamesFolder.text = moss.localPath(selectedFolder)
    }
}
