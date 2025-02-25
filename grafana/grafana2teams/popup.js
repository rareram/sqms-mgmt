// popup.js
let teamsTab = null;

// 팀즈 탭 찾기 또는 열기
async function getTeamsTab() {
  try {
    // 팀즈의 URL 패턴을 teams.microsoft.com/*와 teams.live.com/*로 수정
    const tabs = await chrome.tabs.query({
      url: ["*://teams.microsoft.com/*", "*://teams.live.com/*"]
    });
    console.log('Found Teams tabs:', tabs); // 디버깅용 로그
    if (tabs.length > 0) {
      return tabs[0];
    } else {
      // 팀즈가 열려 있지 않은 경우 메시지 표시
      document.getElementById('loadingStatus').innerHTML = 
        '팀즈가 열려 있지 않습니다.<br><button id="openTeams">팀즈 열기</button>';
      
      document.getElementById('openTeams').addEventListener('click', async () => {
        const newTab = await chrome.tabs.create({url: "https://teams.microsoft.com"});
        window.close(); // 팝업 닫기
      });
      return null;
    }
  } catch (error) {
    console.error('팀즈 탭 찾기 실패:', error);
    showError('팀즈 탭을 찾을 수 없습니다.');
    return null;
  }
}

// 채팅방 목록 가져오기
async function getChatList() {
  try {
    teamsTab = await getTeamsTab();
    if (!teamsTab) {
      return; // Teams 탭이 없는 경우 종료
    }

    try {
      const response = await chrome.tabs.sendMessage(teamsTab.id, {
        action: "GET_CHAT_LIST"
      });

      if (response.error) {
        showError(response.error);
        return;
      }

      displayChatList(response.chats);
    } catch (error) {
      console.error('Teams와 통신 실패:', error);
      showError('Teams가 아직 로딩 중입니다. 잠시 후 다시 시도해주세요.');
    }
  } catch (error) {
    console.error('채팅방 목록 가져오기 실패:', error);
    showError('채팅방 목록을 가져오는데 실패했습니다.');
  }
}

// 채팅방 목록 표시
function displayChatList(chats) {
  const chatListElement = document.getElementById('chatList');
  const loadingStatus = document.getElementById('loadingStatus');
  
  loadingStatus.style.display = 'none';
  chatListElement.innerHTML = '';
  
  if (!chats || chats.length === 0) {
    chatListElement.innerHTML = '<div class="error">채팅방을 찾을 수 없습니다.</div>';
    return;
  }
  
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

// 상태 메시지 표시
function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;
  status.style.display = 'block';
  
  setTimeout(() => {
    status.style.display = 'none';
  }, 3000);
}

// 에러 메시지 표시
function showError(message) {
  const loadingStatus = document.getElementById('loadingStatus');
  loadingStatus.innerHTML = `<div class="error">${message}</div>`;
}

// 자동 새로고침 기능
function setupAutoRefresh() {
  let refreshAttempts = 0;
  const maxAttempts = 3;
  const refreshInterval = 2000; // 2초

  const attemptRefresh = async () => {
    if (refreshAttempts >= maxAttempts) {
      showError('Teams 연결에 실패했습니다. Teams가 로그인되어 있는지 확인해주세요.');
      return;
    }

    refreshAttempts++;
    await getChatList();

    // 채팅방 목록이 없으면 재시도
    const chatList = document.getElementById('chatList');
    if (!chatList.children.length) {
      setTimeout(attemptRefresh, refreshInterval);
    }
  };

  attemptRefresh();
}

// 초기화
document.addEventListener('DOMContentLoaded', setupAutoRefresh);
