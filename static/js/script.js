// 페이지 이동 함수
function navigateTo(page) {
    window.location.href = page;
}

let chatBox = document.getElementById("chatBox");
let userInput = document.getElementById("userInput");

function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;

    // 사용자 메시지 추가
    addMessage("사용자", message);

    // 서버로 메시지 전송
    fetch("/chatbot", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
    })
        .then(response => response.json())
        .then(data => {
            addMessage("챗봇", data.response);

            if (data.done) {
                userInput.disabled = true;
                userInput.placeholder = "추천 결과를 확인하세요!";
            }
        })
        .catch(error => console.error("Error:", error));

    // 입력 필드 초기화
    userInput.value = "";
}

function addMessage(sender, text) {
    chatBox.innerHTML += `<p><strong>${sender}:</strong> ${text}</p>`;
    chatBox.scrollTop = chatBox.scrollHeight; // 스크롤 아래로 이동
}