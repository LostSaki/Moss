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
    color: Theme.windowFill

    property string bannerText: ""
    property string bannerUrl: ""
    property string logBuffer: ""
    property string antiCheatMessage: ""

    Component.onCompleted: {
        Theme.syncFromController(moss)
        if (!moss.onboardingComplete) {
            onboarding.prepare()
            onboarding.open()
        }
    }

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
        function onThemeChanged() { Theme.syncFromController(moss) }
        function onGlassChanged() { Theme.setGlass(moss.glassEnabled) }
        function onAntiCheatBlocked(message, log) {
            antiCheatMessage = message || "This title uses unsupported anti-cheat."
            logBuffer = log || ""
            antiCheatDialog.open()
        }
        function onOnboardingChanged() {
            if (!moss.onboardingComplete && !onboarding.visible) {
                onboarding.prepare()
                onboarding.open()
            }
        }
        function onLaunchFailed(title, detail, canFix, recipeId, gameId) {
            failTitle.text = title || "Launch failed"
            failDetail.text = detail || ""
            failApply.visible = !!canFix
            failDialog.gameId = gameId || ""
            failDialog.recipeId = recipeId || ""
            failDialog.open()
        }
        function onRunningChanged() { }
    }

    // Full-window botanical wash (visible through translucent sidebar when glass is on)
    Item {
        anchors.fill: parent
        z: -1
        visible: Theme.glassEnabled
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: Theme.glassWash }
                GradientStop { position: 0.45; color: Theme.glassWashAccent }
                GradientStop { position: 1.0; color: Theme.backgroundDeep }
            }
        }
        // Soft radial-ish accent blob behind sidebar edge
        Rectangle {
            width: Theme.sidebarWidth + 80
            height: parent.height * 0.55
            x: -20
            y: parent.height * 0.15
            radius: 120
            color: Theme.glassWashAccent
            opacity: 0.9
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        z: 1

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

                // Opaque content plate — glass only affects sidebar/menus/dialogs
                Rectangle {
                    anchors.fill: parent
                    color: Theme.background
                    opacity: 1.0
                }

                LibraryPage {
                    anchors.fill: parent
                    anchors.margins: Theme.contentMargin
                    visible: moss.page === "library"
                    z: 1
                }
                GamePage {
                    anchors.fill: parent
                    anchors.margins: Theme.contentMargin
                    visible: moss.page === "game"
                    z: 1
                    onEditConfig: gameConfig.openFor(moss.current.gameId)
                }
                SettingsPage {
                    anchors.fill: parent
                    anchors.margins: Theme.contentMargin
                    visible: moss.page === "settings"
                    z: 1
                }
                LogsPage {
                    anchors.fill: parent
                    anchors.margins: Theme.contentMargin
                    visible: moss.page === "logs"
                    logText: logBuffer
                    z: 1
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
    OnboardingDialog { id: onboarding }
    GameConfigDialog { id: gameConfig }

    ConfirmDialog {
        id: antiCheatDialog
        titleText: "Anti-cheat not supported"
        message: antiCheatMessage + "\n\nMoss will not keep retrying. Check Logs if you need the raw output."
        confirmLabel: "View Logs"
        cancelLabel: "Dismiss"
        onAccepted: {
            moss.loadLog(moss.current.gameId || "")
        }
    }

    Dialog {
        id: failDialog
        property string gameId: ""
        property string recipeId: ""
        modal: true
        anchors.centerIn: Overlay.overlay
        width: 440
        title: "Launch failed"
        standardButtons: Dialog.NoButton
        background: Rectangle {
            color: Theme.dialogPanelFill
            border.width: 1
            border.color: Theme.border
            radius: Theme.radiusLarge
        }
        contentItem: Column {
            width: parent.width
            spacing: Theme.space12
            Text {
                id: failTitle
                width: parent.width
                wrapMode: Text.WordWrap
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSection
                font.weight: Font.DemiBold
            }
            Text {
                id: failDetail
                width: parent.width
                wrapMode: Text.WordWrap
                color: Theme.textSecondary
                font.pixelSize: Theme.fontSecondary
            }
            Row {
                spacing: Theme.space8
                anchors.right: parent.right
                MossSecondaryButton {
                    text: "View Log"
                    onClicked: {
                        failDialog.close()
                        moss.loadLog(failDialog.gameId)
                    }
                }
                MossButton {
                    id: failApply
                    text: "Apply Fix"
                    visible: false
                    onClicked: {
                        moss.applyRecommendedFix(failDialog.gameId, failDialog.recipeId)
                        failDialog.close()
                    }
                }
                MossSecondaryButton {
                    text: "Dismiss"
                    onClicked: failDialog.close()
                }
            }
        }
    }

    Rectangle {
        id: toast
        visible: false
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: Theme.space24
        radius: Theme.radiusMedium
        color: Theme.dialogPanelFill
        border.width: 1
        border.color: Theme.border
        width: toastLabel.implicitWidth + 24
        height: 36
        z: 10
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
