document.addEventListener('mousedown', async (e) => {
  if (e.button === 2 && e.target.closest('.grafana-panel')) {
    const panel = e.target.closest('.grafana-panel');
      
    const menu = document.createElement('div');
    menu.innerHTML = `
      <div style="position: fixed; top: ${e.clientY}px; left: ${e.clientX}px; 
                  background: white; border: 1px solid #ccc; padding: 5px; z-index: 9999;">
        <button id="sendToTeams">Teams로 보내기</button>
      </div>
    `;
      
    document.body.appendChild(menu);
      
    document.getElementById('sendToTeams').addEventListener('click', async () => {
      try {
        // 패널을 이미지로 캡처
        const canvas = await html2canvas(panel);
          
        // 이미지를 클립보드에 복사
        canvas.toBlob(async (blob) => {
          const clipboardItem = new ClipboardItem({ 'image/png': blob });
          await navigator.clipboard.write([clipboardItem]);
            
          // Teams 탭에 메시지 전송
          chrome.storage.sync.get('selectedChat', async (data) => {
            if (!data.selectedChat) {
              alert('Teams 채팅방을 먼저 선택해주세요.');
              return;
            }
              
            const tabs = await chrome.tabs.query({url: "*://teams.microsoft.com/*"});
            if (tabs.length > 0) {
              chrome.tabs.sendMessage(tabs[0].id, {
                action: "SEND_IMAGE",
                chatId: data.selectedChat.id
              });
            }
          });
        });
          
        menu.remove();
      } catch (error) {
        console.error('이미지 전송 실패:', error);
        alert('이미지 전송에 실패했습니다.');
      }
    });
  }
});