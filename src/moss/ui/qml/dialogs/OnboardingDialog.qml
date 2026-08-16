import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import ".."

Dialog {
    id: root
    modal: true
    anchors.centerIn: Overlay.overlay
    width: Math.min(520, parent ? parent.width - 48 : 520)
    height: Math.min(560, parent ? parent.height - 48 : 560)
    padding: 0
    closePolicy: Popup.NoAutoClose

    property int step: 0
    property int stepCount: 5
    property string gamesFolder: ""
    property string preferredRuntime: "auto"
    property string apiKey: ""
    property bool glassOn: false
    property string themeId: "moss_dark"

    opacity: 0
    scale: 0.98

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 160; easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; from: 0.98; to: 1; duration: 160; easing.type: Easing.OutCubic }
        }
    }

    background: Rectangle {
        color: Theme.panelFill
        border.width: 1
        border.color: Theme.border
        radius: Theme.radiusLarge
    }

    header: Item {
        height: 64
        width: root.width
        Column {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: Theme.space24
            spacing: 4
            Text {
                text: "Welcome to Moss"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSection
                font.weight: Font.DemiBold
            }
            Text {
                text: "Step " + (root.step + 1) + " of " + root.stepCount
                color: Theme.textMuted
                font.pixelSize: Theme.fontCaption
            }
        }
    }

    contentItem: Item {
        implicitHeight: 380

        StackLayout {
            anchors.fill: parent
            anchors.margins: Theme.space24
            currentIndex: root.step

            // 0 — Games folder
            Column {
                spacing: Theme.space12
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Where should Moss look for games?"
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontBody
                }
                RowLayout {
                    width: parent.width
                    spacing: Theme.space8
                    TextField {
                        id: folderField
                        Layout.fillWidth: true
                        text: root.gamesFolder
                        placeholderText: "Games folder"
                        color: Theme.textPrimary
                        onTextChanged: root.gamesFolder = text
                        background: Rectangle {
                            radius: Theme.radiusSmall
                            color: Theme.surface
                            border.width: 1
                            border.color: Theme.border
                        }
                    }
                    MossSecondaryButton {
                        text: "Browse"
                        onClicked: onboardFolder.open()
                    }
                }
            }

            // 1 — Preferred runtime
            Column {
                spacing: Theme.space12
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Preferred runtime"
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontBody
                }
                Repeater {
                    model: [
                        { id: "auto", label: "Auto (Proton, then Wine)" },
                        { id: "proton", label: "Proton" },
                        { id: "wine", label: "Wine" }
                    ]
                    delegate: Button {
                        width: parent.width
                        implicitHeight: 36
                        text: modelData.label
                        background: Rectangle {
                            radius: Theme.radiusSmall
                            color: root.preferredRuntime === modelData.id ? Theme.accentSurface : Theme.surface
                            border.width: 1
                            border.color: root.preferredRuntime === modelData.id ? Theme.accent : Theme.border
                        }
                        contentItem: Text {
                            text: parent.text
                            color: Theme.textPrimary
                            font.pixelSize: Theme.fontSecondary
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: 12
                        }
                        onClicked: root.preferredRuntime = modelData.id
                    }
                }
            }

            // 2 — SteamGridDB
            Column {
                spacing: Theme.space12
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "SteamGridDB API key (optional)"
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontBody
                }
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Used for cover and hero artwork. Leave blank to skip."
                    color: Theme.textMuted
                    font.pixelSize: Theme.fontCaption
                }
                TextField {
                    width: parent.width
                    echoMode: TextInput.Password
                    text: root.apiKey
                    color: Theme.textPrimary
                    onTextChanged: root.apiKey = text
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.border
                    }
                }
            }

            // 3 — Glass
            Column {
                spacing: Theme.space12
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Glass surfaces"
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontBody
                }
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Translucent sidebar, menus, and dialogs. Game cards stay solid."
                    color: Theme.textMuted
                    font.pixelSize: Theme.fontCaption
                }
                MossToggle {
                    checked: root.glassOn
                    text: root.glassOn ? "On" : "Off"
                    onCheckedChanged: root.glassOn = checked
                }
            }

            // 4 — Theme
            Column {
                spacing: Theme.space12
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Choose a theme"
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontBody
                }
                Repeater {
                    model: moss.themes
                    delegate: Button {
                        width: parent.width
                        implicitHeight: 36
                        text: modelData.label
                        background: Rectangle {
                            radius: Theme.radiusSmall
                            color: root.themeId === modelData.id ? Theme.accentSurface : Theme.surface
                            border.width: 1
                            border.color: root.themeId === modelData.id ? Theme.accent : Theme.border
                        }
                        contentItem: Text {
                            text: parent.text
                            color: Theme.textPrimary
                            font.pixelSize: Theme.fontSecondary
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: 12
                        }
                        onClicked: {
                            root.themeId = modelData.id
                            if (modelData.id === "soft_glass" || modelData.id === "mist")
                                root.glassOn = true
                        }
                    }
                }
            }
        }
    }

    footer: Item {
        height: 64
        width: root.width
        Row {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: Theme.space24
            spacing: Theme.space8
            MossSecondaryButton {
                text: root.step === 0 ? "Skip" : "Back"
                onClicked: {
                    if (root.step === 0)
                        finish()
                    else
                        root.step -= 1
                }
            }
            MossButton {
                text: root.step === root.stepCount - 1 ? "Finish" : "Next"
                onClicked: {
                    if (root.step === root.stepCount - 1)
                        finish()
                    else
                        root.step += 1
                }
            }
        }
    }

    function finish() {
        moss.completeOnboarding({
            games_folder: root.gamesFolder,
            preferred_runtime: root.preferredRuntime,
            steamgriddb_api_key: root.apiKey,
            glass_enabled: root.glassOn,
            theme: root.themeId
        })
        root.close()
    }

    FolderDialog {
        id: onboardFolder
        title: "Games folder"
        onAccepted: {
            root.gamesFolder = moss.localPath(selectedFolder)
            folderField.text = root.gamesFolder
        }
    }

    function prepare() {
        var cfg = moss.loadSettings()
        root.gamesFolder = cfg.games_folder || ""
        root.preferredRuntime = cfg.preferred_runtime || "auto"
        root.apiKey = cfg.steamgriddb_api_key || ""
        root.glassOn = !!cfg.glass_enabled
        root.themeId = cfg.theme || "moss_dark"
        root.step = 0
    }
}
