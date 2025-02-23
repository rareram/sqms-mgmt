// content-teams.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "GET_CHAT_LIST") {
    // Teams 채팅 목록 요소 찾기
    const chatElements = document.querySelectorAll('[data-tid="chat-list-item"]');
    
    if (!chatElements.length) {
      sendResponse({
        error: "채팅방 목록을 찾을 수 없습니다. Teams가 로드되었는지 확인해주세요."
      });
      return true;  // 비동기 응답을 위해 true 반환
    }
    
    const chats = Array.from(chatElements).map(elem => ({
      id: elem.getAttribute('data-tid'),
      name: elem.querySelector('.name')?.textContent || '알 수 없는 채팅방'
    }));
    
    sendResponse({ chats });
    return true;  // 비동기 응답을 위해 true 반환
  }
  
  if (request.action === "SEND_IMAGE") {
    try {
      // 선택된 채팅방으로 이동
      const chatElement = document.querySelector(`[data-tid="${request.chatId}"]`);
      chatElement?.click();
      
      // 클립보드에서 이미지 붙여넣기
      const messageInput = document.querySelector('[data-tid="message-input"]');
      if (messageInput) {
        messageInput.focus();
        document.execCommand('paste');
        
        // 전송 버튼 클릭
        const sendButton = document.querySelector('[data-tid="send-message-button"]');
        sendButton?.click();
        
        sendResponse({ success: true });
      } else {
        sendResponse({ error: "메시지 입력창을 찾을 수 없습니다." });
      }
    } catch (error) {
      sendResponse({ error: "이미지 전송 중 오류가 발생했습니다." });
    }
    return true;  // 비동기 응답을 위해 true 반환
  }
});
