let teamsTab = null;

// Teams 탭 찾기 또는 열기
async function getTeamsTab() {
  const tabs = await chrome.tabs.query({url: "*://teams.microsoft.com/*"});
  if (tabs.length > 0) {
    return tabs[0];
  }
  return await chrome.tabs.create({url: "https://teams.microsoft.com"});
}

// 채팅방 목록 가져오기
async function getChatList() {
  teamsTab = await getTeamsTab();
  
  const response = await chrome.tabs.sendMessage(teamsTab.id, {
    action: "GET_CHAT_LIST"
  });
  
  if (response.error) {
    document.getElementById('loadingStatus').textContent = response.error;
    return;
  }
  
  displayChatList(response.chats);
}

// 채팅방 목록 표시
function displayChatList(chats) {
  const chatListElement = document.getElementById('chatList');
  const loadingStatus = document.getElementById('loadingStatus');
  
  loadingStatus.style.display = 'none';
  chatListElement.innerHTML = '';
  
  chats.forEach(chat => {
    const chatItem = document.createElement('div');
    chatItem.className = 'chat-item';
    chatItem.textContent = chat.name;
    chatItem.dataset.chatId = chat.id;
    
    chatItem.addEventListener('click', () => {
      chrome.storage.sync.set({ selectedChat: chat }, () => {
        showStatus('채팅방이 선택되었습니다.', 'success');
      });
    });
    
    chatListElement.appendChild(chatItem);
  });
}

function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;
  status.style.display = 'block';
  
  setTimeout(() => {
    status.style.display = 'none';
  }, 3000);
}

// 초기화
document.addEventListener('DOMContentLoaded', getChatList);