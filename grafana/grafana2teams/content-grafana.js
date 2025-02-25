console.log('Grafana content script loaded!');

// Grafana의 기본 컨텍스트 메뉴 차단 방지
document.addEventListener('contextmenu', (e) => {
    e.stopImmediatePropagation();
}, true);

// 페이지가 로드되었을 때 실행
window.addEventListener('load', () => {
    console.log('Grafana page fully loaded');
});

// 오른쪽 클릭 이벤트 리스너 (디버깅용)
document.addEventListener('contextmenu', (e) => {
    console.log('Right click detected');
    console.log('Clicked element:', e.target);
    console.log('Element classes:', e.target.className);
    let parent = e.target.parentElement;
    let i = 0;
    while (parent && i < 5) {
        console.log(`Parent ${i} classes:`, parent.className);
        parent = parent.parentElement;
        i++;
    }
});

document.addEventListener('contextmenu', function(event) {
    console.log("Right-click detected");
})

document.addEventListener('contextmenu', function(event) {
    event.stopImmediatePropagation();
    console.log("Right-click event stopped");
}, true);

// 메시지 리스너
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Message received in content script:', request);
    
    if (request.action === "CAPTURE_AND_SEND") {
        console.log('Capture and send requested');
        const panel = findGrafanaPanel(document.elementFromPoint(contextMenuX, contextMenuY));
        if (panel) {
            captureAndSendPanel(panel);
        } else {
            alert('캡처할 그래프를 찾을 수 없습니다. 그래프 위에서 우클릭해주세요.');
        }
    }
});

// 마우스 좌표 저장용 변수
let contextMenuX = 0;
let contextMenuY = 0;

// 마우스 좌표 저장
document.addEventListener('mousemove', (e) => {
    contextMenuX = e.clientX;
    contextMenuY = e.clientY;
});

// Grafana 패널 찾기 함수
function findGrafanaPanel(element) {
    console.log('Searching for Grafana panel from element:', element);
    
    if (!element) return null;
    
    const selectors = [
        '.panel-container',
        '.react-grid-item',
        '.dashboard-panel',
        '[data-panelid]',
        '.grafana-panel',
        '.panel',
        '.panel-wrapper'
    ];
    
    let current = element;
    while (current && current !== document.body) {
        console.log('Checking element:', current);
        console.log('Element classes:', current.className);
        
        if (selectors.some(selector => 
            selector.startsWith('.') ? 
            current.classList.contains(selector.slice(1)) : 
            current.matches(selector)
        )) {
            console.log('Found panel:', current);
            return current;
        }
        current = current.parentElement;
    }
    
    console.log('No panel found');
    return null;
}

// 패널 캡처 및 전송 함수
async function captureAndSendPanel(panel) {
    console.log('Attempting to capture panel:', panel);
    
    try {
        if (!window.html2canvas) {
            console.error('html2canvas not loaded');
            await loadHtml2Canvas();
        }
        
        const canvas = await window.html2canvas(panel, {
            scale: 2,
            logging: true
        });
        
        console.log('Panel captured successfully');
        
        canvas.toBlob(async (blob) => {
            try {
                const clipboardItem = new ClipboardItem({ 'image/png': blob });
                await navigator.clipboard.write([clipboardItem]);
                console.log('Image copied to clipboard');
                
                chrome.runtime.sendMessage({
                    action: "SEND_TO_TEAMS"
                });
            } catch (error) {
                console.error('Failed to copy to clipboard:', error);
                alert('클립보드 복사에 실패했습니다.');
            }
        });
    } catch (error) {
        console.error('Capture failed:', error);
        alert('이미지 캡처에 실패했습니다.');
    }
}