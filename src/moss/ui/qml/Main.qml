import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "."

ApplicationWindow {
    id: win
    visible: true
    width: 1180
    height: 740
    title: "Moss"
    color: Theme.background

    property string bannerText: ""
    property string bannerUrl: ""
    property string logBuffer: ""

    Connections {
        target: moss
        function onUpdateAvailable(message, url) {
            bannerText = message
            bannerUrl = url
        }
        function onLogReady(text) { logBuffer = text }
        function onToast(msg) {
            toastLabel.text = msg
            toast.visible = true
            toastTimer.restart()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            visible: bannerText.length > 0
            Layout.fillWidth: true
            height: 36
            color: Theme.accentSurface
            border.width: 1
            border.color: Theme.border
            Text {
                anchors.centerIn: parent
                text: bannerText
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSecondary
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: Qt.openUrlExternally(bannerUrl)
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            MossSidebar {
                Layout.fillHeight: true
                Layout.preferredWidth: Theme.sidebarWidth
                onNavigate: (key) => moss.setFilter(key)
                onAddFolder: folderDlg.open()
                onAddExe: exeDlg.open()
                onAddInstall: installDlg.open()
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                LibraryPage {
                    anchors.fill: parent
                    anchors.margins: Theme.contentMargin
                    visible: moss.page === "library"
                }
                GamePage {
                    anchors.fill: parent
                    anchors.margins: Theme.contentMargin
                    visible: moss.page === "game"
                }
                SettingsPage {
                    anchors.fill: parent
                    anchors.margins: Theme.contentMargin
                    visible: moss.page === "settings"
                }
                LogsPage {
                    anchors.fill: parent
                    anchors.margins: Theme.contentMargin
                    visible: moss.page === "logs"
                    logText: logBuffer
                }
            }
        }
    }

    FolderDialog {
        id: folderDlg
        title: "Add game folder"
        onAccepted: moss.addFolder(moss.localPath(selectedFolder))
    }
    FileDialog {
        id: exeDlg
        title: "Add EXE"
        nameFilters: ["Executables (*.exe)"]
        onAccepted: moss.addExe(moss.localPath(selectedFile))
    }
    InstallDialog { id: installDlg }

    Rectangle {
        id: toast
        visible: false
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: Theme.space24
        radius: Theme.radiusMedium
        color: Theme.surfaceRaised
        border.width: 1
        border.color: Theme.border
        width: toastLabel.implicitWidth + 24
        height: 36
        Text {
            id: toastLabel
            anchors.centerIn: parent
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSecondary
        }
    }
    Timer {
        id: toastTimer
        interval: 2200
        onTriggered: toast.visible = false
    }
}
