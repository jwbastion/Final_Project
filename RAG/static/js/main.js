document.addEventListener('DOMContentLoaded', function () {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // 고유 사용자 ID 생성
    const userId = 'user_' + Math.random().toString(36).substr(2, 9);

    function addMessage(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user' : 'bot');
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);

        // 스크롤 최신 메시지로 이동
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        // 사용자 메시지 출력
        addMessage(message, true);
        userInput.value = '';

        // 서버에 메시지 전송
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                user_id: userId
            })
        })
            .then(response => response.json())
            .then(data => {
                addMessage(data.response, false);
                if (data.is_question) {
                    userInput.focus();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage('죄송합니다. 오류가 발생했습니다.', false);
            });
    }

    // 전송 버튼 및 엔터 이벤트 연결
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
