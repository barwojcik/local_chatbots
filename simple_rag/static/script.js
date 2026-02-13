// Constants and state management
const STATE = {
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
    $('.loading-animation').last().fadeIn(100);
    $('#send-button').prop('disabled', true);
};

const hideBotLoadingAnimation = () => {
    STATE.isProcessing = false;
    $('.loading-animation').last().hide();
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

const resetVectorStore = async () => {
    try {
        const response = await fetch('/reset-vector-store', {
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
        console.log('Vector store reset successfully:', data);
        return data;
    } catch (error) {
        console.error('Error resetting vector store:', error);
        showErrorMessage('Failed to reset uploaded file context. Please try again.');
        return null;
    }
};

// Message handling functions
const showErrorMessage = (message) => {
    hideBotLoadingAnimation();

    $('#message-list').append(`
        <div class="message-line error">
            <div class="message-box error">
                ${message}
            </div>
        </div>
    `);
    scrollToBottom();
};

const populateUserMessage = (userMessage) => {
    $('#message-input').val('');
    $('#message-list').append(`
        <div class="message-line">
            <div class="message-box my-text">
                <div class="me">${userMessage}</div>
            </div>
        </div>
    `);
    scrollToBottom();
};

const renderBotResponse = (response, uploadButtonHtml) => {
    if (!response) return;

    STATE.responses.push(response);
    hideBotLoadingAnimation();

    // Convert markdown to HTML
    const parsedMarkdown = marked.parse(response.botResponse.trim());

    $('#message-list').append(`
        <div class="message-line">
            <div class="markdown-content">
                ${parsedMarkdown}${uploadButtonHtml ? '<br>' + uploadButtonHtml : ''}
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
    let uploadButtonHtml = '';
    if (STATE.isFirstMessage) {
        response = {
          botResponse: "Hello there! I'm your friendly data assistant, ready to answer any questions regarding your data. Could you please upload a PDF file for me to analyze?"
        };
        uploadButtonHtml = `
        <input type="file" id="file-upload" accept=".pdf" hidden>
        <button id="upload-button" class="btn btn-primary btn-sm">Upload File</button>
        `;
    } else {
        response = await processUserMessage(userMessage);
    }

    renderBotResponse(response, uploadButtonHtml);

    // Event listener for file upload
    if (STATE.isFirstMessage) {
    $("#upload-button").on("click", () => {
        $("#file-upload").click();
    });

    $("#file-upload").on("change", async function () {
        try {
            const file = this.files[0];
            if (!file || !file.type.includes('pdf')) {
                throw new Error("Please select a valid PDF file");
            }

            await showBotLoadingAnimation();

            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${STATE.baseUrl}/process-document`, {
                method: "POST",
                headers: { Accept: "application/json" },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed with status: ${response.status}`);
            }

            $('#upload-button').prop('disabled', true);
            const responseData = await response.json();
            console.log('/process-document', responseData);
            renderBotResponse(responseData, '');

        } catch (error) {
            console.error('File upload error:', error);
            showErrorMessage(error.message);
        }
    });

    STATE.isFirstMessage = false;
}
};

// Configure marked.js
const configureMarked = () => {
    // Set options for better security and features
    marked.setOptions({
        renderer: new marked.Renderer(),
        gfm: true, // GitHub flavored markdown
        breaks: true, // Convert line breaks to <br>
        sanitize: false, // Don't sanitize HTML (we'll use DOMPurify if needed)
        smartLists: true,
        smartypants: true, // Use smart typographic punctuation
        highlight: function(code, lang) {
            return code; // Simple code highlighting
        }
    });
};

// Document ready handler
$(document).ready(() => {
    // Configure marked.js
    configureMarked();

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
        await resetVectorStore();
        document.querySelector('#upload-button').disabled = false;
        await populateBotResponse();
    });

    // Start the chat
    populateBotResponse();
});
