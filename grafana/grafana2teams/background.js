console.log('Background script loaded');

// 컨텍스트 메뉴 생성
chrome.runtime.onInstalled.addListener(() => {
    console.log('Extension installed/updated');
    try {
        chrome.contextMenus.create({
            id: "sendToTeams",
            title: "Grafana 항목을 Teams로 보내기",
            contexts: ["all"],
            documentUrlPatterns: ["http://localhost:3000/*", "http://192.168.236.190:3000/*", "https://sqms.skshieldus.com:3000/*"]
        }, () => {
            if (chrome.runtime.lastError) {
                console.error('Context menu creation error:', chrome.runtime.lastError);
            } else {
                console.log('Context menu created successfully');
            }
        });
    } catch (error) {
        console.error('Failed to create context menu:', error);
    }
});

// 컨텍스트 메뉴 클릭 이벤트 처리
chrome.contextMenus.onClicked.addListener((info, tab) => {
    console.log('Context menu clicked:', info);
    if (info.menuItemId === "sendToTeams") {
        console.log('Sending CAPTURE_AND_SEND message to tab:', tab.id);
        chrome.tabs.sendMessage(tab.id, {
            action: "CAPTURE_AND_SEND"
        });
    }
});

// Teams로 이미지 전송 처리
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Message received in background:', message);
    
    if (message.action === "CAPTURE_TAB") {
        chrome.tabs.captureVisibleTab(null, {format: "png"}, (imageUrl) => {
            sendResponse({imageUrl});
        });
        return true;
    }

    if (message.action === "SEND_TO_TEAMS") {
        chrome.storage.sync.get('selectedChat', async (data) => {
            if (!data.selectedChat) {
                console.log('No chat selected');
                await chrome.tabs.sendMessage(sender.tab.id, {
                action: "SHOW_ERROR",
                error: "팀즈 채팅방을 먼저 선택해주세요."
                });
                return;
            }
            
            // 팀즈 탭을 새로운 URL 패턴으로 검색
            const teamsTabs = await chrome.tabs.query({
                url: ["*://teams.microsoft.com/*", "*://teams.live.com/*"]
            });
            if (teamsTabs.length > 0) {
                console.log('Sending to Teams tab:', teamsTabs[0].id);
                chrome.tabs.sendMessage(teamsTabs[0].id, {
                    action: "SEND_IMAGE",
                    chatId: data.selectedChat.id
                });
            } else {
                console.log('No Teams tab found');
                await chrome.tabs.sendMessage(sender.tab.id, {
                    action: "SHOW_ERROR",
                    error: "팀즈를 먼저 열어주세요."
                });
            }
        });
    }
});