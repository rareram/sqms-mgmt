// content-teams.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // 채팅방 목록 가져오기
  if (request.action === "GET_CHAT_LIST") {
    const chatElements = document.querySelectorAll('[data-tid="chat-list-item"]');
    
    if (!chatElements.length) {
      sendResponse({
        error: "채팅방 목록을 찾을 수 없습니다. Teams가 로드되었는지 확인해주세요."
      });
      return true;
    }
    
    const chats = Array.from(chatElements).map(elem => {
      // 채팅방 이름 추출 시도
      let chatName = elem.querySelector('.chat-item-title')?.textContent || // 예상 클래스
                     elem.querySelector('.ts-channel-title')?.textContent || // 다른 가능성
                     elem.querySelector('span')?.textContent || // 일반 span 태그
                     null;
      
      // 이름이 없으면 참석자 이름 추출
      if (!chatName || chatName.trim() === "") {
        const participants = elem.querySelector('.chat-participants')?.textContent || // 예상 클래스
                             elem.querySelector('.ts-channel-members')?.textContent || // 다른 가능성
                             "알 수 없는 채팅방";
        // chatName = participants.trim() ? `${participants}` `${elem.getAttribute('data-tid')}` : "알 수 없는 채팅방";
        chatName = participants.trim() ? `${participants}` : "알 수 없는 채팅방";
      }
      
      return {
        id: elem.getAttribute('data-tid'),
        name: chatName.trim()
      };
    });
    
    console.log('Extracted chats:', chats); // 디버깅용 로그
    sendResponse({ chats });
    return true; // 비동기 응답
  }
  
  // 이미지 전송 처리
  if (request.action === "SEND_IMAGE") {
    try {
      // 선택된 채팅방으로 이동
      const chatElement = document.querySelector(`[data-tid="${request.chatId}"]`);
      if (chatElement) {
        chatElement.click();
      } else {
        sendResponse({ error: "선택된 채팅방을 찾을 수 없습니다." });
        return true;
      }
      
      // 메시지 입력창 찾기
      const messageInput = document.querySelector('[data-tid="message-input"]');
      if (messageInput) {
        messageInput.focus();
        document.execCommand('paste'); // 클립보드에서 이미지 붙여넣기
        
        // 전송 버튼 클릭
        const sendButton = document.querySelector('[data-tid="send-message-button"]');
        if (sendButton) {
          sendButton.click();
          sendResponse({ success: true });
        } else {
          sendResponse({ error: "전송 버튼을 찾을 수 없습니다." });
        }
      } else {
        sendResponse({ error: "메시지 입력창을 찾을 수 없습니다." });
      }
    } catch (error) {
      console.error('이미지 전송 오류:', error);
      sendResponse({ error: "이미지 전송 중 오류가 발생했습니다." });
    }
    return true; // 비동기 응답
  }
});