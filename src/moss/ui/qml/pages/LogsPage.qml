import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Item {
    property string logText: ""
    property string filter: "all"

    ColumnLayout {
        anchors.fill: parent
        spacing: Theme.space12

        RowLayout {
            MossSecondaryButton { text: "Library"; onClicked: moss.backToLibrary() }
            Text {
                text: "Logs"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSection
                font.weight: Font.DemiBold
                Layout.leftMargin: Theme.space8
            }
            Item { Layout.fillWidth: true }
            Repeater {
                model: [
                    { label: "All", key: "all" },
                    { label: "Info", key: "info" },
                    { label: "Warning", key: "warn" },
                    { label: "Error", key: "err" }
                ]
                delegate: Button {
                    text: modelData.label
                    flat: true
                    font.pixelSize: Theme.fontCaption
                    contentItem: Text {
                        text: parent.text
                        color: filter === modelData.key ? Theme.accent : Theme.textMuted
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                    }
                    background: Item {
                        Rectangle {
                            anchors.bottom: parent.bottom
                            width: parent.width
                            height: 1
                            color: filter === modelData.key ? Theme.accent : "transparent"
                        }
                    }
                    onClicked: filter = modelData.key
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            TextArea {
                readOnly: true
                wrapMode: TextEdit.Wrap
                font.family: "Cascadia Mono"
                font.pixelSize: Theme.fontCaption
                color: Theme.textPrimary
                text: {
                    var src = logText
                    if (filter === "all") return src
                    var lines = src.split("\n")
                    if (filter === "err")
                        return lines.filter(function (l) { return l.toLowerCase().indexOf("err") >= 0 }).join("\n")
                    if (filter === "warn")
                        return lines.filter(function (l) {
                            var t = l.toLowerCase()
                            return t.indexOf("warn") >= 0 || t.indexOf("fixme") >= 0
                        }).join("\n")
                    return lines.filter(function (l) {
                        var t = l.toLowerCase()
                        return t.indexOf("info") >= 0 || t.indexOf("fix") >= 0
                    }).join("\n")
                }
                background: Rectangle {
                    color: Theme.backgroundDeep
                    border.width: 1
                    border.color: Theme.border
                    radius: Theme.radiusSmall
                }
            }
        }
    }
}
