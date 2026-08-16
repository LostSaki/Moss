import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Item {
    id: root
    width: Theme.sidebarWidth
    property string currentKey: "all"
    signal navigate(string key)
    signal addFolder()
    signal addExe()
    signal addInstall()
    signal scanLibrary()

    Rectangle {
        anchors.fill: parent
        color: Theme.panelFill
    }

    // Top edge highlight when glass is on — reads as a frosted panel
    Rectangle {
        visible: Theme.glassEnabled
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 1
        color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.35)
        z: 3
    }

    Rectangle {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 1
        color: Theme.glassEnabled
              ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.25)
              : Theme.divider
        z: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.space12
        spacing: 2
        z: 2

        Text {
            text: "Moss"
            color: Theme.textPrimary
            font.pixelSize: 20
            font.weight: Font.DemiBold
            Layout.leftMargin: Theme.space8
            Layout.topMargin: Theme.space8
            Layout.bottomMargin: Theme.space12
        }

        Text {
            text: "LIBRARY"
            color: Theme.textMuted
            font.pixelSize: Theme.fontMicro
            font.weight: Font.DemiBold
            Layout.leftMargin: Theme.space8
            Layout.topMargin: Theme.space8
        }
        MossSidebarItem { label: "All Games"; selected: currentKey === "all"; onActivated: { currentKey = "all"; navigate("all") } }
        MossSidebarItem { label: "Favorites"; selected: currentKey === "favorites"; onActivated: { currentKey = "favorites"; navigate("favorites") } }
        MossSidebarItem { label: "Recently Played"; selected: currentKey === "recent"; onActivated: { currentKey = "recent"; navigate("recent") } }

        Text {
            text: "COLLECTIONS"
            color: Theme.textMuted
            font.pixelSize: Theme.fontMicro
            font.weight: Font.DemiBold
            Layout.leftMargin: Theme.space8
            Layout.topMargin: Theme.space16
        }
        MossSidebarItem { label: "Installed"; selected: currentKey === "installed"; onActivated: { currentKey = "installed"; navigate("installed") } }
        MossSidebarItem { label: "Needs Attention"; selected: currentKey === "attention"; onActivated: { currentKey = "attention"; navigate("attention") } }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.divider
            Layout.topMargin: Theme.space12
            Layout.bottomMargin: Theme.space8
            Layout.leftMargin: Theme.space8
            Layout.rightMargin: Theme.space8
        }

        MossSidebarItem { label: "Settings"; selected: currentKey === "settings"; onActivated: { currentKey = "settings"; navigate("settings") } }

        Item { Layout.fillHeight: true }

        Button {
            id: scanBtn
            Layout.fillWidth: true
            Layout.leftMargin: Theme.space8
            Layout.rightMargin: Theme.space8
            Layout.bottomMargin: Theme.space8
            implicitHeight: 36
            enabled: !moss.scanningLibrary
            text: moss.scanningLibrary ? "Scanning…" : "Scan library"
            font.pixelSize: Theme.fontSecondary
            font.weight: Font.Medium
            ToolTip.visible: hovered
            ToolTip.delay: 400
            ToolTip.text: "Find Windows games in your library folder"
            background: Rectangle {
                radius: Theme.radiusMedium
                color: parent.down ? Theme.surfaceSelected
                     : parent.hovered ? Theme.surfaceHover
                     : "transparent"
                border.width: 1
                border.color: Theme.border
                Behavior on color { ColorAnimation { duration: Theme.durationFast } }
            }
            contentItem: Text {
                text: parent.text
                color: parent.enabled ? Theme.textSecondary : Theme.textDisabled
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font: parent.font
            }
            onClicked: root.scanLibrary()
        }

        Button {
            Layout.fillWidth: true
            Layout.leftMargin: Theme.space8
            Layout.rightMargin: Theme.space8
            implicitHeight: 36
            text: "+  Add Game"
            font.pixelSize: Theme.fontSecondary
            font.weight: Font.Medium
            background: Rectangle {
                radius: Theme.radiusMedium
                color: parent.down ? Theme.surfaceSelected
                     : parent.hovered ? Theme.surfaceHover
                     : Theme.surfaceRaised
                border.width: 1
                border.color: Theme.border
            }
            contentItem: Text {
                text: parent.text
                color: Theme.textPrimary
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font: parent.font
            }
            onClicked: addMenu.open()
            Menu {
                id: addMenu
                background: Rectangle {
                    implicitWidth: 220
                    color: Theme.panelFill
                    border.width: 1
                    border.color: Theme.border
                    radius: Theme.radiusMedium
                }
                MenuItem { text: "Add this game folder…"; onTriggered: root.addFolder() }
                MenuItem { text: "Add EXE"; onTriggered: root.addExe() }
                MenuItem { text: "Install Windows Game"; onTriggered: root.addInstall() }
            }
        }
    }
}
