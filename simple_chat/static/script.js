// Constants and state management
const STATE = {
    lightMode: true,
    isFirstMessage: true,
    responses: [],
    baseUrl: window.location.origin,
    isProcessing: false
};

// Utility functions
const sleep = (time) => new Promise((resolve) => setTimeout(resolve, time));

const cleanTextInput = (value) => {
    return value
        .trim()
        .replace(/[\n\t]/g, "")
        .replace(/<[^>]*>/g, "")
        .replace(/[<>&;]/g, "");
};

// UI manipulation functions
const showBotLoadingAnimation = async () => {
    if (STATE.isProcessing) return;
    STATE.isProcessing = true;
    await sleep(200);
    $('.loading-animation').last().fadeIn();
    $('#send-button').prop('disabled', true);
};

const hideBotLoadingAnimation = () => {
    STATE.isProcessing = false;
    $('.loading-animation').last().fadeOut();
    if (!STATE.isFirstMessage) {
        $('#send-button').prop('disabled', false);
    }
};

const scrollToBottom = () => {
    const chatWindow = $('#chat-window');
    chatWindow.animate({
        scrollTop: chatWindow[0].scrollHeight
    }, 300);
};

// API interaction functions
const processUserMessage = async (userMessage) => {
    try {
        const response = await fetch(`${STATE.baseUrl}/process-message`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ userMessage })
        });

        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('User message processed:', data);
        return data;
    } catch (error) {
        console.error('Error processing user message:', error);
        showErrorMessage('Failed to process message. Please try again.');
        return null;
    }
};

const resetBotChatHistory = async () => {
    try {
        const response = await fetch('/reset-chat-history', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Chat history reset successfully:', data);
        return data;
    } catch (error) {
        console.error('Error resetting chat history:', error);
        showErrorMessage('Failed to reset chat history. Please try again.');
        return null;
    }
};

// Message handling functions
const showErrorMessage = (message) => {
    $('#message-list').append(`
        <div class="message-line error">
            <div class="message-box error${!STATE.lightMode ? ' dark' : ''}">
                ${message}
            </div>
        </div>
    `);
    scrollToBottom();
};

const populateUserMessage = (userMessage) => {
    $('#message-input').val('');
    $('#message-list').append(`
        <div class="message-line my-text">
            <div class="message-box my-text${!STATE.lightMode ? ' dark' : ''}">
                <div class="me">${userMessage}</div>
            </div>
        </div>
    `);
    scrollToBottom();
};

const renderBotResponse = (response) => {
    if (!response) return;
    
    STATE.responses.push(response);
    hideBotLoadingAnimation();

    $('#message-list').append(`
        <div class="message-line">
            <div class="message-box${!STATE.lightMode ? ' dark' : ''}">
                ${response.botResponse.trim()}
            </div>
        </div>
    `);
    scrollToBottom();
};

const handleUserMessage = async () => {
    const messageInput = $('#message-input');
    const message = cleanTextInput(messageInput.val());

    if (!message || STATE.isProcessing) return;

    populateUserMessage(message);
    await populateBotResponse(message);
};

const populateBotResponse = async (userMessage) => {
    await showBotLoadingAnimation();

    let response;
    if (STATE.isFirstMessage) {
        response = {
            botResponse: "Hello there! I'm your friendly AI assistant, ready to chat!"
        };
        STATE.isFirstMessage = false;
    } else {
        response = await processUserMessage(userMessage);
    }

    renderBotResponse(response);
};

// Document ready handler
$(document).ready(() => {
    // Initial setup
    $('#send-button').prop('disabled', true);

    // Event handlers
    $('#message-input').on('keyup', async (event) => {
        const inputVal = cleanTextInput($(event.target).val());
        if (event.keyCode === 13 && inputVal) {
            await handleUserMessage();
        }
    });

    $('#send-button').on('click', handleUserMessage);

    $('#reset-button').on('click', async () => {
        $('#message-list').empty();
        STATE.responses = [];
        STATE.isFirstMessage = true;
        await resetBotChatHistory();
        await populateBotResponse();
    });

    $('#light-dark-mode-switch').on('change', () => {
        $('body').toggleClass('dark-mode');
        $('.message-box').toggleClass('dark');
        $('.loading-dots').toggleClass('dark');
        $('.dot').toggleClass('dark-dot');
        STATE.lightMode = !STATE.lightMode;
    });

    // Start the chat
    populateBotResponse();
});