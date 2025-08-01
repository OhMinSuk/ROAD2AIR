// app.js - 기존 채팅 기능을 별도 파일로 분리
class ChatService {
    constructor() {
        this.apiUrl = '/api/chat_parking_rag';
        this.isLoading = false;
    }

    // 메시지 전송
    async sendMessage(message) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: 'user123'
                })
            });

            if (!response.ok) {
                throw new Error('네트워크 응답이 좋지 않습니다');
            }

            const data = await response.json();
            this.displayMessage(message, 'user');
            this.displayMessage(data.response, 'bot');
            
        } catch (error) {
            console.error('Error:', error);
            this.displayMessage('죄송합니다. 오류가 발생했습니다.', 'bot');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    // 메시지 화면에 표시
    displayMessage(message, sender) {
        const chatBox = document.getElementById('chat-box');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // 로딩 표시
    showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading';
        loadingDiv.className = 'message bot-message';
        loadingDiv.innerHTML = '<div class="loading-dots">답변 생성 중...</div>';
        document.getElementById('chat-box').appendChild(loadingDiv);
    }

    // 로딩 숨기기
    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.remove();
        }
    }
}

// 전역 채팅 서비스 인스턴스
const chatService = new ChatService();

// DOM 로드 완료 후 실행
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    // 전송 버튼 클릭 이벤트
    sendButton.addEventListener('click', function() {
        const message = messageInput.value.trim();
        if (message) {
            chatService.sendMessage(message);
            messageInput.value = '';
        }
    });

    // 엔터 키 이벤트
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendButton.click();
        }
    });

    // 초기 환영 메시지
    chatService.displayMessage('안녕하세요! 주차 관련 질문을 해보세요.', 'bot');
});

// 유틸리티 함수들
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    });
                },
                error => reject(error)
            );
        } else {
            reject(new Error('Geolocation not supported'));
        }
    });
}

function formatTime(date) {
    return date.toLocaleTimeString('ko-KR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}