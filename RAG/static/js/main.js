document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // 인프라 선택 관련 변수
    let selectedInfra = [];
    let isInfraSelectionMode = false;
    
    // 메시지 추가 함수
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        // 추천 매물 메시지인 경우 특별 처리
        if (!isUser && message.includes('추천 매물입니다')) {
            messageDiv.className = 'message bot-message recommendation';
            
            // 헤더와 바디 분리
            const headerText = '추천 매물 결과';
            const bodyText = message;
            
            messageDiv.innerHTML = `
                <div class="recommendation-header">
                    <i class="fas fa-home"></i> ${headerText}
                </div>
                <div class="recommendation-body">
                    ${formatPropertyRecommendations(bodyText)}
                </div>
            `;
        } else {
            // 일반 메시지 처리
            let formattedMessage = message.replace(/\n/g, '<br>');
            
            // 인프라 선택 목록 특별 처리
            if (!isUser && formattedMessage.includes('다음 중에서 가장 중요하게 생각하는 인프라를')) {
                isInfraSelectionMode = true;
                selectedInfra = [];
                formattedMessage = formatInfraSelectionList(formattedMessage);
            } 
            // 다른 선택지들은 기존 방식대로 처리
            else if (!isUser && (formattedMessage.includes('1.') || formattedMessage.includes('번호를 입력'))) {
                // 특별한 경우 버튼 스타일로 변경
                if (formattedMessage.includes('어떤 기준으로 매물을 추천해드릴까요')) {
                    formattedMessage = addServiceChoiceButtons(formattedMessage);
                } else if (formattedMessage.includes('이동 방법을 선택해주세요')) {
                    formattedMessage = addMovementChoiceButtons(formattedMessage);
                } else {
                    // 그 외 일반적인 선택지는 기존 방식 유지
                    formattedMessage = addChoiceButtons(formattedMessage);
                }
            }
            
            messageDiv.innerHTML = formattedMessage;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 인프라 선택 목록 포맷팅 함수 (버튼 스타일로 통일, 다중 선택 지원)
    function formatInfraSelectionList(message) {
        // 메시지 본문과 인프라 목록 분리
        const introEndIndex = message.indexOf('1.');
        const introText = message.substring(0, introEndIndex);
        const listText = message.substring(introEndIndex);
        
        // 인프라 목록 항목 추출
        const regex = /(\d+)\.\s*(.*?)(?=\d+\.|번호를 입력|$)/gs;
        const matches = [...listText.matchAll(regex)];
        
        let html = introText + '<div class="infra-buttons">';
        
        if (matches && matches.length > 0) {
            matches.forEach(match => {
                const number = match[1];
                const text = match[2].trim();
                html += `
                    <button class="infra-btn" data-infra-id="${number}" onclick="toggleInfraSelection('${number}', '${text.replace(/'/g, "\\'")}')">
                        ${number}. ${text}
                    </button>
                `;
            });
        }
        
        html += '</div>';
        
        // 선택된 인프라 표시 영역
        html += `
            <div id="selected-infra-container" style="margin-top: 15px; display: none;">
                <p>선택한 인프라: <span id="selected-infra-list"></span></p>
            </div>
        `;
        
        // 완료 버튼 및 안내문
        html += `
            <div style="margin-top: 15px;">
                <button id="complete-infra-selection" class="btn btn-primary" style="display: none;" onclick="completeInfraSelection()">
                    선택 완료 (1-3개)
                </button>
            </div>
        `;
        
        // 안내문 추가
        const instructionText = listText.match(/번호를 입력해주세요.*$/s);
        if (instructionText) {
            html += `<p class="infra-instruction">${instructionText[0]}</p>`;
        }
        
        return html;
    }
    
    // 인프라 선택 토글 함수
    window.toggleInfraSelection = function(id, name) {
        console.log(`토글: ${id}, ${name}`);
        
        const btn = document.querySelector(`.infra-btn[data-infra-id="${id}"]`);
        const index = selectedInfra.findIndex(item => item.id === id);
        
        // 이미 선택된 경우 제거
        if (index > -1) {
            selectedInfra.splice(index, 1);
            btn.classList.remove('selected');
        } 
        // 새로 선택하는 경우 (최대 3개까지)
        else if (selectedInfra.length < 3) {
            selectedInfra.push({ id, name });
            btn.classList.add('selected');
        } else {
            // 3개 초과 선택 시 알림
            alert('최대 3개까지만 선택 가능합니다.');
            return;
        }
        
        // 선택된 인프라 표시 업데이트
        updateSelectedInfraDisplay();
    };
    
    // 선택된 인프라 표시 업데이트
    function updateSelectedInfraDisplay() {
        const container = document.getElementById('selected-infra-container');
        const list = document.getElementById('selected-infra-list');
        const completeBtn = document.getElementById('complete-infra-selection');
        
        if (selectedInfra.length > 0) {
            container.style.display = 'block';
            completeBtn.style.display = 'inline-block';
            
            // 선택된 인프라 목록 표시
            list.innerHTML = selectedInfra.map(item => `${item.id}. ${item.name}`).join(', ');
            
            // 완료 버튼 텍스트 업데이트
            completeBtn.innerHTML = `선택 완료 (${selectedInfra.length}/3)`;
        } else {
            container.style.display = 'none';
            completeBtn.style.display = 'none';
        }
    }
    
    // 인프라 선택 완료
    window.completeInfraSelection = function() {
        if (selectedInfra.length > 0 && selectedInfra.length <= 3) {
            // 선택된 인프라 ID를 쉼표로 구분하여 전송
            const selectedIds = selectedInfra.map(item => item.id).join(',');
            
            // 사용자 메시지 표시
            const displayText = selectedInfra.map(item => `${item.id}. ${item.name}`).join(', ');
            addMessage(displayText, true);
            
            // 실제 서버로는 ID만 전송
            sendMessageToServer(selectedIds);
            
            // 선택 모드 종료
            isInfraSelectionMode = false;
            selectedInfra = [];
        } else {
            alert('1개 이상, 3개 이하로 선택해주세요.');
        }
    };
    
    // 기준 선택 버튼 추가 함수
    function addServiceChoiceButtons(message) {
        // 원본 메시지 유지
        return message + '<div class="choices">' + 
            '<button class="choice-btn" onclick="sendChoice(\'소요시간 기준\')">1️⃣ 소요시간 기준</button>' +
            '<button class="choice-btn" onclick="sendChoice(\'반경 기준\')">2️⃣ 반경 기준</button>' +
            '<button class="choice-btn" onclick="sendChoice(\'상관없음\')">3️⃣ 상관없음</button>' +
            '</div>';
    }
    
    // 이동 방법 선택 버튼 추가 함수
    function addMovementChoiceButtons(message) {
        // 원본 메시지 유지
        return message + '<div class="choices">' + 
            '<button class="choice-btn" onclick="sendChoice(\'도보\')">1️⃣ 도보</button>' +
            '<button class="choice-btn" onclick="sendChoice(\'대중교통\')">2️⃣ 대중교통</button>' +
            '<button class="choice-btn" onclick="sendChoice(\'상관없음\')">3️⃣ 상관없음</button>' +
            '</div>';
    }
    
    // 층수 정보 형식화 함수
    function formatFloorInfo(floor) {
        if (!floor) return '정보 없음';
        
        // 층수 배지 스타일 결정
        let badgeClass = "bg-primary";
        
        // 층수에 따른 배지 색상 변경
        if (floor.includes('반지층') || floor.includes('지하')) {
            badgeClass = "bg-danger";  // 빨간색
        } else if (floor.includes('옥탑')) {
            badgeClass = "bg-warning text-dark";  // 노란색
        } else if (floor.includes('1층')) {
            badgeClass = "bg-success";  // 초록색
        } else if (floor.includes('2층') || floor.includes('3층')) {
            badgeClass = "bg-info";  // 파란색
        }
        
        return `<span class="badge ${badgeClass}">${floor}</span>`;
    }
    
    // 추천 매물 형식화 함수
    function formatPropertyRecommendations(message) {
        // 매물이 없는 경우 처리
        if (message.includes('설정하신 조건에 맞는 매물을 찾지 못했습니다')) {
            return `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>설정하신 조건에 맞는 매물을 찾지 못했습니다.</p>
                    <p>조건을 변경하여 다시 검색해보세요.</p>
                    <div class="choices mt-3">
                        <button class="choice-btn" onclick="sendChoice('예산을 올려줘')">예산 상향 조정</button>
                        <button class="choice-btn" onclick="sendChoice('반경을 넓혀줘')">검색 반경 확장</button>
                        <button class="choice-btn" onclick="sendChoice('기본 조건으로 검색해줘')">기본 조건으로 검색</button>
                    </div>
                </div>
            `;
        }
        
        // 매물 정보를 파싱하고 카드 형태로 변환
        const regex = /(\d+)\.\s*(.*?)(?=\d+\.|추천 매물에 대해|$)/gs;
        const matches = [...message.matchAll(regex)];
        
        if (matches.length === 0) {
            return message.replace(/\n/g, '<br>');
        }
        
        let html = '<div class="property-cards">';
        let validPropertyCount = 0;
        
        matches.forEach(match => {
            const propertyNumber = match[1];
            const propertyInfo = match[2].trim();
            
            // 주소와 역 정보 추출
            const addressMatch = propertyInfo.match(/(.*?)\s*\((.*?)\)/);
            if (!addressMatch) return; // 주소 정보가 없으면 건너뜀
            
            const address = addressMatch[1];
            const station = addressMatch[2];
            
            // 방 타입 추출 (원룸, 투룸 등)
            const typeMatch = propertyInfo.match(/유형:\s*(.*?)(?=,|$)/i) || propertyInfo.match(/type:\s*(.*?)(?=,|$)/i);
            const roomType = typeMatch ? typeMatch[1].trim() : "";
            
            // 가격 정보 추출
            const rentMatch = propertyInfo.match(/월세:\s*(\d+(?:\.\d+)?)/);
            const depositMatch = propertyInfo.match(/보증금:\s*(\d+(?:\.\d+)?)/);
            const maintMatch = propertyInfo.match(/관리비:\s*(\d+(?:\.\d+)?)/);
            
            if (!rentMatch || !depositMatch) return; // 필수 가격 정보가 없으면 건너뜀
            
            validPropertyCount++;
            
            // 소수점 제거 및 정수로 변환
            const rent = rentMatch ? parseInt(parseFloat(rentMatch[1])) : '?';
            const deposit = depositMatch ? parseInt(parseFloat(depositMatch[1])) : '?';
            const maint = maintMatch ? parseInt(parseFloat(maintMatch[1])) : '?';
            
            // 추가 정보 추출
            const floorMatch = propertyInfo.match(/층수:\s*(.*?)(?=,|$)/);
            const sizeMatch = propertyInfo.match(/면적:\s*(.*?)(?=,|$)/) || propertyInfo.match(/size:\s*(.*?)(?=,|$)/i);
            const directionMatch = propertyInfo.match(/방향:\s*(.*?)(?=,|$)/);
            const heatingMatch = propertyInfo.match(/난방:\s*(.*?)(?=,|$)/);
            const parkingMatch = propertyInfo.match(/주차:\s*(.*?)(?=,|$)/);
            const elevatorMatch = propertyInfo.match(/엘리베이터:\s*(.*?)(?=,|$)/);
            const facilitiesMatch = propertyInfo.match(/생활시설:\s*(.*?)(?=,|$)/);
            const securityMatch = propertyInfo.match(/안전시설:\s*(.*?)(?=,|$)/);
            
            const floor = floorMatch ? floorMatch[1] : '정보 없음';
            const size = sizeMatch ? sizeMatch[1] : '정보 없음';
            const direction = directionMatch ? directionMatch[1] : '정보 없음';
            const heating = heatingMatch ? heatingMatch[1] : '정보 없음';
            const parking = parkingMatch ? parkingMatch[1] : '정보 없음';
            const elevator = elevatorMatch ? elevatorMatch[1] : '정보 없음';
            const facilities = facilitiesMatch ? facilitiesMatch[1] : '정보 없음';
            const security = securityMatch ? securityMatch[1] : '정보 없음';
            
            // 인프라 점수 추출
            const scoreMatch = propertyInfo.match(/인프라 점수:\s*([\d\.]+)/);
            const score = scoreMatch ? parseFloat(scoreMatch[1]).toFixed(1) : '?';
            
            // 이동 시간 정보 추출 및 소수점 제거
            const timeMatch = propertyInfo.match(/(도보|대중교통)\s*(\d+(?:\.\d+)?)/);
            let timeInfo = '';
            if (timeMatch) {
                const moveType = timeMatch[1];
                const minutes = parseInt(parseFloat(timeMatch[2]));
                timeInfo = `${moveType} ${minutes}분`;
            }
            
            // 인프라 정보 추출
            const infraSection = propertyInfo.match(/인프라 세부 정보:([\s\S]*?)(?=\n\n|$)/);
            const infraItems = infraSection ? 
                infraSection[1].match(/- (.*?)(?:\(거리: (\d+)m\))?/g) : [];
            
            let infraHTML = '';
            if (infraItems && infraItems.length > 0) {
                infraHTML = '<div class="property-infra"><div class="infra-title">주변 인프라</div><div class="infra-items">';
                infraItems.forEach(item => {
                    const itemMatch = item.match(/- (.*?)(?:\(거리: (\d+)m\))?/);
                    if (itemMatch) {
                        const infraName = itemMatch[1].trim();
                        const distance = itemMatch[2] ? parseInt(itemMatch[2]) : '';
                        infraHTML += `<div class="infra-item">
                            <i class="fas fa-map-marker-alt"></i> ${infraName} ${distance ? `(${distance}m)` : ''}
                        </div>`;
                    }
                });
                infraHTML += '</div></div>';
            }
            
            // 랜덤 이미지 생성 (실제로는 데이터베이스에서 가져와야 함)
            const imgNumber = Math.floor(Math.random() * 5) + 1;
            
            html += `
            <div class="property-card">
                <div class="property-image">
                    <img src="https://source.unsplash.com/random/300x200/?apartment&${imgNumber}" alt="매물 이미지">
                </div>
                <div class="property-header">
                    <div>매물 ${propertyNumber}</div>
                    <div class="score">
                        <i class="fas fa-star"></i> ${score}
                    </div>
                </div>
                <div class="property-body">
                    <div class="property-address">${address}</div>
                    <div class="property-station">
                        <i class="fas fa-subway"></i> ${station} ${roomType ? `<span class="badge bg-primary ms-2">${roomType}</span>` : ''}
                    </div>
                    <div class="property-price">
                        월세 ${rent}만원 / 보증금 ${deposit}만원
                    </div>
                    <div class="property-info">
                        <span><i class="fas fa-coins"></i> 관리비 ${maint}만원</span>
                        ${timeInfo ? `<span><i class="fas fa-walking"></i> ${timeInfo}</span>` : ''}
                    </div>
                    <div class="property-details mt-2">
                        <div class="row g-2">
                            <div class="col-6"><small><i class="fas fa-building"></i> ${formatFloorInfo(floor)}</small></div>
                            <div class="col-6"><small><i class="fas fa-vector-square"></i> ${size}</small></div>
                            <div class="col-6"><small><i class="fas fa-compass"></i> ${direction}</small></div>
                            <div class="col-6"><small><i class="fas fa-fire"></i> ${heating}</small></div>
                            <div class="col-6"><small><i class="fas fa-car"></i> ${parking}</small></div>
                            <div class="col-6"><small><i class="fas fa-elevator"></i> ${elevator}</small></div>
                        </div>
                    </div>
                    ${facilities !== '정보 없음' || security !== '정보 없음' ? `
                    <div class="property-details mt-2">
                        ${facilities !== '정보 없음' ? `<div><small><i class="fas fa-couch"></i> ${facilities}</small></div>` : ''}
                        ${security !== '정보 없음' ? `<div><small><i class="fas fa-shield-alt"></i> ${security}</small></div>` : ''}
                    </div>` : ''}
                    ${infraHTML}
                    <div class="property-actions">
                        <button class="btn btn-property" onclick="sendChoice('${propertyNumber}번 매물에 대해 자세히 알려줘')">
                            <i class="fas fa-info-circle"></i> 상세정보
                        </button>
                    </div>
                </div>
            </div>
            `;
        });
        
        html += '</div>';
        
        // 유효한 매물이 없는 경우 처리
        if (validPropertyCount === 0) {
            return `
                <div class="no-results">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>표시할 수 있는 매물이 없습니다.</p>
                    <p>다른 조건으로 검색해보세요.</p>
                    <div class="choices mt-3">
                        <button class="choice-btn" onclick="sendChoice('예산을 올려줘')">예산 상향 조정</button>
                        <button class="choice-btn" onclick="sendChoice('반경을 넓혀줘')">검색 반경 확장</button>
                        <button class="choice-btn" onclick="sendChoice('기본 조건으로 검색해줘')">기본 조건으로 검색</button>
                    </div>
                </div>
            `;
        }
        
        const footer = message.match(/추천 매물에 대해[\s\S]*$/);
        if (footer) {
            html += `<div class="mt-3">${footer[0].replace(/\n/g, '<br>')}</div>`;
        }
        
        return html;
    }
    
    // 선택지 버튼 추가 함수 (일반적인 경우)
    function addChoiceButtons(message) {
        // 인프라 선택 특별 처리
        if (message.includes('다음 중에서 가장 중요하게 생각하는 인프라를')) {
            return formatInfraSelectionList(message);
        }
        
        // 기본 아이템 항목 추출 (1. 항목 형태)
        const itemRegex = /(\d+)\.\s*(.*?)(?=\d+\.|$)/g;
        const items = [...message.matchAll(itemRegex)];
        
        if (items.length === 0) {
            return message;
        }
        
        // 선택지 버튼 HTML 생성
        let choicesHTML = '<div class="choices">';
        items.forEach(item => {
            const number = item[1];
            const text = item[2].trim();
            choicesHTML += `<button class="choice-btn" onclick="sendChoice('${number}')">${number}. ${text}</button>`;
        });
        choicesHTML += '</div>';
        
        // 메시지에 선택지 버튼 추가
        return message + choicesHTML;
    }
    
    // 선택지 전송 함수
    window.sendChoice = function(choice) {
        console.log("전송하는 선택지:", choice); // 디버깅용 로그
        addMessage(choice, true);
        sendMessageToServer(choice);
    };
    
    // 메시지 전송 함수
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) {
            return; // 빈 메시지는 처리하지 않음
        }
        
        // 사용자 메시지 표시
        addMessage(message, true);
        
        // 입력 필드 초기화
        userInput.value = '';
        
        // 서버에 메시지 전송
        sendMessageToServer(message);
    }
    
    // 서버에 메시지 전송
    function sendMessageToServer(message) {
        console.log("서버로 전송:", message); // 디버깅용 로그
        
        // 입력 중 표시
        typingIndicator.style.display = 'block';
        
        // API 호출
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            // 입력 중 숨기기
            typingIndicator.style.display = 'none';
            // 봇 응답 표시
            addMessage(data.message);
        })
        .catch(error => {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            addMessage('오류가 발생했습니다. 다시 시도해주세요.');
        });
    }
    
    // 전송 버튼 클릭 이벤트
    sendButton.addEventListener('click', sendMessage);
    
    // 엔터 키 이벤트
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // CSS 스타일 추가
    const style = document.createElement('style');
    style.textContent = `
        /* 인프라 버튼 스타일 */
        .infra-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        
        .infra-btn {
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 8px 15px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: left;
        }
        
        .infra-btn:hover {
            background-color: #e0e0e0;
        }
        
        .infra-btn.selected {
            background-color: #4285f4;
            color: white;
            border-color: #4285f4;
        }
        
        #complete-infra-selection {
            background-color: #4285f4;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 20px;
            cursor: pointer;
        }
        
        #selected-infra-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 10px;
        }
        
        .infra-instruction {
            margin-top: 10px;
            font-size: 14px;
            color: #555;
        }
    `;
    document.head.appendChild(style);
});