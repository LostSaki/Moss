import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Dialog {
    id: root
    title: "Import games"
    modal: true
    standardButtons: Dialog.NoButton
    width: 460
    height: Math.min(520, implicitHeight)

    property var candidates: []

    function openWith(rows) {
        var list = []
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i]
            list.push({
                id: row.id || "",
                name: row.name || "",
                exe: row.exe || "",
                folder: row.folder || "",
                selected: true
            })
        }
        candidates = list
        open()
    }

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.durationNormal; easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; from: 0.98; to: 1; duration: Theme.durationNormal; easing.type: Easing.OutCubic }
        }
    }

    background: Rectangle {
        color: Theme.dialogPanelFill
        border.width: 1
        border.color: Theme.border
        radius: Theme.radiusLarge
    }

    contentItem: ColumnLayout {
        spacing: Theme.space16
        width: parent.width

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Moss found " + root.candidates.length + " games. Choose which to add."
            color: Theme.textSecondary
            font.pixelSize: Theme.fontSecondary
        }

        ListView {
            id: list
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(280, root.candidates.length * 40)
            clip: true
            model: root.candidates
            spacing: 4
            delegate: RowLayout {
                width: list.width
                spacing: Theme.space8
                CheckBox {
                    checked: modelData.selected
                    onToggled: {
                        var copy = root.candidates.slice()
                        copy[index] = {
                            id: modelData.id,
                            name: modelData.name,
                            exe: modelData.exe,
                            folder: modelData.folder,
                            selected: checked
                        }
                        root.candidates = copy
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: modelData.name
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSecondary
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                    Text {
                        text: modelData.folder
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontCaption
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            MossSecondaryButton {
                text: "Select all"
                onClicked: {
                    var copy = []
                    for (var i = 0; i < root.candidates.length; i++) {
                        var r = root.candidates[i]
                        copy.push({ id: r.id, name: r.name, exe: r.exe, folder: r.folder, selected: true })
                    }
                    root.candidates = copy
                }
            }
            MossSecondaryButton {
                text: "Select none"
                onClicked: {
                    var copy = []
                    for (var i = 0; i < root.candidates.length; i++) {
                        var r = root.candidates[i]
                        copy.push({ id: r.id, name: r.name, exe: r.exe, folder: r.folder, selected: false })
                    }
                    root.candidates = copy
                }
            }
            Item { Layout.fillWidth: true }
            MossSecondaryButton {
                text: "Cancel"
                onClicked: root.reject()
            }
            MossButton {
                text: "Import"
                onClicked: {
                    var selected = []
                    for (var i = 0; i < root.candidates.length; i++) {
                        var r = root.candidates[i]
                        if (r.selected)
                            selected.push({ id: r.id, name: r.name, exe: r.exe, folder: r.folder })
                    }
                    moss.importDiscovered(JSON.stringify(selected))
                    root.accept()
                }
            }
        }
    }
}
